"""
EOW Quant Engine — Live Process Access Framework
Institutional-grade runtime observability: thread-safe, read-only, non-blocking.

Captures three live runtime artifact classes:
  1. Runtime log stream   — rolling loguru sink (last 2 000 records)
  2. RL Q-table snapshot  — deep-copy of in-memory contextual bandit state
  3. Trade execution logs — in-memory PnL records + SQLite-persisted trades

Architecture principles:
  • Read-only extraction   — zero mutation of any engine state
  • Thread-safe            — all buffer access gated by threading.Lock
  • Defensive              — every extraction wrapped in try/except; partial
                             failure never aborts the whole package
  • Non-blocking           — synchronous build_package() safe to run in
                             asyncio.to_thread(); nothing awaits inside
  • Zero-corruption        — sink writes are fire-and-forget; an exception
                             in the sink is silently discarded, never
                             propagated to the logger caller

Integration:
  At app startup call live_process_access.register_log_sink() once.
  Thereafter call live_process_access.build_package(...) from any endpoint.
"""
from __future__ import annotations

import io
import json
import threading
import time
import zipfile
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ── Constants ─────────────────────────────────────────────────────────────────

_MAX_LOG_BUFFER   = 2_000   # rolling window — oldest entries evicted automatically
_MAX_TRADE_EXPORT = 500     # cap trade list to avoid multi-MB packages


# ── Log Sink ──────────────────────────────────────────────────────────────────

class _LogSink:
    """
    Loguru-compatible write sink.
    Captures every log record into a deque with a fixed max length.
    Thread-safe via a reentrant lock so logger calls from any thread are safe.
    Never raises — exceptions are silently dropped to protect the caller.
    """

    def __init__(self, maxlen: int = _MAX_LOG_BUFFER) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._buf: deque = deque(maxlen=maxlen)

    # loguru calls write(message) where message has a .record attribute
    def write(self, message) -> None:        # noqa: ANN001
        try:
            rec = message.record
            entry: Dict[str, Any] = {
                "ts":      rec["time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "level":   rec["level"].name,
                "module":  rec["module"],
                "func":    rec["function"],
                "line":    rec["line"],
                "message": rec["message"],
            }
            with self._lock:
                self._buf.append(entry)
        except Exception:
            pass  # never raise from a loguru sink

    def snapshot(self) -> List[Dict[str, Any]]:
        """Return a shallow copy of the current buffer. Non-destructive."""
        with self._lock:
            return list(self._buf)

    def __len__(self) -> int:
        with self._lock:
            return len(self._buf)


# ── Snapshot dataclass ────────────────────────────────────────────────────────

@dataclass
class LiveProcessSnapshot:
    captured_at:  str
    log_entries:  List[Dict[str, Any]]
    thought_log:  List[Dict[str, Any]]
    rl_table:     Dict[str, Any]
    trade_log:    Dict[str, Any]
    meta:         Dict[str, Any]


# ── Framework engine ──────────────────────────────────────────────────────────

class LiveProcessAccessEngine:
    """
    Singleton runtime observability engine.

    Usage (once at app startup):
        live_process_access.register_log_sink()

    Usage (on demand, e.g. from an API endpoint):
        pkg_bytes = live_process_access.build_package(
            rl_engine_instance=rl_engine,
            pnl_calc_instance=pnl_calc,
            data_lake_instance=data_lake,
            thought_log=_thought_log,
        )
        # pkg_bytes is a ready-to-serve ZIP (application/zip)
    """

    def __init__(self) -> None:
        self._log_sink:  _LogSink     = _LogSink(maxlen=_MAX_LOG_BUFFER)
        self._sink_id:   Optional[int] = None
        self._lock:      threading.RLock = threading.RLock()
        self._registered: bool = False

    # ── Startup wire-up ───────────────────────────────────────────────────────

    def register_log_sink(self) -> None:
        """
        Install the loguru sink.  Idempotent — safe to call multiple times;
        only the first call installs the sink.
        """
        with self._lock:
            if self._registered:
                return
            try:
                from loguru import logger
                self._sink_id = logger.add(
                    self._log_sink.write,
                    level="DEBUG",
                    colorize=False,
                    backtrace=False,
                    diagnose=False,
                    enqueue=False,  # synchronous — shares the caller's thread
                    format="{time:YYYY-MM-DDTHH:mm:ss.SSS}Z | {level:<8} | {module}:{function}:{line} | {message}",
                )
                self._registered = True
                # Log the registration so it appears in its own buffer
                logger.info("[LIVE-PROCESS-ACCESS] Log sink registered — runtime observability ACTIVE")
            except Exception as exc:
                # Graceful degradation: framework still works, just without log capture
                import traceback
                traceback.print_exc()
                print(f"[LIVE-PROCESS-ACCESS] Warning: log sink registration failed: {exc}")

    # ── Individual snapshot methods ───────────────────────────────────────────

    def snapshot_logs(self) -> List[Dict[str, Any]]:
        """Return current log buffer contents. Read-only, thread-safe copy."""
        return self._log_sink.snapshot()

    def snapshot_rl_table(self, rl_engine_instance: Any) -> Dict[str, Any]:
        """
        Extract Q-table state from the RL engine.
        Performs a deep-copy of each ContextState into plain dicts —
        no references to live objects are retained in the snapshot.
        """
        if rl_engine_instance is None:
            return {
                "error":   "rl_engine not provided",
                "contexts": [],
                "meta":    {},
                "captured_at": _now_iso(),
            }
        try:
            # summary() is already read-only; use it for aggregate metadata
            meta = _safe_call(rl_engine_instance.summary, {})

            # Snapshot individual context states
            contexts: List[Dict[str, Any]] = []
            table: Dict[str, Any] = getattr(rl_engine_instance, "_table", {})
            total_pulls = getattr(rl_engine_instance, "_total_pulls", 1)

            for ctx_key, state in table.items():
                try:
                    n_vis = int(getattr(state, "n_visits", 0))
                    q_val = float(getattr(state, "q_value", 0.0))
                    n_win = int(getattr(state, "n_wins", 0))
                    t_pnl = float(getattr(state, "total_pnl", 0.0))
                    last_ts = int(getattr(state, "last_ts", 0))
                    wr    = n_win / n_vis if n_vis > 0 else 0.0

                    # UCB score (read-only property call)
                    try:
                        ucb = float(state.ucb_score(total_pulls, 1.5))
                    except Exception:
                        ucb = 0.0
                    # Cap +inf for JSON serialisability
                    if ucb != ucb or ucb > 1e9:   # nan or +inf
                        ucb = 999.0

                    contexts.append({
                        "context_key": ctx_key,
                        "n_visits":    n_vis,
                        "q_value":     round(q_val, 4),
                        "ucb_score":   round(ucb, 4),
                        "win_rate":    round(wr, 4),
                        "n_wins":      n_win,
                        "total_pnl":   round(t_pnl, 4),
                        "last_ts":     last_ts,
                    })
                except Exception:
                    continue

            contexts.sort(key=lambda x: x["n_visits"], reverse=True)

            return {
                "captured_at":    _now_iso(),
                "total_contexts": len(contexts),
                "meta":           meta,
                "contexts":       contexts,
            }
        except Exception as exc:
            return {
                "error":    str(exc),
                "contexts": [],
                "meta":     {},
                "captured_at": _now_iso(),
            }

    def snapshot_trades(
        self,
        pnl_calc_instance:  Any,
        data_lake_instance: Any,
    ) -> Dict[str, Any]:
        """
        Extract trade execution logs from both sources:
          • pnl_calc.trades  — in-memory TradeRecord list (current session)
          • data_lake        — SQLite-persisted rows (cross-session)
        Returns plain-dict structure safe for JSON serialisation.
        """
        result: Dict[str, Any] = {
            "captured_at":    _now_iso(),
            "in_memory":      [],
            "persisted":      [],
            "session_stats":  {},
            "db_stats":       {},
        }

        # ── In-memory trades ──────────────────────────────────────────────────
        if pnl_calc_instance is not None:
            try:
                raw_trades = getattr(pnl_calc_instance, "trades", [])
                exported: List[Dict[str, Any]] = []
                for t in raw_trades[-_MAX_TRADE_EXPORT:]:
                    try:
                        if hasattr(t, "__dataclass_fields__"):
                            exported.append(
                                {k: _json_safe(getattr(t, k))
                                 for k in t.__dataclass_fields__}
                            )
                        elif hasattr(t, "__dict__"):
                            exported.append(
                                {k: _json_safe(v) for k, v in t.__dict__.items()}
                            )
                        else:
                            exported.append(_json_safe(t))  # type: ignore[arg-type]
                    except Exception:
                        continue
                result["in_memory"]     = exported
                result["session_stats"] = _safe_call(
                    lambda: dict(pnl_calc_instance.session_stats), {}
                )
            except Exception as exc:
                result["in_memory_error"] = str(exc)

        # ── Persisted trades (SQLite via DataLake) ────────────────────────────
        if data_lake_instance is not None:
            try:
                # Call get_trades directly (not via _safe_call) so DataLake
                # errors propagate to the except block and are surfaced as
                # persisted_error rather than silently returning an empty list.
                rows = data_lake_instance.get_trades(limit=_MAX_TRADE_EXPORT)
                result["persisted"] = rows or []
                result["db_stats"]  = _safe_call(data_lake_instance.db_stats, {})
            except Exception as exc:
                result["persisted"]       = []
                result["persisted_error"] = str(exc)

        return result

    # ── Package builder ───────────────────────────────────────────────────────

    def build_package(
        self,
        rl_engine_instance:  Any                    = None,
        pnl_calc_instance:   Any                    = None,
        data_lake_instance:  Any                    = None,
        thought_log:         Optional[List[dict]]   = None,
    ) -> bytes:
        """
        Assemble a ZIP package containing all live runtime artifacts.

        Safety guarantees:
          • Each artifact is extracted in its own try/except block.
          • A failure in one artifact produces a *_ERROR.txt entry rather
            than aborting the whole package.
          • No live engine state is modified.
          • The returned bytes object is fully self-contained.

        Returns:
            bytes — a complete ZIP archive ready to stream as HTTP response.
        """
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        buf    = io.BytesIO()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

            # ── MANIFEST ─────────────────────────────────────────────────────
            manifest = {
                "framework":   "EOW Live Process Access Framework v1.0",
                "captured_at": ts_str + "Z",
                "contents": {
                    "runtime_logs.json":  "All loguru log records (last 2 000 lines)",
                    "runtime_logs.txt":   "Human-readable plain-text log stream",
                    "thought_log.json":   "Engine CT-Scan decision trace (last 500 thoughts)",
                    "rl_qtable.json":     "Complete RL Q-table — all context states",
                    "trade_logs.json":    "In-memory + SQLite trade execution history",
                },
                "architecture": {
                    "extraction_mode":  "read-only",
                    "thread_safety":    "threading.RLock on all buffer access",
                    "corruption_risk":  "zero — no mutation of engine state",
                    "blocking":         "non-blocking (safe for asyncio.to_thread)",
                },
            }
            zf.writestr(
                f"07_live_process/{ts_str}_MANIFEST.json",
                json.dumps(manifest, indent=2),
            )

            # ── 1. RUNTIME LOG STREAM ─────────────────────────────────────────
            try:
                log_entries = self.snapshot_logs()
                zf.writestr(
                    f"07_live_process/{ts_str}_runtime_logs.json",
                    json.dumps(
                        {"captured_at": ts_str + "Z",
                         "total_entries": len(log_entries),
                         "entries": log_entries},
                        indent=2,
                        default=str,
                    ),
                )
                # Plain-text version for human readability
                lines = "\n".join(
                    f"[{e.get('ts', '')}] "
                    f"{e.get('level', ''):8s} | "
                    f"{e.get('module', ''):30s} | "
                    f"{e.get('message', '')}"
                    for e in log_entries
                )
                zf.writestr(
                    f"07_live_process/{ts_str}_runtime_logs.txt",
                    lines or "(no log entries captured — sink may not be registered)",
                )
            except Exception as exc:
                zf.writestr(
                    f"07_live_process/{ts_str}_runtime_logs_ERROR.txt",
                    f"Log snapshot failed: {exc}\n",
                )

            # ── 2. THOUGHT LOG (CT-SCAN decision trace) ───────────────────────
            try:
                tlog = list(thought_log or [])
                zf.writestr(
                    f"07_live_process/{ts_str}_thought_log.json",
                    json.dumps(
                        {"captured_at": ts_str + "Z",
                         "total_entries": len(tlog),
                         "entries": tlog},
                        indent=2,
                        default=str,
                    ),
                )
            except Exception as exc:
                zf.writestr(
                    f"07_live_process/{ts_str}_thought_log_ERROR.txt",
                    f"Thought log snapshot failed: {exc}\n",
                )

            # ── 3. RL Q-TABLE ─────────────────────────────────────────────────
            try:
                rl_data = self.snapshot_rl_table(rl_engine_instance)
                zf.writestr(
                    f"07_live_process/{ts_str}_rl_qtable.json",
                    json.dumps(rl_data, indent=2, default=str),
                )
            except Exception as exc:
                zf.writestr(
                    f"07_live_process/{ts_str}_rl_qtable_ERROR.txt",
                    f"Q-table snapshot failed: {exc}\n",
                )

            # ── 4. TRADE EXECUTION LOGS ───────────────────────────────────────
            try:
                trade_data = self.snapshot_trades(pnl_calc_instance, data_lake_instance)
                zf.writestr(
                    f"07_live_process/{ts_str}_trade_logs.json",
                    json.dumps(trade_data, indent=2, default=str),
                )
            except Exception as exc:
                zf.writestr(
                    f"07_live_process/{ts_str}_trade_logs_ERROR.txt",
                    f"Trade log snapshot failed: {exc}\n",
                )

        buf.seek(0)
        return buf.read()

    # ── Introspection ─────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Health summary for the /api/status family of endpoints."""
        return {
            "module":          "LIVE_PROCESS_ACCESS",
            "version":         "1.0",
            "sink_registered": self._registered,
            "sink_id":         self._sink_id,
            "log_buffer_len":  len(self._log_sink),
            "log_buffer_max":  _MAX_LOG_BUFFER,
        }


# ── Private helpers ───────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _safe_call(fn: Any, default: Any) -> Any:
    """Call fn(); return default on any exception."""
    try:
        return fn()
    except Exception:
        return default


def _json_safe(v: Any) -> Any:
    """Convert values that are not JSON-serialisable to safe equivalents."""
    import math
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
    if isinstance(v, (int, float, str, bool, type(None))):
        return v
    return str(v)


# ── Module-level singleton ────────────────────────────────────────────────────
live_process_access = LiveProcessAccessEngine()

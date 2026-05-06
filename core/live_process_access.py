"""
EOW Quant Engine — Live Process Access Framework v1.1
Institutional-grade runtime observability: thread-safe, read-only, non-blocking.

Captures three live runtime artifact classes:
  1. Runtime log stream   — rolling loguru sink (last 2 000 records, 2 KB/msg cap)
  2. RL Q-table snapshot  — read-only traversal of in-memory contextual bandit state
  3. Trade execution logs — in-memory PnL records + SQLite-persisted trades (500 cap)

Architecture principles:
  • Read-only extraction   — zero mutation of any engine state
  • Thread-safe            — all buffer access gated by threading.RLock
  • Defensive              — every extraction wrapped in try/except; partial
                             failure embeds an error key, never aborts the package
  • Non-blocking           — synchronous build_package() safe to run in
                             asyncio.to_thread(); nothing awaits inside
  • Zero-corruption        — sink write() is fire-and-forget; exceptions silently
                             discarded, never propagated to the logger caller
  • Bounded memory         — deque maxlen + per-message truncation + export caps
                             prevent snapshot explosion under prolonged runtime

Export limits (configurable via constants):
  _MAX_LOG_BUFFER    2 000   rolling ring buffer size (LRU eviction)
  _MAX_LOG_EXPORT    2 000   records extracted per snapshot
  _MAX_MESSAGE_LEN   2 048   chars per log message (stack traces truncated)
  _MAX_TRADE_EXPORT  500     trade records per snapshot
  _MAX_BUNDLE_BYTES  50 MB   hard ceiling on output ZIP

Integration:
  At app startup call live_process_access.register_log_sink() once.
  Thereafter call live_process_access.build_package(...) from any endpoint.
"""
from __future__ import annotations

import hashlib
import io
import json
import threading
import time
import uuid
import zipfile
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ── Export limits ─────────────────────────────────────────────────────────────

_MAX_LOG_BUFFER    = 2_000          # rolling ring buffer capacity
_MAX_LOG_EXPORT    = 2_000          # records written per snapshot (= buffer size)
_MAX_MESSAGE_LEN   = 2_048          # characters — prevents stack-trace explosion
_MAX_TRADE_EXPORT  = 500            # trade records per snapshot
_MAX_BUNDLE_BYTES  = 50 * 1024 * 1024   # 50 MB ceiling on the output ZIP
_BUILD_VERSION     = "1.1"


# ── Log Sink ──────────────────────────────────────────────────────────────────

class _LogSink:
    """
    Loguru-compatible write sink.
    Captures every log record into a deque with a fixed max length.
    Thread-safe via a reentrant lock so logger calls from any thread are safe.
    Never raises — exceptions are silently dropped to protect the caller.

    Memory analysis:
      Each captured entry holds 6 string fields.  A typical record occupies
      ~300–500 B (Python object overhead + strings).  At maxlen=2 000 the
      buffer peaks at ≈1 MB.  Per-message truncation at 2 048 chars prevents
      oversized stack traces from inflating individual entries.
    """

    def __init__(self, maxlen: int = _MAX_LOG_BUFFER) -> None:
        self._lock:   threading.RLock = threading.RLock()
        self._buf:    deque           = deque(maxlen=maxlen)
        self._maxlen: int             = maxlen

    # loguru calls write(message) where message.record is a dict
    def write(self, message) -> None:        # noqa: ANN001
        try:
            rec = message.record
            raw_msg = str(rec["message"])
            truncated = len(raw_msg) > _MAX_MESSAGE_LEN
            entry: Dict[str, Any] = {
                "ts":        rec["time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "level":     rec["level"].name,
                "module":    rec["module"],
                "func":      rec["function"],
                "line":      rec["line"],
                "message":   raw_msg[:_MAX_MESSAGE_LEN],
                "truncated": truncated,
            }
            with self._lock:
                self._buf.append(entry)
        except Exception:
            pass  # never raise from a loguru sink

    def snapshot(self) -> List[Dict[str, Any]]:
        """
        Return a shallow copy of the current buffer, newest records last.
        Non-destructive; acquires lock for minimal duration.
        """
        with self._lock:
            return list(self._buf)[-_MAX_LOG_EXPORT:]

    def __len__(self) -> int:
        with self._lock:
            return len(self._buf)


# ── Snapshot dataclass ────────────────────────────────────────────────────────

@dataclass
class LiveProcessSnapshot:
    snapshot_id:  str
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
            boot_ts=_boot_ts,          # optional — enables uptime in manifest
        )
        # pkg_bytes is a ready-to-serve ZIP (application/zip)
    """

    def __init__(self) -> None:
        self._log_sink:   _LogSink      = _LogSink(maxlen=_MAX_LOG_BUFFER)
        self._sink_id:    Optional[int]  = None
        self._lock:       threading.RLock = threading.RLock()
        self._registered: bool           = False

    # ── Startup wire-up ───────────────────────────────────────────────────────

    def register_log_sink(self) -> None:
        """
        Install the loguru sink.  Idempotent — safe to call multiple times;
        only the first call installs the sink.  The _registered flag + RLock
        prevents duplicate registration during hot reloads, restart cycles,
        lifespan re-entry, and uvicorn --reload development mode.
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
                    enqueue=False,  # synchronous — shares caller's thread; GIL-safe
                    format="{time:YYYY-MM-DDTHH:mm:ss.SSS}Z | {level:<8} | "
                           "{module}:{function}:{line} | {message}",
                )
                self._registered = True
                logger.info(
                    "[LIVE-PROCESS-ACCESS] Log sink v1.1 registered — "
                    f"buffer={_MAX_LOG_BUFFER} msg_cap={_MAX_MESSAGE_LEN}chars"
                )
            except Exception as exc:
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

        Synchronization model:
          The RL engine has no explicit reader-writer lock.  However:
          (a) Python's GIL ensures single-field reads of primitive types
              (float, int) are atomic — no partial reads of q_value / n_visits.
          (b) We call getattr() with defaults and wrap each ContextState
              in its own try/except, so a mid-iteration mutation drops only
              the affected entry rather than aborting the snapshot.
          (c) The snapshot is a value copy (plain dicts) — once extracted
              there are no live references to engine objects.

          For the current single-process, GIL-protected Python runtime this is
          a safe and accepted pattern for read-only introspection.  A future
          multi-process deployment would require an explicit asyncio.Lock on
          the RL engine's update/read path.

        Returns plain-dict structure with no live references to engine objects.
        """
        if rl_engine_instance is None:
            return {
                "error":        "rl_engine not provided",
                "contexts":     [],
                "meta":         {},
                "captured_at":  _now_iso(),
            }
        try:
            meta = _safe_call(rl_engine_instance.summary, {})

            contexts: List[Dict[str, Any]] = []
            table: Dict[str, Any]  = getattr(rl_engine_instance, "_table", {})
            total_pulls: int       = int(getattr(rl_engine_instance, "_total_pulls", 1) or 1)

            for ctx_key, state in table.items():
                try:
                    n_vis  = int(getattr(state, "n_visits",   0))
                    q_val  = float(getattr(state, "q_value",  0.0))
                    n_win  = int(getattr(state, "n_wins",     0))
                    t_pnl  = float(getattr(state, "total_pnl", 0.0))
                    last_ts = int(getattr(state, "last_ts",   0))
                    wr     = n_win / n_vis if n_vis > 0 else 0.0
                    try:
                        ucb = float(state.ucb_score(total_pulls, 1.5))
                    except Exception:
                        ucb = 0.0
                    if ucb != ucb or ucb > 1e9:   # nan / +inf guard
                        ucb = 999.0
                    contexts.append({
                        "context_key": ctx_key,
                        "n_visits":    n_vis,
                        "q_value":     round(q_val, 4),
                        "ucb_score":   round(ucb,   4),
                        "win_rate":    round(wr,    4),
                        "n_wins":      n_win,
                        "total_pnl":   round(t_pnl, 4),
                        "last_ts":     last_ts,
                    })
                except Exception:
                    continue   # corrupt state — skip, never abort

            contexts.sort(key=lambda x: x["n_visits"], reverse=True)
            return {
                "captured_at":    _now_iso(),
                "total_contexts": len(contexts),
                "meta":           meta,
                "contexts":       contexts,
            }
        except Exception as exc:
            return {
                "error":        str(exc),
                "contexts":     [],
                "meta":         {},
                "captured_at":  _now_iso(),
            }

    def snapshot_trades(
        self,
        pnl_calc_instance:  Any,
        data_lake_instance: Any,
    ) -> Dict[str, Any]:
        """
        Extract trade execution logs.
        Scale behaviour:
          - In-memory: last _MAX_TRADE_EXPORT (500) records from pnl_calc.trades
          - SQLite:    get_trades(limit=_MAX_TRADE_EXPORT) → bounded query
          Both caps prevent bundle growth from growing unbounded over long sessions.
          Export latency is proportional to O(500) record serialisation — sub-ms.
        """
        result: Dict[str, Any] = {
            "captured_at":   _now_iso(),
            "in_memory":     [],
            "persisted":     [],
            "session_stats": {},
            "db_stats":      {},
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
                # Direct call (not via _safe_call) so errors propagate to the
                # except block and surface as persisted_error rather than
                # silently returning an empty list.
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
        boot_ts:             Optional[float]        = None,
    ) -> bytes:
        """
        Assemble a ZIP package containing all live runtime artifacts.

        Safety guarantees:
          • Each artifact extracted in its own try/except block.
          • Failure in one artifact produces an error key in its JSON rather
            than aborting the whole package.
          • The MANIFEST is always written last and always succeeds.
          • SHA-256 hashes are computed per artifact for forensic validation.
          • Output is capped at _MAX_BUNDLE_BYTES (50 MB) — raises ValueError
            if exceeded (indicates misconfiguration or runaway data growth).
          • No live engine state is modified at any point.

        Returns:
            bytes — a complete ZIP archive ready to stream as HTTP response.
        """
        snap_id    = str(uuid.uuid4())
        ts_str     = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        captured_at = _now_iso()
        uptime_sec = round(time.time() - boot_ts, 1) if boot_ts and boot_ts > 0 else None

        # artifact_registry: name → (bytes_content, sha256_hex, size_bytes)
        artifact_registry: Dict[str, Tuple[bytes, str, int]] = {}

        def _register(name: str, content: str | bytes) -> None:
            """Encode, hash, and record an artifact."""
            raw = content.encode("utf-8") if isinstance(content, str) else content
            sha = hashlib.sha256(raw).hexdigest()
            artifact_registry[name] = (raw, sha, len(raw))

        # ── 1. RUNTIME LOG STREAM ─────────────────────────────────────────────
        try:
            log_entries = self.snapshot_logs()
            _register(
                f"07_live_process/{ts_str}_runtime_logs.json",
                json.dumps(
                    {"captured_at": captured_at,
                     "snapshot_id": snap_id,
                     "total_entries": len(log_entries),
                     "max_message_len": _MAX_MESSAGE_LEN,
                     "entries": log_entries},
                    indent=2, default=str,
                ),
            )
            lines = "\n".join(
                f"[{e.get('ts', '')}] "
                f"{e.get('level', ''):8s} | "
                f"{e.get('module', ''):30s} | "
                f"{e.get('message', '')}"
                + (" [TRUNCATED]" if e.get("truncated") else "")
                for e in log_entries
            )
            _register(
                f"07_live_process/{ts_str}_runtime_logs.txt",
                lines or "(no log entries captured — sink may not be registered)",
            )
        except Exception as exc:
            _register(
                f"07_live_process/{ts_str}_runtime_logs_ERROR.txt",
                f"Log snapshot failed: {exc}\n",
            )

        # ── 2. THOUGHT LOG (CT-SCAN decision trace) ───────────────────────────
        try:
            tlog = list(thought_log or [])
            _register(
                f"07_live_process/{ts_str}_thought_log.json",
                json.dumps(
                    {"captured_at": captured_at,
                     "snapshot_id": snap_id,
                     "total_entries": len(tlog),
                     "entries": tlog},
                    indent=2, default=str,
                ),
            )
        except Exception as exc:
            _register(
                f"07_live_process/{ts_str}_thought_log_ERROR.txt",
                f"Thought log snapshot failed: {exc}\n",
            )

        # ── 3. RL Q-TABLE ─────────────────────────────────────────────────────
        try:
            rl_data = self.snapshot_rl_table(rl_engine_instance)
            _register(
                f"07_live_process/{ts_str}_rl_qtable.json",
                json.dumps(rl_data, indent=2, default=str),
            )
        except Exception as exc:
            _register(
                f"07_live_process/{ts_str}_rl_qtable_ERROR.txt",
                f"Q-table snapshot failed: {exc}\n",
            )

        # ── 4. TRADE EXECUTION LOGS ───────────────────────────────────────────
        try:
            trade_data = self.snapshot_trades(pnl_calc_instance, data_lake_instance)
            _register(
                f"07_live_process/{ts_str}_trade_logs.json",
                json.dumps(trade_data, indent=2, default=str),
            )
        except Exception as exc:
            _register(
                f"07_live_process/{ts_str}_trade_logs_ERROR.txt",
                f"Trade log snapshot failed: {exc}\n",
            )

        # ── 5. SHA-256 CHECKSUMS FILE ─────────────────────────────────────────
        checksum_lines = [
            f"{sha}  {name.split('/')[-1]}"
            for name, (_, sha, _sz) in artifact_registry.items()
        ]
        _register(
            f"07_live_process/{ts_str}_CHECKSUMS.sha256",
            "\n".join(checksum_lines) + "\n",
        )

        # ── 6. MANIFEST (written last — includes artifact sizes + hashes) ─────
        manifest = {
            "framework":         "EOW Live Process Access Framework",
            "version":           _BUILD_VERSION,
            "snapshot_id":       snap_id,
            "generated_at":      captured_at,
            "runtime_uptime_sec": uptime_sec,
            "contents": {
                "*_runtime_logs.json":  f"All loguru log records (last {_MAX_LOG_EXPORT})",
                "*_runtime_logs.txt":   "Human-readable plain-text log stream",
                "*_thought_log.json":   "Engine CT-Scan decision trace (last 500 thoughts)",
                "*_rl_qtable.json":     "Complete RL Q-table — all context states",
                "*_trade_logs.json":    "In-memory + SQLite trade execution history",
                "*_CHECKSUMS.sha256":   "SHA-256 hashes for all artifacts",
            },
            "export_limits": {
                "max_log_records":    _MAX_LOG_EXPORT,
                "max_message_len":    _MAX_MESSAGE_LEN,
                "max_trade_records":  _MAX_TRADE_EXPORT,
                "max_bundle_bytes":   _MAX_BUNDLE_BYTES,
            },
            "artifact_sizes": {
                name.split("/")[-1]: sz
                for name, (_, _, sz) in artifact_registry.items()
            },
            "sha256_hashes": {
                name.split("/")[-1]: sha
                for name, (_, sha, _) in artifact_registry.items()
            },
            "architecture": {
                "extraction_mode":   "read-only",
                "thread_safety":     "threading.RLock on all buffer access",
                "corruption_risk":   "zero — no mutation of engine state",
                "blocking":          "non-blocking (safe for asyncio.to_thread)",
                "rl_consistency":    "GIL-protected primitive reads; per-entry try/except",
            },
        }
        _register(
            f"07_live_process/{ts_str}_MANIFEST.json",
            json.dumps(manifest, indent=2, default=str),
        )

        # ── Assemble ZIP ──────────────────────────────────────────────────────
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, (raw, _sha, _sz) in artifact_registry.items():
                zf.writestr(name, raw)

        result_bytes = buf.getvalue()

        # Hard ceiling check — raises rather than silently delivering oversized package
        if len(result_bytes) > _MAX_BUNDLE_BYTES:
            raise ValueError(
                f"[LPA] Package exceeds {_MAX_BUNDLE_BYTES // (1024*1024)} MB ceiling "
                f"({len(result_bytes) // (1024*1024)} MB actual). "
                "Reduce log verbosity or lower _MAX_LOG_BUFFER."
            )

        return result_bytes

    # ── Introspection ─────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Health summary — safe to expose via /api/status endpoints."""
        return {
            "module":            "LIVE_PROCESS_ACCESS",
            "version":           _BUILD_VERSION,
            "sink_registered":   self._registered,
            "sink_id":           self._sink_id,
            "log_buffer_len":    len(self._log_sink),
            "log_buffer_max":    _MAX_LOG_BUFFER,
            "max_message_len":   _MAX_MESSAGE_LEN,
            "max_trade_export":  _MAX_TRADE_EXPORT,
            "max_bundle_mb":     _MAX_BUNDLE_BYTES // (1024 * 1024),
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

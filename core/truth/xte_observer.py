"""
XTE Observer — FTD-094A (XTE Observation Activation)

Observation-only wrapper around the (otherwise dormant) Exit Truth Engine.

Scores OPEN positions tick-by-tick and records ONE trajectory summary per closed
trade for offline calibration. This layer has NO execution authority: it never
modifies stop-loss, take-profit, position quantity, nor forces a close. It only
reads position state and writes JSONL telemetry.

Gated by `cfg.XTE_OBSERVE_ENABLED` (default False). When disabled the engine
never reaches this module — the call sites in main.py short-circuit on the flag.

Why a separate module (not main.py inline): keeps the per-tick scoring,
trajectory accumulation, and archive I/O unit-testable without a live engine
(see tests/verify_xte_observer.py) and isolates all XTE state behind one lock.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_PATH_MAX = 400   # GAP-C4: bounded per-trade path length

from loguru import logger

from config import cfg
from core.truth.exit_truth_engine import exit_truth_engine


def _current_r(side: str, entry: float, price: float, init_sl: float) -> float:
    # Sign-aware R-multiple of the live position. entry_risk per unit is the
    # initial SL distance; guard the degenerate zero-distance case.
    if side == "SHORT":
        risk = init_sl - entry
        return (entry - price) / risk if risk > 0 else 0.0
    risk = entry - init_sl
    return (price - entry) / risk if risk > 0 else 0.0


def _advisory_label(adv: Any) -> str:
    # Collapse the XTEAdvisory bool-set into the single strongest action label.
    if getattr(adv, "scale_out", False):
        return "SCALE_OUT"
    if getattr(adv, "tighten_tsl", False):
        return "TIGHTEN"
    if getattr(adv, "trigger_be", False):
        return "BREAKEVEN"
    if getattr(adv, "hold", True):
        return "HOLD"
    return "NEUTRAL"


@dataclass
class _Trajectory:
    symbol: str
    side: str
    regime: str
    entry_ts: int
    evals: int = 0
    score_sum: float = 0.0
    peak_score: float = 0.0
    min_score: float = 100.0
    last_score: float = 0.0
    last_advisory: str = "HOLD"
    advisory_transitions: int = 0
    peak_r_seen: float = 0.0
    path: List[dict] = field(default_factory=list)   # GAP-C4: per-tick path (bounded)


class XTEObserver:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._trajectories: Dict[str, _Trajectory] = {}
        self._closed_count = 0
        self._last_record: Optional[dict] = None

    # ── Config helpers ────────────────────────────────────────────────────────
    def _archive_path(self) -> str:
        return getattr(
            cfg, "XTE_OBSERVE_ARCHIVE",
            "reports/xte_observations/xte_observations.jsonl",
        )

    # ── Per-tick observation (open position) ──────────────────────────────────
    def observe(
        self,
        position: Any,
        price: float,
        closes: List[float],
        volumes: List[float],
        atr_pct: float,
        atr_ema: float,
    ) -> Optional[Any]:
        """Score one open position. Returns the XTEResult (or None on failure).
        NEVER mutates `position`."""
        side = getattr(position, "side", "LONG")
        entry = float(getattr(position, "entry_price", 0.0) or 0.0)
        init_sl = float(
            getattr(position, "initial_stop_loss", 0.0)
            or getattr(position, "stop_loss", 0.0)
            or 0.0
        )
        cur_r = _current_r(side, entry, price, init_sl)
        peak_r = float(getattr(position, "peak_r", 0.0) or 0.0)

        result = exit_truth_engine.evaluate(
            closes=list(closes or []),
            volumes=list(volumes or []),
            atr_pct=float(atr_pct or 0.0),
            atr_ema=float(atr_ema or 0.0),
            current_r=cur_r,
            peak_r=peak_r,
            side="LONG" if side == "LONG" else "SHORT",
        )

        sym = getattr(position, "symbol", "?")
        label = _advisory_label(result.advisory)
        with self._lock:
            traj = self._trajectories.get(sym)
            if traj is None:
                traj = _Trajectory(
                    symbol=sym,
                    side=side,
                    regime=getattr(position, "regime", "UNKNOWN"),
                    entry_ts=int(getattr(position, "entry_ts", int(time.time() * 1000))),
                )
                self._trajectories[sym] = traj
            traj.evals += 1
            traj.score_sum += result.score
            traj.peak_score = max(traj.peak_score, result.score)
            traj.min_score = min(traj.min_score, result.score)
            if traj.evals > 1 and label != traj.last_advisory:
                traj.advisory_transitions += 1
            traj.last_advisory = label
            traj.last_score = result.score
            traj.peak_r_seen = max(traj.peak_r_seen, peak_r)
            if getattr(cfg, "XTE_OBSERVE_PATH_ENABLED", False) and len(traj.path) < _PATH_MAX:
                traj.path.append({
                    "price": round(float(price), 6),
                    "current_r": round(cur_r, 4),
                    "peak_r": round(peak_r, 4),
                    "score": round(result.score, 1),
                    "advisory": label,
                })
        return result

    # ── Per-trade finalization (position closed) ──────────────────────────────
    def on_close(self, symbol: str, trade_record: Any, tag: str = "") -> Optional[dict]:
        """Build and persist one observation record joining the XTE trajectory to
        the realized exit outcome. Returns the record (or None if persist fails).
        `tag` (optional) stamps record["source"] for provenance (e.g. backfill)."""
        with self._lock:
            traj = self._trajectories.pop(symbol, None)

        exit_r = float(getattr(trade_record, "r_multiple", 0.0) or 0.0)
        peak_r = float(getattr(trade_record, "peak_r", 0.0) or 0.0)
        if traj is not None:
            peak_r = max(peak_r, traj.peak_r_seen)
        net_pnl = float(getattr(trade_record, "net_pnl", 0.0) or 0.0)
        regime = getattr(trade_record, "regime", None) or (traj.regime if traj else "UNKNOWN")
        entry_ts = int(getattr(trade_record, "entry_ts", 0) or (traj.entry_ts if traj else 0))
        exit_ts = int(getattr(trade_record, "exit_ts", 0) or int(time.time() * 1000))
        duration_s = round(max(0.0, (exit_ts - entry_ts) / 1000.0), 1) if entry_ts else 0.0

        giveback_pct = round((peak_r - exit_r) / peak_r * 100, 2) if peak_r > 0 else 0.0
        profit_capture = (
            round(exit_r / peak_r, 4) if peak_r > 0 else (1.0 if exit_r >= 0 else 0.0)
        )
        exit_method = (
            getattr(trade_record, "exit_method", "")
            or getattr(trade_record, "exit_reason", "")
            or "UNKNOWN"
        )

        record = {
            "ts": int(time.time() * 1000),
            "exit_ts": exit_ts,
            "symbol": symbol,
            "regime": regime,
            "duration_s": duration_s,
            "exit_r": round(exit_r, 4),
            "peak_r": round(peak_r, 4),
            "giveback_pct": giveback_pct,
            "profit_capture": profit_capture,
            "volatility_atr_pct": round(float(getattr(trade_record, "atr_pct", 0.0) or 0.0), 6),
            "net_pnl": round(net_pnl, 6),
            "exit_method": exit_method,
            "won": net_pnl >= 0,
            "xte_evals": traj.evals if traj else 0,
            "xte_score_last": round(traj.last_score, 1) if traj else None,
            "xte_score_avg": round(traj.score_sum / traj.evals, 1) if traj and traj.evals else None,
            "xte_score_peak": round(traj.peak_score, 1) if traj and traj.evals else None,
            "xte_score_min": round(traj.min_score, 1) if traj and traj.evals else None,
            "xte_advisory_last": traj.last_advisory if traj else None,
            "xte_advisory_transitions": traj.advisory_transitions if traj else 0,
        }
        if tag:
            record["source"] = tag

        if not self._append(record):
            return None
        # GAP-C4: persist the per-tick path (separate archive) for path-accurate replay.
        if traj is not None and traj.path:
            self._append_path({
                "ts": record["ts"], "exit_ts": exit_ts, "symbol": symbol, "regime": regime,
                "exit_method": exit_method, "exit_r": round(exit_r, 4),
                "peak_r": round(peak_r, 4), "won": net_pnl >= 0,
                "net_pnl": round(net_pnl, 6), "path": traj.path,
            })
        with self._lock:
            self._closed_count += 1
            self._last_record = record
        return record

    def _append_path(self, record: dict) -> bool:
        path = getattr(cfg, "XTE_PATH_ARCHIVE", "reports/xte_observations/xte_paths.jsonl")
        try:
            with self._lock:
                d = os.path.dirname(path)
                if d:
                    os.makedirs(d, exist_ok=True)
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record) + "\n")
            return True
        except Exception as e:
            logger.warning(f"[XTE-OBS] path archive append failed: {e}")
            return False

    def _append(self, record: dict) -> bool:
        path = self._archive_path()
        try:
            with self._lock:
                d = os.path.dirname(path)
                if d:
                    os.makedirs(d, exist_ok=True)
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record) + "\n")
            return True
        except Exception as e:
            logger.warning(f"[XTE-OBS] archive append failed: {e}")
            return False

    # ── Read / report ─────────────────────────────────────────────────────────
    def read_records(self, limit: Optional[int] = None) -> List[dict]:
        path = self._archive_path()
        if not os.path.exists(path):
            return []
        out: List[dict] = []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"[XTE-OBS] archive read failed: {e}")
            return []
        return out[-limit:] if limit else out

    def summary(self) -> dict:
        with self._lock:
            session_closed = self._closed_count
            active = len(self._trajectories)
            last = self._last_record
        total = len(self.read_records())
        return {
            "observe_enabled": bool(getattr(cfg, "XTE_OBSERVE_ENABLED", False)),
            "archive_path": self._archive_path(),
            "archive_samples": total,
            "calibration_target": 500,
            "calibration_progress_pct": round(min(100.0, total / 500 * 100), 1),
            "session_closed_observations": session_closed,
            "active_trajectories": active,
            "last_record": last,
        }

    def report_sections(self) -> dict:
        """Phase 5 — institutional report sections derived from the archive."""
        rows = self.read_records()
        n = len(rows)
        header = {
            "sample_count": n,
            "calibration_target": 500,
            "calibration_progress_pct": round(min(100.0, n / 500 * 100), 1),
            "observe_enabled": bool(getattr(cfg, "XTE_OBSERVE_ENABLED", False)),
        }
        if n == 0:
            return {
                "header": header,
                "score_distribution": {},
                "advisory_distribution": {},
                "giveback_analysis": {},
                "xte_vs_actual_exit": {},
                "note": "No XTE observations archived yet. Set XTE_OBSERVE_ENABLED=True to begin collection.",
            }

        def _bucket(score: Optional[float]) -> str:
            if score is None:
                return "n/a"
            b = int(score // 10) * 10
            return f"{b}-{b + 10}"

        # 1. Score distribution (by avg score)
        score_dist: Dict[str, int] = {}
        for r in rows:
            score_dist[_bucket(r.get("xte_score_avg"))] = score_dist.get(_bucket(r.get("xte_score_avg")), 0) + 1

        # 2. Advisory distribution (last advisory)
        adv_dist: Dict[str, int] = {}
        for r in rows:
            key = r.get("xte_advisory_last") or "n/a"
            adv_dist[key] = adv_dist.get(key, 0) + 1

        # 3. Giveback analysis
        gb = [r.get("giveback_pct", 0.0) for r in rows]
        winners = [r for r in rows if r.get("won")]
        losers = [r for r in rows if not r.get("won")]
        giveback_analysis = {
            "avg_giveback_pct": round(sum(gb) / n, 2),
            "avg_giveback_winners_pct": round(sum(r.get("giveback_pct", 0.0) for r in winners) / len(winners), 2) if winners else None,
            "avg_profit_capture": round(sum(r.get("profit_capture", 0.0) for r in rows) / n, 4),
            "be_scratch_rate_pct": round(
                sum(1 for r in rows if abs(r.get("exit_r", 0.0)) < 0.1) / n * 100, 1
            ),
        }

        # 4. XTE vs actual exit — does the live score track realized outcome?
        by_bucket: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            key = _bucket(r.get("xte_score_avg"))
            agg = by_bucket.setdefault(key, {"n": 0, "exit_r_sum": 0.0, "wins": 0, "gb_sum": 0.0})
            agg["n"] += 1
            agg["exit_r_sum"] += r.get("exit_r", 0.0)
            agg["wins"] += 1 if r.get("won") else 0
            agg["gb_sum"] += r.get("giveback_pct", 0.0)
        xte_vs_actual = {
            k: {
                "n": v["n"],
                "avg_exit_r": round(v["exit_r_sum"] / v["n"], 4),
                "win_rate_pct": round(v["wins"] / v["n"] * 100, 1),
                "avg_giveback_pct": round(v["gb_sum"] / v["n"], 2),
            }
            for k, v in sorted(by_bucket.items())
        }

        return {
            "header": header,
            "score_distribution": dict(sorted(score_dist.items())),
            "advisory_distribution": adv_dist,
            "giveback_analysis": giveback_analysis,
            "xte_vs_actual_exit": xte_vs_actual,
        }

    def reset(self) -> None:
        # Test/maintenance hook — clears in-memory trajectory state only.
        with self._lock:
            self._trajectories.clear()
            self._closed_count = 0
            self._last_record = None


# Module-level singleton
xte_observer = XTEObserver()

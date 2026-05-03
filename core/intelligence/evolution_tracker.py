"""
EOW Quant Engine — core/intelligence/evolution_tracker.py
FTD-EV-001: Automatic Evolution Monitoring Framework

Implements 3 pillars from the evolution governance framework:

  A. DRIFT DETECTION (Behavioral Analysis — Anomaly Detection)
     Detects when self-corrections are systematically making performance worse.
     If DRIFT_WINDOW consecutive correction outcomes show degradation →
     raise DRIFT alert and pause auto-correction for DRIFT_PAUSE_CYCLES cycles.

  B. PERFORMANCE TRAJECTORY (Outcome Prediction)
     Rolling analysis of recent trade outcomes to predict system direction:
     IMPROVING / STABLE / DEGRADING. Used by auto_intelligence_engine to
     adjust correction aggressiveness.

  C. CRITICAL ALERTING (Reporting — Critical Alert Triggers)
     Immediate alerts when predefined safety thresholds are crossed:
       - Win rate < WIN_RATE_DANGER for last DANGER_WINDOW trades
       - Single trade loss > SINGLE_LOSS_DANGER_MULT × avg_loss
       - Session drawdown > DRAWDOWN_DANGER_PCT
     Alerts are logged and stored for dashboard display.

Design: stateless per call where possible; state stored in-memory (session-only).
No external dependencies beyond stdlib + loguru.
"""
from __future__ import annotations

import json
import pathlib
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Thresholds ─────────────────────────────────────────────────────────────────

DRIFT_WINDOW        = 3      # consecutive degrading corrections → DRIFT
DRIFT_PAUSE_CYCLES  = 2      # correction cycles to skip after drift detected
TRAJ_WINDOW         = 20     # trades to analyse for trajectory
TRAJ_IMPROVE_DELTA  = 0.03   # WR must improve by ≥3pp to be IMPROVING
TRAJ_DEGRADE_DELTA  = 0.03   # WR must fall by ≥3pp to be DEGRADING

WIN_RATE_DANGER     = 0.28   # WR < 28% for last DANGER_WINDOW trades → CRITICAL
DANGER_WINDOW       = 10     # consecutive trades used for danger check
SINGLE_LOSS_MULT    = 3.0    # single trade loss > 3× session avg_loss → OUTLIER
DRAWDOWN_DANGER     = 0.15   # session drawdown > 15% → CRITICAL

EVOLUTION_REPORT_PATH = pathlib.Path("reports/auto_intelligence/evolution_status.json")


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class CorrectionSnapshot:
    cycle_id:    str
    ts:          int
    n_trades:    int
    win_rate:    float    # 0–1
    net_pnl:     float
    drawdown:    float
    is_pre:      bool     # True = before correction, False = after


@dataclass
class EvolutionAlert:
    alert_id:   str
    ts:         int
    kind:       str       # DRIFT | WR_CRITICAL | LOSS_OUTLIER | DD_CRITICAL
    severity:   str       # WARNING | CRITICAL
    message:    str
    context:    Dict[str, Any] = field(default_factory=dict)


class EvolutionTracker:
    """
    FTD-EV-001 — System evolution monitor.
    One singleton per process; reset on session restart is acceptable.
    """

    MODULE = "EVOLUTION_TRACKER"

    def __init__(self):
        self._snapshots: List[CorrectionSnapshot] = []
        self._alerts:    List[EvolutionAlert]     = []
        self._paused_until_cycle: int = 0          # cycle number when pause expires
        self._cycle_count: int = 0
        self._reactive_log: List[Dict[str, Any]] = []  # FTD-REA-001 per-trade adjustments

        logger.info(
            f"[EV-001] Evolution Tracker online | "
            f"drift_window={DRIFT_WINDOW} traj_window={TRAJ_WINDOW} "
            f"wr_danger={WIN_RATE_DANGER:.0%} dd_danger={DRAWDOWN_DANGER:.0%}"
        )

    # ── A: Drift Detection ────────────────────────────────────────────────────

    def record_pre_correction(
        self,
        cycle_id:  str,
        n_trades:  int,
        win_rate:  float,
        net_pnl:   float,
        drawdown:  float,
    ) -> None:
        self._snapshots.append(CorrectionSnapshot(
            cycle_id=cycle_id, ts=int(time.time() * 1000),
            n_trades=n_trades, win_rate=win_rate,
            net_pnl=net_pnl, drawdown=drawdown, is_pre=True,
        ))
        logger.debug(
            f"[EV-001] PRE  cycle={cycle_id} wr={win_rate:.1%} "
            f"pnl={net_pnl:.2f} dd={drawdown:.1f}%"
        )

    def record_post_correction(
        self,
        cycle_id:  str,
        n_trades:  int,
        win_rate:  float,
        net_pnl:   float,
        drawdown:  float,
    ) -> None:
        self._cycle_count += 1
        self._snapshots.append(CorrectionSnapshot(
            cycle_id=cycle_id, ts=int(time.time() * 1000),
            n_trades=n_trades, win_rate=win_rate,
            net_pnl=net_pnl, drawdown=drawdown, is_pre=False,
        ))
        logger.debug(
            f"[EV-001] POST cycle={cycle_id} wr={win_rate:.1%} "
            f"pnl={net_pnl:.2f} dd={drawdown:.1f}%"
        )
        self._evaluate_drift(cycle_id)
        self._persist()

    def check_drift_pause(self) -> bool:
        """Return True if auto-correction should be paused due to drift.
        Bug fix: 0 <= 0 was always True on fresh start, permanently blocking
        self-learning before any cycle ran. Now only pauses when a real drift
        event has set paused_until_cycle above zero AND cycles have started.
        """
        return self._cycle_count > 0 and self._cycle_count <= self._paused_until_cycle

    def _evaluate_drift(self, cycle_id: str) -> None:
        """Compare last DRIFT_WINDOW pre/post pairs. If all show degradation → DRIFT."""
        pairs = self._extract_pairs()
        if len(pairs) < DRIFT_WINDOW:
            return

        recent_pairs = pairs[-DRIFT_WINDOW:]
        degraded = [
            post.win_rate < pre.win_rate - 0.01   # WR dropped > 1pp after correction
            for pre, post in recent_pairs
        ]
        if all(degraded):
            self._paused_until_cycle = self._cycle_count + DRIFT_PAUSE_CYCLES
            alert = EvolutionAlert(
                alert_id=f"DRIFT_{cycle_id}",
                ts=int(time.time() * 1000),
                kind="DRIFT",
                severity="CRITICAL",
                message=(
                    f"Evolution DRIFT detected: {DRIFT_WINDOW} consecutive corrections "
                    f"degraded win rate. Pausing auto-correction for "
                    f"{DRIFT_PAUSE_CYCLES} cycles."
                ),
                context={
                    "pairs_checked": DRIFT_WINDOW,
                    "wr_deltas": [
                        round(post.win_rate - pre.win_rate, 4)
                        for pre, post in recent_pairs
                    ],
                    "resume_at_cycle": self._paused_until_cycle,
                },
            )
            self._alerts.append(alert)
            logger.warning(
                f"[EV-001] ⚠ DRIFT DETECTED — corrections pausing until "
                f"cycle #{self._paused_until_cycle}. "
                f"WR deltas: {[round(p.win_rate - r.win_rate, 3) for r, p in recent_pairs]}"
            )

    def _extract_pairs(self) -> List[tuple]:
        """Match pre/post snapshots by cycle_id → list of (pre, post) tuples."""
        pre_map = {s.cycle_id: s for s in self._snapshots if s.is_pre}
        pairs = []
        for s in self._snapshots:
            if not s.is_pre and s.cycle_id in pre_map:
                pairs.append((pre_map[s.cycle_id], s))
        return pairs

    # ── B: Performance Trajectory ─────────────────────────────────────────────

    def compute_trajectory(self, recent_trades: List[Any]) -> Dict[str, Any]:
        """
        Analyse the last TRAJ_WINDOW closed trades (each must have .net_pnl).
        Returns: { verdict, win_rate, win_rate_prev, wr_delta, direction }
        """
        if len(recent_trades) < TRAJ_WINDOW // 2:
            return {"verdict": "INSUFFICIENT_DATA", "reason": f"need≥{TRAJ_WINDOW//2} trades"}

        window = recent_trades[-TRAJ_WINDOW:]
        half   = max(1, len(window) // 2)

        first_half  = window[:half]
        second_half = window[half:]

        wr_first  = sum(1 for t in first_half  if t.net_pnl > 0) / len(first_half)
        wr_second = sum(1 for t in second_half if t.net_pnl > 0) / len(second_half)
        wr_delta  = wr_second - wr_first

        if wr_delta >= TRAJ_IMPROVE_DELTA:
            verdict = "IMPROVING"
        elif wr_delta <= -TRAJ_DEGRADE_DELTA:
            verdict = "DEGRADING"
        else:
            verdict = "STABLE"

        result = {
            "verdict":    verdict,
            "win_rate":   round(wr_second, 4),
            "wr_prev":    round(wr_first, 4),
            "wr_delta":   round(wr_delta, 4),
            "window":     len(window),
            "direction":  "↑" if verdict == "IMPROVING" else ("↓" if verdict == "DEGRADING" else "→"),
        }
        logger.info(
            f"[EV-001] Trajectory: {verdict} | "
            f"wr {wr_first:.1%}→{wr_second:.1%} (Δ{wr_delta:+.1%})"
        )
        return result

    # ── C: Critical Alerting ──────────────────────────────────────────────────

    def check_critical_alerts(
        self,
        recent_trades:  List[Any],
        session_dd_pct: float,
        last_trade_pnl: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fire CRITICAL alerts when safety thresholds are crossed.
        Call once after each trade closes.
        Returns list of new alerts fired this call.
        """
        new_alerts: List[Dict[str, Any]] = []

        # ── Alert C1: Win rate danger ──────────────────────────────────────────
        if len(recent_trades) >= DANGER_WINDOW:
            recent_window = recent_trades[-DANGER_WINDOW:]
            wr = sum(1 for t in recent_window if t.net_pnl > 0) / DANGER_WINDOW
            if wr < WIN_RATE_DANGER:
                alert = EvolutionAlert(
                    alert_id=f"WR_CRIT_{int(time.time())}",
                    ts=int(time.time() * 1000),
                    kind="WR_CRITICAL",
                    severity="CRITICAL",
                    message=(
                        f"Win rate {wr:.1%} below danger threshold {WIN_RATE_DANGER:.0%} "
                        f"for last {DANGER_WINDOW} trades."
                    ),
                    context={"wr": wr, "window": DANGER_WINDOW, "threshold": WIN_RATE_DANGER},
                )
                self._alerts.append(alert)
                new_alerts.append(asdict(alert))
                logger.warning(
                    f"[EV-001] ⚠ WR_CRITICAL: wr={wr:.1%} last {DANGER_WINDOW} trades "
                    f"(threshold {WIN_RATE_DANGER:.0%})"
                )

        # ── Alert C2: Single trade loss outlier ────────────────────────────────
        if last_trade_pnl is not None and last_trade_pnl < 0 and len(recent_trades) >= 5:
            losses = [t.net_pnl for t in recent_trades if t.net_pnl < 0]
            if losses:
                avg_loss = sum(losses) / len(losses)
                if last_trade_pnl < avg_loss * SINGLE_LOSS_MULT:
                    alert = EvolutionAlert(
                        alert_id=f"LOSS_OUT_{int(time.time())}",
                        ts=int(time.time() * 1000),
                        kind="LOSS_OUTLIER",
                        severity="WARNING",
                        message=(
                            f"Loss outlier detected: ${last_trade_pnl:.2f} is "
                            f"{last_trade_pnl/avg_loss:.1f}× the session average loss "
                            f"(${avg_loss:.2f}). Check for slippage."
                        ),
                        context={
                            "trade_pnl":  last_trade_pnl,
                            "avg_loss":   round(avg_loss, 4),
                            "multiplier": round(last_trade_pnl / avg_loss, 2) if avg_loss else 0,
                        },
                    )
                    self._alerts.append(alert)
                    new_alerts.append(asdict(alert))
                    logger.warning(
                        f"[EV-001] ⚠ LOSS_OUTLIER: ${last_trade_pnl:.2f} "
                        f"(avg_loss=${avg_loss:.2f} mult={last_trade_pnl/avg_loss:.1f}×)"
                    )

        # ── Alert C3: Drawdown danger ──────────────────────────────────────────
        if session_dd_pct >= DRAWDOWN_DANGER * 100:
            alert = EvolutionAlert(
                alert_id=f"DD_CRIT_{int(time.time())}",
                ts=int(time.time() * 1000),
                kind="DD_CRITICAL",
                severity="CRITICAL",
                message=(
                    f"Session drawdown {session_dd_pct:.1f}% exceeds danger threshold "
                    f"{DRAWDOWN_DANGER:.0%}."
                ),
                context={"drawdown_pct": session_dd_pct, "threshold": DRAWDOWN_DANGER * 100},
            )
            self._alerts.append(alert)
            new_alerts.append(asdict(alert))
            logger.warning(
                f"[EV-001] ⚠ DD_CRITICAL: drawdown={session_dd_pct:.1f}% "
                f"(threshold={DRAWDOWN_DANGER:.0%})"
            )

        return new_alerts

    # ── FTD-REA-001: Reactive Adjustment Recording ───────────────────────────

    def record_reactive_adjustment(self, adj: Dict[str, Any]) -> None:
        """
        Called by ReactiveEvolutionEngine after every per-trade micro-adjustment.
        Stores the full before/after change record for forensic audit trail.
        """
        self._reactive_log.append(adj)
        logger.debug(
            f"[EV-001] REACTIVE adj recorded: "
            f"{adj.get('symbol')} {adj.get('diagnosis')} "
            f"pnl={adj.get('trade_pnl')} r={adj.get('r_multiple')}"
        )
        self._persist()

    # ── Summary & Persistence ─────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        pairs       = self._extract_pairs()
        drift_paused = self.check_drift_pause()
        recent_alerts = [asdict(a) for a in self._alerts[-10:]]

        recent_corrections = []
        for pre, post in pairs[-5:]:
            recent_corrections.append({
                "cycle_id": post.cycle_id,
                "wr_before": round(pre.win_rate, 4),
                "wr_after":  round(post.win_rate, 4),
                "wr_delta":  round(post.win_rate - pre.win_rate, 4),
                "outcome":   "IMPROVED" if post.win_rate > pre.win_rate + 0.01
                             else ("DEGRADED" if post.win_rate < pre.win_rate - 0.01
                                   else "NEUTRAL"),
            })

        reactive_by_diagnosis: Dict[str, int] = {}
        for r in self._reactive_log:
            d = r.get("diagnosis", "UNKNOWN")
            reactive_by_diagnosis[d] = reactive_by_diagnosis.get(d, 0) + 1

        return {
            "module":               self.MODULE,
            "total_correction_pairs": len(pairs),
            "drift_paused":         drift_paused,
            "paused_until_cycle":   self._paused_until_cycle,
            "current_cycle":        self._cycle_count,
            "recent_corrections":   recent_corrections,
            "total_alerts":         len(self._alerts),
            "active_alerts":        [a for a in recent_alerts
                                     if a["kind"] in ("DRIFT", "WR_CRITICAL", "DD_CRITICAL")],
            "recent_alerts":        recent_alerts,
            "reactive_adjustments": {
                "total":          len(self._reactive_log),
                "by_diagnosis":   reactive_by_diagnosis,
                "recent":         self._reactive_log[-10:],
            },
            "snapshot_ts":          int(time.time() * 1000),
        }

    def _persist(self) -> None:
        try:
            EVOLUTION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            EVOLUTION_REPORT_PATH.write_text(
                json.dumps(self.summary(), indent=2, default=str)
            )
        except Exception:
            pass


# ── Module-level singleton ────────────────────────────────────────────────────
evolution_tracker = EvolutionTracker()

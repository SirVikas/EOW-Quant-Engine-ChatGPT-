"""
EOW Quant Engine — Execution Drive Policy (EDP)

Implements: EXECUTION DRIVE POLICY — SIMPLE & SAFE

Goals:
  1. No idle system — if signals exist but trades = 0 for > EDP_IDLE_DETECTION_MIN,
     enter DRIVE mode: emit forced score_min floor + exploration boost.
  2. Strong signals (score >= EDP_FORCE_SCORE AND rr >= EDP_FORCE_RR) → force execute
     (bypass decay gate; hard gates — risk, fees, drawdown — still apply).
  3. Learning mode — per-minute activity tracking for data collection phase.
  4. Cost control — Net > 0 enforced downstream by execution_engine, not here.

Integration:
  edp.record_signal(sym)      — call once per signal that enters the pipeline
  edp.record_trade(sym)       — call once per trade opened
  edp.get_score_override(min) — lower effective score_min when in DRIVE mode
  edp.should_force_execute(score, rr) — True for elite setups (bypass decay gate)
  edp.summary()               — expose to dashboard / export
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from loguru import logger

try:
    from config import cfg
    _ENABLED              = getattr(cfg, "EDP_ENABLED",              True)
    _FORCE_SCORE          = getattr(cfg, "EDP_FORCE_SCORE",           0.75)
    _FORCE_RR             = getattr(cfg, "EDP_FORCE_RR",              2.0)
    _IDLE_DETECTION_MIN   = getattr(cfg, "EDP_IDLE_DETECTION_MIN",    1.0)
    _DRIVE_SCORE_OVERRIDE = getattr(cfg, "EDP_DRIVE_SCORE_OVERRIDE",  0.40)
except Exception:
    _ENABLED              = True
    _FORCE_SCORE          = 0.75
    _FORCE_RR             = 2.0
    _IDLE_DETECTION_MIN   = 1.0
    _DRIVE_SCORE_OVERRIDE = 0.40


@dataclass
class EDPStatus:
    is_drive_active:    bool
    force_explore:      bool
    score_min_override: float
    idle_minutes:       float
    signals_1min:       int
    trades_1min:        int
    reason:             str = ""


class ExecutionDrivePolicy:
    """
    Monitors per-minute signal/trade activity and enforces the EDP rules.

    DRIVE mode activates when:
      - At least one signal has been seen in the last 60 seconds
      - No trade has been executed for >= EDP_IDLE_DETECTION_MIN minutes

    In DRIVE mode:
      - get_score_override() returns max(current_min, EDP_DRIVE_SCORE_OVERRIDE=0.40)
        effectively capping the minimum score at the absolute floor so dry-spell
        relaxation is immediate rather than waiting for activator tiers.

    Force-execute path (independent of DRIVE mode):
      - should_force_execute(score, rr) returns True when score >= EDP_FORCE_SCORE
        AND rr >= EDP_FORCE_RR, allowing the decay gate to be bypassed for
        elite setups that already cleared all other quality gates.
    """

    def __init__(self):
        self._signal_ts: deque[float] = deque(maxlen=2000)
        self._trade_ts:  deque[float] = deque(maxlen=2000)
        self._last_trade: float       = time.time()
        logger.info(
            f"[EDP] Execution Drive Policy activated | "
            f"idle_thresh={_IDLE_DETECTION_MIN}min "
            f"force_score={_FORCE_SCORE} force_rr={_FORCE_RR} "
            f"drive_floor={_DRIVE_SCORE_OVERRIDE}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def record_signal(self, symbol: str = "") -> None:
        """Call when a non-NONE signal enters the execution pipeline."""
        self._signal_ts.append(time.time())

    def record_trade(self, symbol: str = "") -> None:
        """Call immediately after a trade is opened."""
        ts = time.time()
        self._trade_ts.append(ts)
        self._last_trade = ts
        logger.debug(f"[EDP] Trade recorded | sym={symbol} idle reset")

    def should_force_execute(self, score: float, rr: float) -> bool:
        """
        True when signal has both high score AND high RR, bypassing only
        the confidence-decay gate. All hard gates (risk, fees, DD) still apply.
        """
        if not _ENABLED:
            return False
        if score >= _FORCE_SCORE and rr >= _FORCE_RR:
            logger.info(
                f"[EDP] FORCE_EXECUTE triggered: "
                f"score={score:.3f}>={_FORCE_SCORE} rr={rr:.2f}>={_FORCE_RR}"
            )
            return True
        return False

    def get_score_override(self, current_score_min: float) -> float:
        """
        If in DRIVE mode, return min(current_score_min, EDP_DRIVE_SCORE_OVERRIDE)
        so that the effective threshold never exceeds the absolute floor during
        idle periods. Returns current_score_min unchanged in NORMAL mode.
        """
        if not _ENABLED:
            return current_score_min
        status = self.get_status()
        if status.is_drive_active:
            override = min(current_score_min, _DRIVE_SCORE_OVERRIDE)
            if override < current_score_min:
                logger.info(
                    f"[EDP] DRIVE score_min: {current_score_min:.3f} → {override:.3f} "
                    f"(idle={status.idle_minutes:.1f}min "
                    f"sigs_1m={status.signals_1min} trades_1m=0)"
                )
            return override
        return current_score_min

    def get_status(self) -> EDPStatus:
        now       = time.time()
        cutoff_1m = now - 60.0

        signals_1min = sum(1 for ts in self._signal_ts if ts >= cutoff_1m)
        trades_1min  = sum(1 for ts in self._trade_ts  if ts >= cutoff_1m)
        idle_minutes = (now - self._last_trade) / 60.0

        is_drive = (
            _ENABLED
            and idle_minutes >= _IDLE_DETECTION_MIN
            and signals_1min > 0
            and trades_1min == 0
        )

        return EDPStatus(
            is_drive_active    = is_drive,
            force_explore      = is_drive,
            score_min_override = _DRIVE_SCORE_OVERRIDE if is_drive else 1.0,
            idle_minutes       = round(idle_minutes, 2),
            signals_1min       = signals_1min,
            trades_1min        = trades_1min,
            reason             = (
                f"DRIVE(idle={idle_minutes:.1f}min "
                f"sigs={signals_1min} trades={trades_1min})"
                if is_drive else "NORMAL"
            ),
        )

    def summary(self) -> dict:
        s = self.get_status()
        return {
            "enabled":            _ENABLED,
            "is_drive_active":    s.is_drive_active,
            "idle_minutes":       s.idle_minutes,
            "signals_1min":       s.signals_1min,
            "trades_1min":        s.trades_1min,
            "force_explore":      s.force_explore,
            "drive_score_floor":  _DRIVE_SCORE_OVERRIDE,
            "force_score_thresh": _FORCE_SCORE,
            "force_rr_thresh":    _FORCE_RR,
            "reason":             s.reason,
            "module":             "EXECUTION_DRIVE_POLICY",
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
execution_drive_policy = ExecutionDrivePolicy()

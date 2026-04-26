"""
EOW Quant Engine — Phase 5.1: Trade Activator
Prevents system freeze by relaxing filters when no trades occur.

Tier System (minutes since last trade):
  < T1_MIN           : NORMAL  — no relaxation (score=cfg.MIN_TRADE_SCORE, vol=1.0×)
  T1_MIN – T2_MIN    : TIER_1  — soft relaxation (vol=0.60×, score=0.55)
  T2_MIN – T3_MIN    : TIER_2  — medium relaxation (vol=0.40×, score=0.50)
  ≥ T3_MIN           : TIER_3  — aggressive relaxation (vol=0.30×, score=0.50)

Hard safety floors: score never below 0.45; vol_mult never below 0.20.

Integration: call check() at the start of signal processing to get effective
thresholds, use them in downstream gate checks. Call record_trade() after any
trade is placed to reset the timer.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from config import cfg


# Absolute floors — cannot be overridden by any tier
# qFTD-032: score floor lowered 0.45→0.40. At 0.45 both TIER_1 and TIER_2
# resolve to the same effective min (max(0.45, T1_SCORE=0.44)=0.45) making
# TIER_1 meaningless. Floor 0.40 lets TIER_1 provide real relaxation.
_SCORE_FLOOR   = 0.40
_VOL_MULT_FLOOR = 0.20


@dataclass
class ActivatorResult:
    tier:                str    # "NORMAL" | "TIER_1" | "TIER_2" | "TIER_3"
    effective_score_min: float  # relaxed minimum score threshold
    effective_vol_mult:  float  # multiplier on the volume threshold (1.0 = unchanged)
    active:              bool   # True when any relaxation is in effect
    reason:              str = ""


class TradeActivator:
    """
    Monitors global time-since-last-trade and emits effective filter thresholds.
    Relaxation is proportional to how long the system has been without a trade.
    """

    def __init__(self):
        self._last_trade_ts: float = time.time()
        logger.info(
            f"[TRADE-ACTIVATOR] Phase 5.1 activated | "
            f"tiers: T1={cfg.ACTIVATOR_T1_MIN}min "
            f"T2={cfg.ACTIVATOR_T2_MIN}min "
            f"T3={cfg.ACTIVATOR_T3_MIN}min"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def check(self, minutes_no_trade: float | None = None) -> ActivatorResult:
        """
        Return effective thresholds based on no-trade duration.

        Args:
            minutes_no_trade: explicit override (used in tests).
                              If None, computed from internal timer.
        """
        if minutes_no_trade is None:
            minutes_no_trade = self.minutes_since_last_trade()

        if minutes_no_trade >= cfg.ACTIVATOR_T3_MIN:
            result = ActivatorResult(
                tier="TIER_3",
                effective_score_min=max(_SCORE_FLOOR, cfg.ACTIVATOR_T2_SCORE),
                effective_vol_mult=max(_VOL_MULT_FLOOR, cfg.ACTIVATOR_T3_VOL_MULT),
                active=True,
                reason=f"NO_TRADE_{minutes_no_trade:.0f}min≥T3({cfg.ACTIVATOR_T3_MIN}min)",
            )
            logger.debug(f"[TRADE-ACTIVATOR] {result.reason}")
            return result

        if minutes_no_trade >= cfg.ACTIVATOR_T2_MIN:
            result = ActivatorResult(
                tier="TIER_2",
                effective_score_min=max(_SCORE_FLOOR, cfg.ACTIVATOR_T2_SCORE),
                effective_vol_mult=max(_VOL_MULT_FLOOR, cfg.ACTIVATOR_T2_VOL_MULT),
                active=True,
                reason=f"NO_TRADE_{minutes_no_trade:.0f}min≥T2({cfg.ACTIVATOR_T2_MIN}min)",
            )
            logger.debug(f"[TRADE-ACTIVATOR] {result.reason}")
            return result

        if minutes_no_trade >= cfg.ACTIVATOR_T1_MIN:
            result = ActivatorResult(
                tier="TIER_1",
                effective_score_min=max(_SCORE_FLOOR, cfg.ACTIVATOR_T1_SCORE),
                effective_vol_mult=max(_VOL_MULT_FLOOR, cfg.ACTIVATOR_T1_VOL_MULT),
                active=True,
                reason=f"NO_TRADE_{minutes_no_trade:.0f}min≥T1({cfg.ACTIVATOR_T1_MIN}min)",
            )
            logger.debug(f"[TRADE-ACTIVATOR] {result.reason}")
            return result

        return ActivatorResult(
            tier="NORMAL",
            effective_score_min=cfg.MIN_TRADE_SCORE,
            effective_vol_mult=1.0,
            active=False,
        )

    def no_execution_override(
        self, score_min: float, signals: int, trades: int
    ) -> float:
        """
        FTD-034: Further lower score_min when signals exist but none execute.
        Applies on top of any tier-based relaxation already in effect.
        Floor is always respected (_SCORE_FLOOR = 0.40).
        """
        if signals > 0 and trades == 0:
            adjusted = max(_SCORE_FLOOR, score_min - 0.10)
            if adjusted < score_min:
                logger.debug(
                    f"[TRADE-ACTIVATOR][FTD-034] NO_EXECUTION override: "
                    f"score_min {score_min:.2f} → {adjusted:.2f}"
                )
            return adjusted
        return score_min

    def record_trade(self):
        """Reset the no-trade timer. Call immediately after a trade is placed."""
        self._last_trade_ts = time.time()
        logger.debug("[TRADE-ACTIVATOR] Timer reset — trade placed")

    def minutes_since_last_trade(self) -> float:
        """Elapsed minutes since the last recorded trade."""
        return (time.time() - self._last_trade_ts) / 60.0

    def summary(self) -> dict:
        result = self.check()
        return {
            "minutes_no_trade":    round(self.minutes_since_last_trade(), 1),
            "tier":                result.tier,
            "active":              result.active,
            "effective_score_min": result.effective_score_min,
            "effective_vol_mult":  result.effective_vol_mult,
            "reason":              result.reason,
            "module": "TRADE_ACTIVATOR",
            "phase":  5.1,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
trade_activator = TradeActivator()

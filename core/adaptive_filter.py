"""
EOW Quant Engine — Phase 5.1: Adaptive Filter Engine
Dynamically adjusts score threshold stringency based on system state.

State Machine:
  TIGHTEN : consecutive_losses ≥ AF_TIGHTEN_AFTER_LOSSES
            → raise threshold by AF_TIGHTEN_STEP per extra loss
            → cap at AF_MAX_TIGHTEN above base
  RELAX   : minutes_no_trade ≥ AF_RELAX_AFTER_MIN
            → lower threshold by AF_RELAX_STEP per 30-min increment
            → cap at AF_MAX_RELAX below base
  NORMAL  : all else → no adjustment

Note: TIGHTEN takes priority over RELAX.

Outputs score_offset to be added to cfg.MIN_TRADE_SCORE.
  Negative offset → relaxed (lower bar)
  Positive offset → tightened (higher bar)

Effective threshold is always bounded: [0.40, 0.85]
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


# Absolute bounds on effective score min — cannot be exceeded by offset
_SCORE_MIN_FLOOR   = 0.40
_SCORE_MIN_CEILING = 0.85


@dataclass
class AFResult:
    state:               str    # "RELAX" | "TIGHTEN" | "NORMAL"
    score_offset:        float  # add to cfg.MIN_TRADE_SCORE; negative = relax
    effective_score_min: float  # final threshold after offset + clamping
    reason:              str = ""


class AdaptiveFilterEngine:
    """
    Stateless per-call filter engine.
    State is derived entirely from the inputs, no internal mutation.
    """

    def __init__(self):
        logger.info(
            f"[ADAPTIVE-FILTER] Phase 5.1 activated | "
            f"relax_after={cfg.AF_RELAX_AFTER_MIN}min "
            f"tighten_after={cfg.AF_TIGHTEN_AFTER_LOSSES}losses "
            f"steps=[relax={cfg.AF_RELAX_STEP} tighten={cfg.AF_TIGHTEN_STEP}]"
        )

    def check(
        self,
        consecutive_losses: int   = 0,
        minutes_no_trade:   float = 0.0,
        recent_pnl_pct:     float = 0.0,
    ) -> AFResult:
        """
        Compute filter adjustment based on system state.

        Args:
            consecutive_losses: back-to-back losing trades
            minutes_no_trade:   global minutes since last completed trade
            recent_pnl_pct:     session P&L as fraction of equity (unused currently,
                                reserved for future enhancements)

        Returns AFResult with score_offset and final effective_score_min.
        """
        # TIGHTEN takes priority — loss streak always overrides no-trade relaxation
        if consecutive_losses >= cfg.AF_TIGHTEN_AFTER_LOSSES:
            extra  = consecutive_losses - cfg.AF_TIGHTEN_AFTER_LOSSES
            offset = min(cfg.AF_MAX_TIGHTEN, cfg.AF_TIGHTEN_STEP * (1 + extra))
            eff    = min(_SCORE_MIN_CEILING, cfg.MIN_TRADE_SCORE + offset)
            result = AFResult(
                state="TIGHTEN",
                score_offset=round(offset, 4),
                effective_score_min=round(eff, 4),
                reason=(
                    f"TIGHTEN(losses={consecutive_losses}"
                    f"≥{cfg.AF_TIGHTEN_AFTER_LOSSES} +{offset:.3f})"
                ),
            )
            logger.debug(f"[ADAPTIVE-FILTER] {result.reason}")
            return result

        if minutes_no_trade >= cfg.AF_RELAX_AFTER_MIN:
            extra_steps = int((minutes_no_trade - cfg.AF_RELAX_AFTER_MIN) / 30)
            offset      = min(cfg.AF_MAX_RELAX, cfg.AF_RELAX_STEP * (1 + extra_steps))
            eff         = max(_SCORE_MIN_FLOOR, cfg.MIN_TRADE_SCORE - offset)
            result = AFResult(
                state="RELAX",
                score_offset=round(-offset, 4),
                effective_score_min=round(eff, 4),
                reason=(
                    f"RELAX(no_trade={minutes_no_trade:.0f}min"
                    f"≥{cfg.AF_RELAX_AFTER_MIN}min -{offset:.3f})"
                ),
            )
            logger.debug(f"[ADAPTIVE-FILTER] {result.reason}")
            return result

        return AFResult(
            state="NORMAL",
            score_offset=0.0,
            effective_score_min=cfg.MIN_TRADE_SCORE,
            reason="NORMAL",
        )

    def summary(
        self,
        consecutive_losses: int   = 0,
        minutes_no_trade:   float = 0.0,
    ) -> dict:
        result = self.check(consecutive_losses, minutes_no_trade)
        return {
            "state":               result.state,
            "score_offset":        result.score_offset,
            "effective_score_min": result.effective_score_min,
            "base_score_min":      cfg.MIN_TRADE_SCORE,
            "reason":              result.reason,
            "module": "ADAPTIVE_FILTER",
            "phase":  5.1,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
adaptive_filter = AdaptiveFilterEngine()

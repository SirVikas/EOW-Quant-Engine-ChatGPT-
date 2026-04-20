"""
EOW Quant Engine — Phase 6: Streak Intelligence Engine
Detects hot/cold win-loss streaks and emits a score_min adjustment that
is added on top of the DynamicThresholdProvider's base score_min.

States:
  HOT  (≥ SE_WIN_STREAK_MIN consecutive wins)
       → score_adj = SE_HOT_SCORE_ADJ  (-0.03)  slightly relax score gate
  COLD (≥ SE_LOSS_STREAK_MIN consecutive losses)
       → score_adj = SE_COLD_SCORE_ADJ (+0.05)  tighten score gate
  NEUTRAL → score_adj = 0.0  (no change)

Integration: score_adj is added to thresholds.score_min, clamped to [0.40, ∞).
This is complementary to AdaptiveFilter — the filter controls the base
score_min; the streak engine adds a momentum-aware delta on top.

Non-negotiable: HOT streak never boosts size above 1×; it only makes filters
slightly more permissive, NOT more aggressive.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class StreakResult:
    state:            str    # "HOT" | "COLD" | "NEUTRAL"
    streak_len:       int    # length of the current streak
    score_adjustment: float  # delta to apply to score_min (negative=relax, positive=tighten)
    reason:           str = ""


class StreakIntelligenceEngine:
    """
    Momentum-aware score gate adjuster.
    Reads consecutive win/loss counts and returns a score_min delta.
    Stateless: all streak state is computed from the inputs, not stored.
    """

    def __init__(self):
        logger.info(
            f"[STREAK-ENGINE] Phase 6 activated | "
            f"hot≥{cfg.SE_WIN_STREAK_MIN}wins(adj={cfg.SE_HOT_SCORE_ADJ:+.2f}) "
            f"cold≥{cfg.SE_LOSS_STREAK_MIN}losses(adj={cfg.SE_COLD_SCORE_ADJ:+.2f})"
        )

    def check(
        self,
        consecutive_wins:   int,
        consecutive_losses: int,
    ) -> StreakResult:
        """
        Determine current streak state and emit score_min adjustment.

        Args:
            consecutive_wins:   back-to-back winning trades
            consecutive_losses: back-to-back losing trades

        Returns StreakResult with score_adjustment to apply to score_min.
        COLD takes priority when both are somehow non-zero (shouldn't happen
        in practice, but defensive handling is correct).
        """
        # COLD takes priority — safety over opportunity
        if consecutive_losses >= cfg.SE_LOSS_STREAK_MIN:
            reason = (
                f"STREAK_COLD({consecutive_losses} losses≥{cfg.SE_LOSS_STREAK_MIN}"
                f" → adj={cfg.SE_COLD_SCORE_ADJ:+.2f})"
            )
            logger.debug(f"[STREAK-ENGINE] {reason}")
            return StreakResult(
                state="COLD",
                streak_len=consecutive_losses,
                score_adjustment=cfg.SE_COLD_SCORE_ADJ,
                reason=reason,
            )

        if consecutive_wins >= cfg.SE_WIN_STREAK_MIN:
            reason = (
                f"STREAK_HOT({consecutive_wins} wins≥{cfg.SE_WIN_STREAK_MIN}"
                f" → adj={cfg.SE_HOT_SCORE_ADJ:+.2f})"
            )
            logger.debug(f"[STREAK-ENGINE] {reason}")
            return StreakResult(
                state="HOT",
                streak_len=consecutive_wins,
                score_adjustment=cfg.SE_HOT_SCORE_ADJ,
                reason=reason,
            )

        return StreakResult(
            state="NEUTRAL",
            streak_len=max(consecutive_wins, consecutive_losses),
            score_adjustment=0.0,
        )

    def summary(self) -> dict:
        return {
            "win_streak_min":    cfg.SE_WIN_STREAK_MIN,
            "loss_streak_min":   cfg.SE_LOSS_STREAK_MIN,
            "hot_score_adj":     cfg.SE_HOT_SCORE_ADJ,
            "cold_score_adj":    cfg.SE_COLD_SCORE_ADJ,
            "module": "STREAK_INTELLIGENCE_ENGINE",
            "phase":  6,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
streak_engine = StreakIntelligenceEngine()

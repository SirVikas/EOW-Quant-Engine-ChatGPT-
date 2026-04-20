"""
EOW Quant Engine — Phase 6: Loss Cluster Controller
Circuit breaker for consecutive-loss clusters. Prevents compounding losses
from feeding on each other by stepping down size and imposing a trading pause.

Tier logic (based on consecutive losing trades):
  < LCC_REDUCE_AFTER (3) → NORMAL  — full size, no restriction
  ≥ LCC_REDUCE_AFTER     → REDUCING — size × 0.50, trading continues
  ≥ LCC_PAUSE_AFTER  (5) → PAUSED  — block all new trades for 30 min

The pause is time-based: once LCC_PAUSE_MINUTES have elapsed, the controller
automatically resets to NORMAL. A single win at any point resets the streak.

Non-negotiable: pause duration is enforced in wall-clock time, not trade count.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class LossClusterResult:
    ok:                bool    # False → blocked, do not trade
    size_mult:         float   # 1.0 normal | 0.50 reducing | 0.0 paused
    state:             str     # "NORMAL" | "REDUCING" | "PAUSED"
    consecutive_losses: int
    reason:            str = ""


class LossClusterController:
    """
    Monitors consecutive losses and enforces size reduction / trading pause.
    All new trade signals must pass check() before entering the quality chain.
    """

    def __init__(self):
        self._pause_until: float = 0.0   # epoch-seconds; 0 = not paused
        logger.info(
            f"[LOSS-CLUSTER] Phase 6 activated | "
            f"reduce≥{cfg.LCC_REDUCE_AFTER} losses({cfg.LCC_REDUCE_SIZE_MULT:.0%}×) "
            f"pause≥{cfg.LCC_PAUSE_AFTER} losses({cfg.LCC_PAUSE_MINUTES}min)"
        )

    def check(self, consecutive_losses: int) -> LossClusterResult:
        """
        Evaluate whether the current loss streak warrants intervention.

        Args:
            consecutive_losses: number of back-to-back losing trades

        Returns LossClusterResult; ok=False → skip signal immediately.
        """
        now = time.time()

        # Time-based pause check (highest priority)
        if self._pause_until > now:
            remaining = (self._pause_until - now) / 60.0
            reason = (
                f"LCC_PAUSED({consecutive_losses} losses, "
                f"{remaining:.1f}min remaining)"
            )
            logger.debug(f"[LOSS-CLUSTER] {reason}")
            return LossClusterResult(
                ok=False, size_mult=0.0, state="PAUSED",
                consecutive_losses=consecutive_losses, reason=reason,
            )

        # Trigger new pause if loss count reached pause threshold
        if consecutive_losses >= cfg.LCC_PAUSE_AFTER:
            self._pause_until = now + cfg.LCC_PAUSE_MINUTES * 60.0
            reason = (
                f"LCC_PAUSE_START({consecutive_losses} losses≥{cfg.LCC_PAUSE_AFTER}"
                f" → pause {cfg.LCC_PAUSE_MINUTES}min)"
            )
            logger.warning(f"[LOSS-CLUSTER] {reason}")
            return LossClusterResult(
                ok=False, size_mult=0.0, state="PAUSED",
                consecutive_losses=consecutive_losses, reason=reason,
            )

        # Size reduction zone
        if consecutive_losses >= cfg.LCC_REDUCE_AFTER:
            reason = (
                f"LCC_REDUCING({consecutive_losses} losses≥{cfg.LCC_REDUCE_AFTER}"
                f" → {cfg.LCC_REDUCE_SIZE_MULT:.0%}× size)"
            )
            logger.debug(f"[LOSS-CLUSTER] {reason}")
            return LossClusterResult(
                ok=True, size_mult=cfg.LCC_REDUCE_SIZE_MULT, state="REDUCING",
                consecutive_losses=consecutive_losses, reason=reason,
            )

        return LossClusterResult(
            ok=True, size_mult=1.0, state="NORMAL",
            consecutive_losses=consecutive_losses,
        )

    def reset_pause(self):
        """Force-clear any active pause (call after manual review / win trade)."""
        self._pause_until = 0.0
        logger.info("[LOSS-CLUSTER] Pause manually cleared")

    def is_paused(self) -> bool:
        return self._pause_until > time.time()

    def summary(self) -> dict:
        now = time.time()
        return {
            "paused":           self.is_paused(),
            "pause_remaining_min": max(0.0, round((self._pause_until - now) / 60.0, 1)),
            "reduce_after":     cfg.LCC_REDUCE_AFTER,
            "pause_after":      cfg.LCC_PAUSE_AFTER,
            "pause_minutes":    cfg.LCC_PAUSE_MINUTES,
            "reduce_size_mult": cfg.LCC_REDUCE_SIZE_MULT,
            "module": "LOSS_CLUSTER_CONTROLLER",
            "phase":  6,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
loss_cluster_controller = LossClusterController()

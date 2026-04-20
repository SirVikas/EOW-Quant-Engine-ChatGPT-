"""
EOW Quant Engine — Phase 6: Exploration Guard
Dedicated gate that disables exploration trades for the rest of the day
once cumulative exploration losses reach EG_DAILY_LOSS_CAP_PCT of equity.

Rationale: ExplorationEngine already has a daily cap, but that cap is checked
inside should_explore() after the slot is allocated. This guard provides an
explicit, separately-logged pre-check that sits in the signal flow before
should_explore() is ever called — making the protection auditable at the gate.

Non-negotiable: once the daily cap fires, exploration is disabled until
midnight UTC, regardless of win trades in between.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class ExploreGuardResult:
    allowed:          bool
    daily_loss_pct:   float   # current daily exploration loss as % of equity
    cap_pct:          float   # the cap threshold in use
    reason:           str = ""


class ExplorationGuard:
    """
    Pre-flight gate for the exploration engine.
    Tracks nothing internally — reads daily_loss_pct from ExplorationEngine
    and applies a hard block when the cap is breached.
    """

    def __init__(self):
        logger.info(
            f"[EXPLORE-GUARD] Phase 6 activated | "
            f"daily_loss_cap={cfg.EG_DAILY_LOSS_CAP_PCT:.0%}"
        )

    def check(self, daily_loss_pct: float) -> ExploreGuardResult:
        """
        Decide whether exploration is permitted given current daily losses.

        Args:
            daily_loss_pct: exploration loss today as a fraction of equity.
                            Obtained via exploration_engine.daily_loss_pct(equity).

        Returns ExploreGuardResult; allowed=False → skip exploration for this signal.
        """
        cap = cfg.EG_DAILY_LOSS_CAP_PCT

        if daily_loss_pct >= cap:
            reason = (
                f"EG_BLOCKED(daily_loss={daily_loss_pct:.2%}"
                f"≥cap={cap:.0%})"
            )
            logger.debug(f"[EXPLORE-GUARD] {reason}")
            return ExploreGuardResult(
                allowed=False,
                daily_loss_pct=round(daily_loss_pct, 4),
                cap_pct=cap,
                reason=reason,
            )

        return ExploreGuardResult(
            allowed=True,
            daily_loss_pct=round(daily_loss_pct, 4),
            cap_pct=cap,
            reason=f"EG_OK({daily_loss_pct:.2%}<{cap:.0%})",
        )

    def summary(self) -> dict:
        return {
            "daily_loss_cap_pct": cfg.EG_DAILY_LOSS_CAP_PCT,
            "module": "EXPLORATION_GUARD",
            "phase":  6,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
exploration_guard = ExplorationGuard()

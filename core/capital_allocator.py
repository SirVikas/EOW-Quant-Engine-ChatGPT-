"""
EOW Quant Engine — Phase 4: Capital Allocator (Smart Position Sizing)
Scales position size based on trade confidence score.

Score bands → size multiplier:
  > 0.90  → 2.0× base risk
  > 0.80  → 1.5× base risk
  > 0.70  → 1.0× base risk
  > 0.60  → 0.5× base risk
  ≤ 0.60  → blocked (should not reach here; Trade Scorer already rejects)

Safety caps:
  • MAX_CAPITAL_PER_TRADE — hard cap on risk per trade (% of equity)
  • DAILY_RISK_CAP        — hard cap on total risk risked in a calendar day
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from config import cfg


# Score → size multiplier lookup (descending threshold order)
_SCORE_BANDS = [
    (0.90, 2.0),
    (0.80, 1.5),
    (0.70, 1.0),
    (0.60, 0.5),
]


@dataclass
class AllocationResult:
    size_multiplier: float
    max_risk_usdt:   float
    reason:          str


class CapitalAllocator:
    """
    Translates trade score into a position size multiplier.
    Enforces per-trade capital cap and daily risk cap.
    """

    def __init__(self):
        self.max_capital_pct = cfg.MAX_CAPITAL_PER_TRADE
        self.daily_risk_cap  = cfg.DAILY_RISK_CAP
        self._daily_risk_used: float = 0.0
        self._current_day:     int   = int(time.time()) // 86400
        logger.info(
            f"[CAPITAL-ALLOCATOR] Phase 4 activated | "
            f"max_per_trade={self.max_capital_pct:.0%} "
            f"daily_cap={self.daily_risk_cap:.0%}"
        )

    def _reset_daily_if_needed(self):
        today = int(time.time()) // 86400
        if today != self._current_day:
            self._daily_risk_used = 0.0
            self._current_day = today

    def allocate(
        self,
        trade_score:    float,
        equity:         float,
        base_risk_usdt: float,  # raw USDT risk from CapitalScaler
    ) -> AllocationResult:
        """
        Returns AllocationResult with size_multiplier to apply to qty.
        Returns size_multiplier=0 and reason string when allocation is blocked.
        """
        self._reset_daily_if_needed()

        # Resolve multiplier from score band
        multiplier = 0.0
        for threshold, mult in _SCORE_BANDS:
            if trade_score > threshold:
                multiplier = mult
                break

        if multiplier == 0.0:
            return AllocationResult(
                size_multiplier=0.0, max_risk_usdt=0.0,
                reason=f"SCORE_BELOW_MIN({trade_score:.3f})",
            )

        proposed_risk = base_risk_usdt * multiplier

        # Cap: max % of equity per trade
        max_trade_risk = equity * self.max_capital_pct
        if proposed_risk > max_trade_risk:
            multiplier    = max_trade_risk / base_risk_usdt if base_risk_usdt > 0 else 0.0
            proposed_risk = max_trade_risk

        # Cap: daily risk budget
        remaining_daily = equity * self.daily_risk_cap - self._daily_risk_used
        if remaining_daily <= 0:
            return AllocationResult(
                size_multiplier=0.0, max_risk_usdt=0.0,
                reason="DAILY_RISK_CAP_REACHED",
            )

        final_risk = min(proposed_risk, remaining_daily)
        if base_risk_usdt > 0:
            final_multiplier = final_risk / base_risk_usdt
        else:
            final_multiplier = multiplier

        return AllocationResult(
            size_multiplier=round(final_multiplier, 4),
            max_risk_usdt=round(final_risk, 4),
            reason=f"SCORE={trade_score:.3f} MULT={multiplier:.1f}x OK",
        )

    def record_risk_used(self, risk_usdt: float):
        """Call after a trade is opened to track daily risk consumption."""
        self._reset_daily_if_needed()
        self._daily_risk_used += risk_usdt

    def summary(self, equity: float = 0.0) -> dict:
        self._reset_daily_if_needed()
        # FIX: daily_risk_remaining must be equity-relative, not a raw cap comparison.
        # Use equity if provided, otherwise omit the remaining calculation.
        daily_cap_usdt = equity * self.daily_risk_cap if equity > 0 else None
        remaining = round(max(0.0, daily_cap_usdt - self._daily_risk_used), 4) if daily_cap_usdt is not None else None
        return {
            "max_capital_pct":        self.max_capital_pct,
            "daily_risk_cap":         self.daily_risk_cap,
            "daily_risk_used":        round(self._daily_risk_used, 4),
            "daily_risk_cap_usdt":    round(daily_cap_usdt, 4) if daily_cap_usdt is not None else None,
            "daily_risk_remaining":   remaining,
            "score_bands": {f">{t:.2f}": f"{m}x" for t, m in _SCORE_BANDS},
            "module": "CAPITAL_ALLOCATOR",
            "phase":  4,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
capital_allocator = CapitalAllocator()

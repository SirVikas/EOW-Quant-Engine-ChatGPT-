"""
EOW Quant Engine — Phase 5: Drawdown Controller (Capital Protection)
Protects capital during losing phases via tiered position-size reduction.

Tier table:
  DD < 5%   → 1.00× size  (normal)
  DD 5–10%  → 0.75× size  (soft cut)
  DD 10–15% → 0.50× size  (hard cut)
  DD > 15%  → STOP        (block all new trades)

Operates independently from risk_engine for belt-and-suspenders protection:
  • risk_engine enforces daily loss / streak limits
  • drawdown_controller enforces peak-to-trough equity drawdown

Call update_equity() on every tick; call check() before trade entry.
Equity peak is tracked internally; drawdown is computed as:
  DD% = (peak − current) / peak
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class DrawdownResult:
    allowed:    bool
    multiplier: float   # size multiplier to apply (0 = blocked)
    drawdown:   float   # current drawdown fraction (0–1)
    tier:       str     # "NORMAL" | "SOFT_CUT" | "HARD_CUT" | "STOP"
    reason:     str = ""


class DrawdownController:
    """
    Tracks peak equity and current drawdown.
    Returns a sizing multiplier (or STOP) for each new trade decision.
    """

    def __init__(self):
        self._peak_equity:    float = 0.0
        self._current_equity: float = 0.0
        self._soft_at  = cfg.DD_SOFT_CUT_AT   # 0.05
        self._hard_at  = cfg.DD_HARD_CUT_AT   # 0.10
        self._stop_at  = cfg.DD_STOP_AT        # 0.15
        logger.info(
            f"[DD-CONTROLLER] Phase 5 activated | "
            f"tiers: soft={self._soft_at:.0%} "
            f"hard={self._hard_at:.0%} "
            f"stop={self._stop_at:.0%}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def update_equity(self, equity: float):
        """
        Update current equity and track the all-time high (peak).
        Call on every tick — lightweight float comparison.
        """
        self._current_equity = equity
        if equity > self._peak_equity:
            self._peak_equity = equity

    def check(self) -> DrawdownResult:
        """
        Evaluate current drawdown and return sizing decision.
        Returns DrawdownResult(allowed=False) when DD ≥ STOP threshold.
        """
        if self._peak_equity <= 0:
            return DrawdownResult(
                allowed=True, multiplier=1.0, drawdown=0.0,
                tier="NORMAL", reason="NO_PEAK_YET",
            )

        dd = (self._peak_equity - self._current_equity) / self._peak_equity
        dd = max(0.0, dd)

        if dd >= self._stop_at:
            return DrawdownResult(
                allowed=False, multiplier=0.0, drawdown=round(dd, 4),
                tier="STOP",
                reason=f"DD_STOP({dd:.1%}≥{self._stop_at:.0%})",
            )

        if dd >= self._hard_at:
            return DrawdownResult(
                allowed=True, multiplier=0.50, drawdown=round(dd, 4),
                tier="HARD_CUT",
                reason=f"DD_HARD_CUT({dd:.1%} → 0.50×)",
            )

        if dd >= self._soft_at:
            return DrawdownResult(
                allowed=True, multiplier=0.75, drawdown=round(dd, 4),
                tier="SOFT_CUT",
                reason=f"DD_SOFT_CUT({dd:.1%} → 0.75×)",
            )

        return DrawdownResult(
            allowed=True, multiplier=1.0, drawdown=round(dd, 4),
            tier="NORMAL",
        )

    def current_drawdown(self) -> float:
        """Return current drawdown as a fraction (0–1)."""
        if self._peak_equity <= 0:
            return 0.0
        return max(0.0, (self._peak_equity - self._current_equity) / self._peak_equity)

    def summary(self) -> dict:
        dd = self.current_drawdown()
        return {
            "peak_equity":    round(self._peak_equity, 4),
            "current_equity": round(self._current_equity, 4),
            "drawdown_pct":   round(dd * 100, 2),
            "tier_thresholds": {
                "soft_cut": self._soft_at,
                "hard_cut": self._hard_at,
                "stop":     self._stop_at,
            },
            "module": "DRAWDOWN_CONTROLLER",
            "phase":  5,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
drawdown_controller = DrawdownController()

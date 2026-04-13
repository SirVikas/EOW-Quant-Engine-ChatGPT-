"""
EOW Quant Engine — Risk Engine  (FTD-REF-MASTER-001)
Institutional-grade daily and portfolio risk controls.

Enforces:
  • Risk per trade:    0.5 – 1.0% of current equity
  • Max daily loss:    3% of equity at day-start → halt new entries
  • Max drawdown:      15% → halt new entries
  • Max trades/day:    6 (prevents over-trading)

Dynamic controls:
  • Drawdown ≥ 10% → reduce position size by 50% (half-Kelly mode)
  • Day rollover:    resets daily counters at UTC midnight
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from loguru import logger


# ── Limits ────────────────────────────────────────────────────────────────────
RISK_PCT_MIN        = 0.005   # 0.5% minimum risk per trade
RISK_PCT_MAX        = 0.010   # 1.0% maximum risk per trade
MAX_DAILY_LOSS_PCT  = 0.030   # 3% of equity-at-day-start → halt
MAX_DRAWDOWN_PCT    = 0.150   # 15% peak-to-trough → halt
MAX_TRADES_PER_DAY  = 6       # absolute daily trade cap
SIZE_HALVE_AT_DD    = 0.100   # at 10% DD, cut position size by 50%


@dataclass
class RiskEngineState:
    day_start_equity:  float = 0.0
    daily_pnl:         float = 0.0
    trades_today:      int   = 0
    peak_equity:       float = 0.0
    current_equity:    float = 0.0
    halted:            bool  = False
    halt_reason:       str   = ""
    size_multiplier:   float = 1.0    # 1.0 normal, 0.5 half-Kelly
    last_day:          str   = ""     # "YYYY-MM-DD" for rollover detection


class RiskEngine:
    """
    Portfolio-level risk gatekeeper.
    Call check_new_trade() before opening any position.
    Call record_trade_result() after every close.
    """

    def __init__(self):
        self._state = RiskEngineState()

    # ── Public ────────────────────────────────────────────────────────────────

    def initialize(self, current_equity: float):
        """Call once at engine startup with the current equity."""
        today = _utc_date()
        self._state.current_equity   = current_equity
        self._state.peak_equity      = current_equity
        self._state.day_start_equity = current_equity
        self._state.last_day         = today
        logger.info(
            f"[RISK-ENG] Initialized | equity={current_equity:.2f} "
            f"day={today}"
        )

    def update_equity(self, current_equity: float):
        """
        Update current equity (call on every PnL snapshot).
        Triggers automatic checks and daily rollover.
        """
        self._maybe_rollover(current_equity)
        self._state.current_equity = current_equity
        if current_equity > self._state.peak_equity:
            self._state.peak_equity = current_equity

        # Recompute drawdown and apply dynamic size control
        dd_pct = self._drawdown_pct()
        if dd_pct >= MAX_DRAWDOWN_PCT and not self._state.halted:
            self._halt(f"MAX_DRAWDOWN({dd_pct:.1%}>={MAX_DRAWDOWN_PCT:.0%})")
        elif dd_pct >= SIZE_HALVE_AT_DD and self._state.size_multiplier > 0.5:
            self._state.size_multiplier = 0.5
            logger.warning(
                f"[RISK-ENG] DD={dd_pct:.1%} ≥ {SIZE_HALVE_AT_DD:.0%} → "
                "size halved to 50%."
            )
        elif dd_pct < SIZE_HALVE_AT_DD and self._state.size_multiplier < 1.0:
            self._state.size_multiplier = 1.0
            logger.info("[RISK-ENG] Recovery: size multiplier restored to 100%.")

        # Daily loss check
        daily_loss_pct = self._daily_loss_pct()
        if daily_loss_pct >= MAX_DAILY_LOSS_PCT and not self._state.halted:
            self._halt(
                f"MAX_DAILY_LOSS({daily_loss_pct:.1%}>={MAX_DAILY_LOSS_PCT:.0%})"
            )

    def check_new_trade(self) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        Call BEFORE submitting a new order.
        """
        if self._state.halted:
            return False, f"HALTED: {self._state.halt_reason}"

        if self._state.trades_today >= MAX_TRADES_PER_DAY:
            return False, f"DAILY_TRADE_CAP({self._state.trades_today}/{MAX_TRADES_PER_DAY})"

        daily_loss_pct = self._daily_loss_pct()
        if daily_loss_pct >= MAX_DAILY_LOSS_PCT:
            return False, f"MAX_DAILY_LOSS({daily_loss_pct:.1%})"

        return True, ""

    def compute_risk_usdt(self, equity: float) -> float:
        """
        Returns the USDT amount to risk on the next trade,
        clamped to [RISK_PCT_MIN, RISK_PCT_MAX] × equity,
        and scaled by the current size multiplier.
        """
        base = equity * RISK_PCT_MAX   # 1% baseline
        adjusted = base * self._state.size_multiplier
        minimum = equity * RISK_PCT_MIN
        return max(minimum, adjusted)

    def record_trade_result(self, net_pnl: float):
        """Call after every trade close with the net PnL (positive or negative)."""
        self._state.daily_pnl      += net_pnl
        self._state.trades_today   += 1
        self._state.current_equity += net_pnl
        if self._state.current_equity > self._state.peak_equity:
            self._state.peak_equity = self._state.current_equity

    def resume(self):
        """Manually clear a halt (e.g. start of new trading day)."""
        self._state.halted      = False
        self._state.halt_reason = ""
        logger.info("[RISK-ENG] Halt cleared — trading resumed.")

    # ── State access ──────────────────────────────────────────────────────────

    @property
    def halted(self) -> bool:
        return self._state.halted

    @property
    def size_multiplier(self) -> float:
        return self._state.size_multiplier

    def snapshot(self) -> dict:
        return {
            "halted":           self._state.halted,
            "halt_reason":      self._state.halt_reason,
            "trades_today":     self._state.trades_today,
            "daily_pnl":        round(self._state.daily_pnl, 4),
            "daily_loss_pct":   round(self._daily_loss_pct() * 100, 2),
            "drawdown_pct":     round(self._drawdown_pct() * 100, 2),
            "size_multiplier":  self._state.size_multiplier,
            "peak_equity":      round(self._state.peak_equity, 4),
            "current_equity":   round(self._state.current_equity, 4),
            "limits": {
                "max_daily_loss_pct": MAX_DAILY_LOSS_PCT * 100,
                "max_drawdown_pct":   MAX_DRAWDOWN_PCT * 100,
                "max_trades_per_day": MAX_TRADES_PER_DAY,
                "risk_pct_range":     [RISK_PCT_MIN * 100, RISK_PCT_MAX * 100],
            },
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _drawdown_pct(self) -> float:
        if self._state.peak_equity <= 0:
            return 0.0
        return max(
            0.0,
            (self._state.peak_equity - self._state.current_equity)
            / self._state.peak_equity,
        )

    def _daily_loss_pct(self) -> float:
        if self._state.day_start_equity <= 0:
            return 0.0
        return max(0.0, -self._state.daily_pnl / self._state.day_start_equity)

    def _halt(self, reason: str):
        self._state.halted      = True
        self._state.halt_reason = reason
        logger.error(f"[RISK-ENG] HALTED: {reason}")

    def _maybe_rollover(self, equity: float):
        today = _utc_date()
        if today != self._state.last_day:
            logger.info(
                f"[RISK-ENG] Day rollover {self._state.last_day} → {today}. "
                f"Daily PnL was {self._state.daily_pnl:+.4f} USDT, "
                f"trades={self._state.trades_today}."
            )
            self._state.daily_pnl        = 0.0
            self._state.trades_today     = 0
            self._state.day_start_equity = equity
            self._state.last_day         = today
            # Clear daily-loss halt on new day; DD halt persists
            if self._state.halted and "DAILY" in self._state.halt_reason:
                self.resume()


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Module-level singleton ────────────────────────────────────────────────────
risk_engine = RiskEngine()

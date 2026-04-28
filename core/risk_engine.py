"""
EOW Quant Engine — Risk Engine  (FTD-REF-023 + FTD-REF-024 + FTD-REF-025)
Institutional-grade daily and portfolio risk controls.

Enforces:
  • Risk per trade:    0.5 – 1.5% of current equity
  • Max daily loss:    5% of equity at day-start → halt new entries
  • Max drawdown:      15% → halt new entries
  • Max trades/day:    12 (balanced opportunity window)

Dynamic controls (FTD-REF-023):
  • win_streak  ≥ 3  → increase position size by 20% (scale up winners)
  • loss_streak ≥ 2  → reduce position size by 30% (protect from losers)
  • Day rollover:     resets daily counters at UTC midnight

Capital Preservation Mode — tiered DD cuts (FTD-REF-024):
  •  5% ≤ DD < 10%   → size_multiplier = 0.75 (reduce trading by 25%)
  • 10% ≤ DD < 15%   → size_multiplier = 0.50 (reduce trading by 50%)
  •      DD ≥ 15%    → HALT new entries
  • Recovery < 5% DD → size_multiplier restored to 1.00 automatically

Risk-of-Ruin (FTD-REF-025):
  • RoR is an ADVISORY metric only — never a hard trade block.
  • High RoR → position SIZE is reduced (not trading halted).
  • Hard stops are DD and daily-loss limits only.
  • This prevents a bad historical sample from locking the engine permanently.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from config import cfg


# ── Limits ────────────────────────────────────────────────────────────────────
RISK_PCT_MIN        = 0.005   # 0.5% minimum risk per trade
RISK_PCT_MAX        = 0.015   # 1.5% maximum risk per trade (increased for opportunity)
MAX_DAILY_LOSS_PCT  = 0.050   # 5% of equity-at-day-start → halt (raised from 3%)
MAX_DRAWDOWN_PCT    = 0.150   # 15% peak-to-trough → halt
MAX_TRADES_PER_DAY  = 50      # qFTD-032: 12→50 — multi-currency system needs room to operate
MAX_RISK_OF_RUIN    = 0.60    # RoR threshold for SIZE reduction only (not a trade block)
ROR_SIZE_REDUCTION  = 0.65    # reduce to 65% size when RoR is elevated

# ── Tiered DD size cuts (FTD-REF-024 Capital Preservation Mode) ───────────────
SIZE_SOFT_CUT_AT    = 0.050   # 5% DD  → reduce to SIZE_SOFT_CUT_TO
SIZE_SOFT_CUT_TO    = 0.750   # 75% of normal size at 5% DD
SIZE_HALVE_AT_DD    = 0.100   # 10% DD → reduce to 50%

# ── Streak-based scaling (FTD-REF-023) ───────────────────────────────────────
WIN_STREAK_BOOST_AT   = 3     # consecutive wins before size increase
WIN_STREAK_BOOST_PCT  = 0.20  # +20% per qualifying win streak
LOSS_STREAK_CUT_AT    = 2     # consecutive losses before size reduction
LOSS_STREAK_CUT_PCT   = 0.30  # −30% on qualifying loss streak
MAX_STREAK_MULTIPLIER = 1.40  # ceiling for streak-boosted size
MIN_STREAK_MULTIPLIER = 0.50  # floor (can't go below 50%, combined with DD)


@dataclass
class RiskEngineState:
    day_start_equity:  float = 0.0
    daily_pnl:         float = 0.0
    trades_today:      int   = 0
    peak_equity:       float = 0.0
    current_equity:    float = 0.0
    halted:            bool  = False
    halt_reason:       str   = ""
    size_multiplier:   float = 1.0    # base multiplier (DD + streak combined)
    streak_multiplier: float = 1.0    # streak-only component
    win_streak:        int   = 0
    loss_streak:       int   = 0
    last_day:          str   = ""
    risk_of_ruin:      float = 0.0


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

    def _paper_speed_active(self) -> bool:
        return (cfg.TRADE_MODE == "PAPER" and cfg.PAPER_SPEED_MODE)

    def update_equity(self, current_equity: float):
        """
        Update current equity (call on every PnL snapshot).
        Triggers automatic checks and daily rollover.
        """
        self._maybe_rollover(current_equity)
        self._state.current_equity = current_equity
        if current_equity > self._state.peak_equity:
            self._state.peak_equity = current_equity

        # ── Tiered drawdown → size control (FTD-REF-024) ────────────────────
        dd_pct = self._drawdown_pct()
        if dd_pct >= MAX_DRAWDOWN_PCT and not self._state.halted and not self._paper_speed_active():
            self._halt(f"MAX_DRAWDOWN({dd_pct:.1%}>={MAX_DRAWDOWN_PCT:.0%})")
        elif dd_pct >= SIZE_HALVE_AT_DD:
            # Tier 2: ≥10% DD → halve to 50%
            if self._state.size_multiplier > 0.5:
                self._state.size_multiplier = 0.5
                logger.warning(
                    f"[RISK-ENG] DD={dd_pct:.1%}≥{SIZE_HALVE_AT_DD:.0%}"
                    " → size halved to 50%."
                )
        elif dd_pct >= SIZE_SOFT_CUT_AT:
            # Tier 1: 5–10% DD → capital preservation mode (75%)
            if self._state.size_multiplier != SIZE_SOFT_CUT_TO:
                self._state.size_multiplier = SIZE_SOFT_CUT_TO
                logger.warning(
                    f"[RISK-ENG] DD={dd_pct:.1%}≥{SIZE_SOFT_CUT_AT:.0%}"
                    f" → capital preservation: size={SIZE_SOFT_CUT_TO:.0%}."
                )
        else:
            # Full recovery: DD < 5% → restore to 100%
            if self._state.size_multiplier < 1.0:
                self._state.size_multiplier = 1.0
                logger.info("[RISK-ENG] Recovery: size multiplier restored to 100%.")

        # Daily loss check
        daily_loss_pct = self._daily_loss_pct()
        if daily_loss_pct >= MAX_DAILY_LOSS_PCT and not self._state.halted and not self._paper_speed_active():
            self._halt(
                f"MAX_DAILY_LOSS({daily_loss_pct:.1%}>={MAX_DAILY_LOSS_PCT:.0%})"
            )


    def update_risk_of_ruin(self, risk_of_ruin: float):
        """
        Update latest risk-of-ruin estimate (fraction 0.0-1.0).
        RoR is ADVISORY: it adjusts position size but never halts trading.
        Size recovers automatically when RoR drops below threshold.
        """
        self._state.risk_of_ruin = max(0.0, float(risk_of_ruin))
        if self._state.risk_of_ruin > MAX_RISK_OF_RUIN:
            new_mult = min(self._state.size_multiplier, ROR_SIZE_REDUCTION)
            if new_mult != self._state.size_multiplier:
                self._state.size_multiplier = new_mult
                logger.warning(
                    f"[RISK-ENG] RoR={self._state.risk_of_ruin:.1%} > {MAX_RISK_OF_RUIN:.0%} "
                    f"→ size reduced to {self._state.size_multiplier:.0%} (advisory)."
                )
        else:
            # RoR returned to healthy range — size multiplier restored via DD tiering
            logger.debug(
                f"[RISK-ENG] RoR={self._state.risk_of_ruin:.1%} within limit — no size cut."
            )

    def check_new_trade(self) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        Call BEFORE submitting a new order.

        Hard stops: engine halt, daily trade cap, daily loss limit, max drawdown.
        RoR is ADVISORY only — it reduces position size but never blocks trading.
        This prevents a stale bad-sample from permanently locking the engine.
        """
        _paper_speed = self._paper_speed_active()
        if self._state.halted and not _paper_speed:
            return False, f"HALTED: {self._state.halt_reason}"
        if self._state.halted and _paper_speed:
            logger.warning(
                f"[RISK-ENG] PAPER_SPEED bypass halt: {self._state.halt_reason}"
            )

        if (not _paper_speed) and self._state.trades_today >= MAX_TRADES_PER_DAY:
            return False, f"DAILY_TRADE_CAP({self._state.trades_today}/{MAX_TRADES_PER_DAY})"

        daily_loss_pct = self._daily_loss_pct()
        if daily_loss_pct >= MAX_DAILY_LOSS_PCT:
            return False, f"MAX_DAILY_LOSS({daily_loss_pct:.1%})"

        return True, ""

    def compute_risk_usdt(self, equity: float) -> float:
        """
        Returns the USDT amount to risk on the next trade, scaled by
        both the drawdown multiplier and the streak multiplier.
        Clamped to [RISK_PCT_MIN, RISK_PCT_MAX × 1.40] × equity.
        """
        combined = self._state.size_multiplier * self._state.streak_multiplier
        combined = max(MIN_STREAK_MULTIPLIER, min(MAX_STREAK_MULTIPLIER, combined))
        base     = equity * RISK_PCT_MAX
        adjusted = base * combined
        minimum  = equity * RISK_PCT_MIN
        return max(minimum, adjusted)

    def record_trade_result(self, net_pnl: float):
        """Call after every trade close with the net PnL (positive or negative)."""
        self._state.daily_pnl      += net_pnl
        self._state.trades_today   += 1
        self._state.current_equity += net_pnl
        if self._state.current_equity > self._state.peak_equity:
            self._state.peak_equity = self._state.current_equity
        # ── FTD-REF-023: streak-based size scaling ────────────────────────────
        self._update_streaks(net_pnl)

    def _update_streaks(self, net_pnl: float):
        """Adjust size_multiplier based on consecutive win / loss streaks."""
        if net_pnl > 0:
            self._state.win_streak  += 1
            self._state.loss_streak  = 0
        else:
            self._state.loss_streak += 1
            self._state.win_streak   = 0

        prev = self._state.streak_multiplier

        if self._state.win_streak >= WIN_STREAK_BOOST_AT:
            self._state.streak_multiplier = min(
                MAX_STREAK_MULTIPLIER,
                self._state.streak_multiplier * (1 + WIN_STREAK_BOOST_PCT),
            )
            if self._state.streak_multiplier != prev:
                logger.info(
                    f"[RISK-ENG] Win streak={self._state.win_streak} → "
                    f"size ×{self._state.streak_multiplier:.2f}"
                )
        elif self._state.loss_streak >= LOSS_STREAK_CUT_AT:
            self._state.streak_multiplier = max(
                MIN_STREAK_MULTIPLIER,
                self._state.streak_multiplier * (1 - LOSS_STREAK_CUT_PCT),
            )
            if self._state.streak_multiplier != prev:
                logger.warning(
                    f"[RISK-ENG] Loss streak={self._state.loss_streak} → "
                    f"size ×{self._state.streak_multiplier:.2f}"
                )

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
        combined = self._state.size_multiplier * self._state.streak_multiplier
        return {
            "halted":              self._state.halted,
            "halt_reason":         self._state.halt_reason,
            "trades_today":        self._state.trades_today,
            "daily_pnl":           round(self._state.daily_pnl, 4),
            "daily_loss_pct":      round(self._daily_loss_pct() * 100, 2),
            "drawdown_pct":        round(self._drawdown_pct() * 100, 2),
            "size_multiplier":     round(self._state.size_multiplier, 3),
            "streak_multiplier":   round(self._state.streak_multiplier, 3),
            "effective_multiplier":round(combined, 3),
            "win_streak":          self._state.win_streak,
            "loss_streak":         self._state.loss_streak,
            "peak_equity":         round(self._state.peak_equity, 4),
            "current_equity":   round(self._state.current_equity, 4),
            "risk_of_ruin":      round(self._state.risk_of_ruin, 4),
            "limits": {
                "max_daily_loss_pct": MAX_DAILY_LOSS_PCT * 100,
                "max_drawdown_pct":   MAX_DRAWDOWN_PCT * 100,
                "max_trades_per_day": ("UNLIMITED_PAPER_SPEED"
                                       if (cfg.TRADE_MODE == "PAPER" and cfg.PAPER_SPEED_MODE)
                                       else MAX_TRADES_PER_DAY),
                "risk_pct_range":     [RISK_PCT_MIN * 100, RISK_PCT_MAX * 100],
                "max_risk_of_ruin":  MAX_RISK_OF_RUIN,
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

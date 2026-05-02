"""
EOW Quant Engine — Capital Scaler
Implements Kelly Criterion + Fixed Fractional with streak-based adjustments.
Dynamically sizes positions up on winning streaks, down on drawdowns.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from loguru import logger
from config import cfg


@dataclass
class SizingDecision:
    symbol:           str
    usdt_risk:        float      # USDT amount at risk this trade
    qty:              float      # base asset qty
    position_pct:     float      # % of capital
    method:           str
    reason:           str
    current_equity:   float
    current_drawdown: float


class CapitalScaler:
    """
    Sizes each new position using:
    1. Kelly Criterion (conservative quarter-Kelly) based on recent win rate / avg R
    2. Streak modifier: scale up after win streak, scale down after loss streak
    3. Hard stop: reduce to minimum if drawdown exceeds threshold
    """

    MIN_RISK_PCT     = 0.005   # 0.5% floor (raised from 0.2% — at 55%+ WR this triples net $/trade)
    MAX_RISK_PCT     = 0.030   # 3.0% ceiling (raised from 2.5% — allows full Kelly at strong edge)
    MAX_NOTIONAL_PCT = 0.20    # 20% of equity max position notional (raised from 15%)

    def __init__(self):
        self._results: List[float] = []   # +ve win, -ve loss in USDT
        self._streak  = 0                 # +ve win streak, -ve loss streak
        self._equity  = cfg.INITIAL_CAPITAL
        self._peak    = cfg.INITIAL_CAPITAL

    # ── Update After Trade ──────────────────────────────────────────────────

    def record_trade(self, net_pnl: float):
        self._results.append(net_pnl)
        self._equity += net_pnl
        if self._equity > self._peak:
            self._peak = self._equity

        if net_pnl > 0:
            self._streak = max(0, self._streak) + 1
        else:
            self._streak = min(0, self._streak) - 1

    # ── Compute Position Size ───────────────────────────────────────────────

    def compute(
        self,
        symbol:      str,
        entry_price: float,
        stop_loss:   float,
    ) -> SizingDecision:
        equity    = self._equity
        drawdown  = (self._peak - equity) / self._peak if self._peak else 0

        # ── Emergency Halt ─────────────────────────────────────────────────
        if drawdown >= cfg.MAX_DRAWDOWN_HALT:
            if cfg.BYPASS_ALL_GATES:
                # Paper / dev mode: reset peak so we don't stay permanently halted
                self._peak = self._equity
                drawdown = 0.0
                logger.warning(
                    f"[SCALER] MDD bypass: peak reset to {self._equity:.2f} (BYPASS_ALL_GATES)"
                )
            else:
                logger.critical(f"[SCALER] ⛔ MDD {drawdown*100:.1f}% — ENGINE HALTED")
                return SizingDecision(
                    symbol=symbol, usdt_risk=0, qty=0,
                    position_pct=0, method="HALT",
                    reason=f"MDD {drawdown*100:.1f}% ≥ halt threshold",
                    current_equity=equity, current_drawdown=drawdown,
                )

        # ── Base Risk via Kelly ─────────────────────────────────────────────
        base_risk_pct = self._kelly_fraction()

        # ── Streak Adjustment ───────────────────────────────────────────────
        if self._streak >= cfg.WIN_STREAK_SCALE_UP:
            scale  = 1.0 + 0.25 * (self._streak - cfg.WIN_STREAK_SCALE_UP + 1)
            method = f"KELLY+STREAK_UP({self._streak})"
        elif self._streak <= -cfg.LOSS_STREAK_SCALE_DOWN:
            scale  = max(0.25, 1.0 - 0.30 * abs(self._streak - cfg.LOSS_STREAK_SCALE_DOWN + 1))
            method = f"KELLY+STREAK_DOWN({self._streak})"
        else:
            scale  = 1.0
            method = "KELLY"

        # ── Drawdown Scalar ─────────────────────────────────────────────────
        if drawdown > 0.05:
            dd_scale = max(0.3, 1.0 - drawdown * 3)
            base_risk_pct *= dd_scale
            method += f"+DD_REDUCE({drawdown*100:.1f}%)"

        adjusted_pct = min(self.MAX_RISK_PCT, max(self.MIN_RISK_PCT, base_risk_pct * scale))

        usdt_risk = equity * adjusted_pct
        sl_dist   = abs(entry_price - stop_loss)
        qty       = (usdt_risk / sl_dist) if sl_dist > 0 else 0.0

        # Hard notional cap: never risk more than MAX_NOTIONAL_PCT of equity in one position.
        # Prevents qty blow-up when sl_dist is tiny (low-priced assets, tight ATR).
        if entry_price > 0 and qty > 0:
            max_qty = equity * self.MAX_NOTIONAL_PCT / entry_price
            if qty > max_qty:
                logger.debug(
                    f"[SCALER] {symbol} notional cap: qty {qty:.6f}→{max_qty:.6f} "
                    f"(≤{self.MAX_NOTIONAL_PCT*100:.0f}% equity)"
                )
                qty = max_qty

        logger.debug(
            f"[SCALER] {symbol} | Equity={equity:.2f} DD={drawdown*100:.1f}% "
            f"Risk={adjusted_pct*100:.2f}% USDT={usdt_risk:.2f} Qty={qty:.6f}"
        )

        return SizingDecision(
            symbol=symbol,
            usdt_risk=round(usdt_risk, 4),
            qty=round(qty, 6),
            position_pct=round(adjusted_pct * 100, 3),
            method=method,
            reason=f"streak={self._streak} dd={drawdown*100:.1f}%",
            current_equity=round(equity, 4),
            current_drawdown=round(drawdown * 100, 2),
        )

    # ── Kelly Fraction ──────────────────────────────────────────────────────

    def _kelly_fraction(self) -> float:
        recent = self._results[-50:]   # last 50 trades for stats
        if len(recent) < 5:
            return self.MAX_RISK_PCT * 0.5   # conservative cold-start

        wins   = [r for r in recent if r > 0]
        losses = [r for r in recent if r <= 0]
        if not losses:
            return self.MAX_RISK_PCT

        win_rate = len(wins) / len(recent)
        avg_win  = sum(wins) / len(wins) if wins else 0
        avg_loss = abs(sum(losses) / len(losses))

        # Kelly: f* = (p * b - q) / b   where b = avg_win/avg_loss, q = 1-p
        b = avg_win / avg_loss if avg_loss else 1
        kelly = (win_rate * b - (1 - win_rate)) / b if b else 0

        # Quarter-Kelly conservative
        return max(self.MIN_RISK_PCT, min(self.MAX_RISK_PCT, kelly * cfg.KELLY_FRACTION))

    # ── State ───────────────────────────────────────────────────────────────

    @property
    def equity(self) -> float:
        return self._equity

    @property
    def drawdown_pct(self) -> float:
        return ((self._peak - self._equity) / self._peak * 100) if self._peak else 0

    @property
    def streak(self) -> int:
        return self._streak

    def set_equity(self, value: float):
        """Sync from broker balance."""
        self._equity = value
        if value > self._peak:
            self._peak = value

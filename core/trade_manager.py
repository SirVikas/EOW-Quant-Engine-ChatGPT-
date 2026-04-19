"""
EOW Quant Engine — Phase 4: Trade Manager (Profit Protection)
Maximizes winners and minimizes losers through dynamic SL management.

Lifecycle actions:
  1. MOVE_BE    — move SL to break-even once position reaches 1R profit
  2. TRAIL_SL   — trail SL using ATR after break-even is set
  3. PARTIAL_TP — book 50% of qty at 1.5R profit to lock in gains
  4. HOLD       — no action needed this tick

Integration: call trade_manager.register() when a position opens,
trade_manager.update() on every price tick, and trade_manager.deregister()
when the position closes.  Apply returned ManagementAction to risk_ctrl.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from loguru import logger

from config import cfg


@dataclass
class ManagedPosition:
    symbol:         str
    side:           str     # "LONG" | "SHORT"
    entry_price:    float
    stop_loss:      float   # initial SL (updated as manager moves it)
    take_profit:    float
    initial_risk:   float   # |entry - stop_loss| in price terms
    qty:            float
    breakeven_set:  bool  = False
    partial_booked: bool  = False
    peak_price:     float = 0.0
    current_sl:     float = 0.0


@dataclass
class ManagementAction:
    action:      str    # "MOVE_BE" | "TRAIL_SL" | "PARTIAL_TP" | "HOLD" | "NONE"
    new_sl:      float = 0.0
    partial_qty: float = 0.0
    reason:      str   = ""


class TradeManager:
    """
    Manages open position lifecycles to protect capital and compound gains.
    Works alongside RiskController — provides SL updates and partial TP signals.
    """

    def __init__(self):
        self._positions: Dict[str, ManagedPosition] = {}
        self.be_r            = 1.0                        # move to breakeven at 1R
        self.partial_tp_r    = cfg.PARTIAL_TP_R           # partial exit at 1.5R
        self.trail_atr_mult  = cfg.ATR_MULT_SL * 0.7     # tighter trail after BE
        self.be_epsilon      = cfg.BREAKEVEN_EPSILON_USDT
        logger.info(
            f"[TRADE-MANAGER] Phase 4 activated | "
            f"be_r={self.be_r} partial_r={self.partial_tp_r} "
            f"trail_mult={self.trail_atr_mult:.2f}"
        )

    # ── Position lifecycle ────────────────────────────────────────────────────

    def register(self, pos: ManagedPosition):
        """Register a new position for lifecycle management."""
        pos.peak_price = pos.entry_price
        pos.current_sl = pos.stop_loss
        self._positions[pos.symbol] = pos
        logger.debug(
            f"[TRADE-MANAGER] Registered {pos.symbol} {pos.side} "
            f"entry={pos.entry_price:.4f} risk={pos.initial_risk:.4f}"
        )

    def deregister(self, symbol: str):
        """Remove position on close (called from main on_tick close handler)."""
        if symbol in self._positions:
            del self._positions[symbol]

    # ── Per-tick update ───────────────────────────────────────────────────────

    def update(self, symbol: str, current_price: float, atr: float) -> ManagementAction:
        """
        Called on every price tick for managed positions.
        Priority: MOVE_BE → PARTIAL_TP → TRAIL_SL → HOLD
        Returns a ManagementAction describing what (if anything) to do.
        """
        pos = self._positions.get(symbol)
        if not pos:
            return ManagementAction(action="NONE")

        if pos.initial_risk <= 0:
            return ManagementAction(action="HOLD")

        # Current P&L in R-multiples
        if pos.side == "LONG":
            r_mult = (current_price - pos.entry_price) / pos.initial_risk
            pos.peak_price = max(pos.peak_price, current_price)
        else:
            r_mult = (pos.entry_price - current_price) / pos.initial_risk
            if pos.peak_price == 0.0:
                pos.peak_price = pos.entry_price
            pos.peak_price = min(pos.peak_price, current_price)

        # 1. Move SL to break-even at 1R (one-time)
        if not pos.breakeven_set and r_mult >= self.be_r:
            be_price = (pos.entry_price + self.be_epsilon
                        if pos.side == "LONG"
                        else pos.entry_price - self.be_epsilon)
            if ((pos.side == "LONG"  and be_price > pos.current_sl) or
                    (pos.side == "SHORT" and be_price < pos.current_sl)):
                pos.current_sl    = be_price
                pos.breakeven_set = True
                action = ManagementAction(
                    action="MOVE_BE", new_sl=be_price,
                    reason=f"R={r_mult:.2f}≥{self.be_r} → SL→BE±{self.be_epsilon}",
                )
                logger.info(f"[TRADE-MANAGER] {symbol} BE set @ {be_price:.4f}")
                return action

        # 2. Partial TP at 1.5R (one-time)
        if not pos.partial_booked and r_mult >= self.partial_tp_r:
            partial_qty = round(pos.qty * 0.50, 8)
            pos.partial_booked = True
            action = ManagementAction(
                action="PARTIAL_TP", partial_qty=partial_qty,
                reason=f"R={r_mult:.2f}≥{self.partial_tp_r} → partial TP 50%",
            )
            logger.info(
                f"[TRADE-MANAGER] {symbol} partial TP {partial_qty:.6f} "
                f"@ {current_price:.4f} (R={r_mult:.2f})"
            )
            return action

        # 3. Trail SL after break-even is armed
        if pos.breakeven_set and atr > 0:
            trail_dist = atr * self.trail_atr_mult
            if pos.side == "LONG":
                candidate = pos.peak_price - trail_dist
                if candidate > pos.current_sl:
                    pos.current_sl = candidate
                    return ManagementAction(
                        action="TRAIL_SL", new_sl=candidate,
                        reason=f"peak={pos.peak_price:.4f} trail_dist={trail_dist:.4f}",
                    )
            else:
                candidate = pos.peak_price + trail_dist
                if candidate < pos.current_sl:
                    pos.current_sl = candidate
                    return ManagementAction(
                        action="TRAIL_SL", new_sl=candidate,
                        reason=f"peak={pos.peak_price:.4f} trail_dist={trail_dist:.4f}",
                    )

        return ManagementAction(action="HOLD")

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_current_sl(self, symbol: str) -> Optional[float]:
        pos = self._positions.get(symbol)
        return pos.current_sl if pos else None

    def is_managed(self, symbol: str) -> bool:
        return symbol in self._positions

    def summary(self) -> dict:
        return {
            "managed_count":  len(self._positions),
            "managed_symbols": list(self._positions.keys()),
            "be_r":           self.be_r,
            "partial_tp_r":   self.partial_tp_r,
            "trail_atr_mult": self.trail_atr_mult,
            "module":         "TRADE_MANAGER",
            "phase":          4,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
trade_manager = TradeManager()

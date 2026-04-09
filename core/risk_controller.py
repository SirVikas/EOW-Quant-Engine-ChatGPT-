"""
EOW Quant Engine — Autonomous Risk Controller  (Step 5)
Monitors all open positions and enforces stop-losses, trailing stops,
and portfolio-level drawdown halts.
"""
from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from loguru import logger

from config import cfg
from core.pnl_calculator import PurePnLCalculator, TradeRecord
from utils.capital_scaler import CapitalScaler


@dataclass
class OpenPosition:
    position_id:  str
    symbol:       str
    side:         str            # "LONG" | "SHORT"
    entry_price:  float
    qty:          float
    stop_loss:    float
    take_profit:  float
    entry_ts:     int
    strategy_id:  str
    trailing_sl:  bool  = True
    peak_price:   float = 0.0    # used for trailing stop
    initial_risk: float = 0.0    # USDT at risk at entry
    regime:       str   = "UNKNOWN"  # market regime at entry


@dataclass
class RiskEvent:
    event_id:   str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    ts:         int = field(default_factory=lambda: int(time.time() * 1000))
    event_type: str = "INFO"     # INFO | WARNING | HALT | CLOSE_POSITION
    symbol:     str = ""
    detail:     str = ""


class RiskController:
    """
    Step 5: Autonomous Risk Controller.
    • Monitors open positions tick-by-tick.
    • Enforces hard SL / TP.
    • Implements trailing stop-loss (ATR-based).
    • Portfolio MDD halt — pauses new signal generation when breached.
    • Reports risk events to a bounded log.
    """

    def __init__(self, pnl_calc: PurePnLCalculator, scaler: CapitalScaler):
        self.pnl_calc   = pnl_calc
        self.scaler     = scaler
        self.positions: Dict[str, OpenPosition] = {}
        self.events:    List[RiskEvent]         = []
        self.halted:    bool                    = False
        self._running   = False

    # ── Position Lifecycle ──────────────────────────────────────────────────

    def open_position(self, pos: OpenPosition) -> bool:
        if self.halted:
            self._emit("WARNING", pos.symbol, "Engine halted — position rejected.")
            return False
        if pos.symbol in self.positions:
            self._emit("WARNING", pos.symbol, "Duplicate position attempt — rejected.")
            return False
        pos.peak_price = pos.entry_price
        self.positions[pos.symbol] = pos
        self._emit("INFO", pos.symbol,
                   f"OPEN {pos.side} @ {pos.entry_price} SL={pos.stop_loss} TP={pos.take_profit}")
        return True

    def on_price_update(self, symbol: str, price: float) -> Optional[str]:
        """
        Call this on every tick for a symbol.
        Returns action string if position should be closed: "SL" | "TP" | None.
        """
        pos = self.positions.get(symbol)
        if not pos:
            return None

        action = None

        if pos.side == "LONG":
            # Trailing stop update
            if pos.trailing_sl and price > pos.peak_price:
                pos.peak_price = price
                # Trail SL up: maintain same distance from peak
                trail_dist     = pos.entry_price - pos.stop_loss
                new_sl         = pos.peak_price - trail_dist
                if new_sl > pos.stop_loss:
                    pos.stop_loss = new_sl

            if price <= pos.stop_loss:
                action = "SL"
            elif price >= pos.take_profit:
                action = "TP"

        else:  # SHORT
            if pos.trailing_sl and price < pos.peak_price:
                pos.peak_price = price
                trail_dist     = pos.stop_loss - pos.entry_price
                new_sl         = pos.peak_price + trail_dist
                if new_sl < pos.stop_loss:
                    pos.stop_loss = new_sl

            if price >= pos.stop_loss:
                action = "SL"
            elif price <= pos.take_profit:
                action = "TP"

        if action:
            self._close_position(symbol, price, action)

        # Portfolio MDD check
        self._check_mdd_halt()
        return action

    def _close_position(self, symbol: str, exit_price: float, reason: str):
        pos = self.positions.pop(symbol, None)
        if not pos:
            return

        record = TradeRecord(
            trade_id=pos.position_id,
            symbol=pos.symbol,
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            qty=pos.qty,
            entry_ts=pos.entry_ts,
            exit_ts=int(time.time() * 1000),
            is_short=(pos.side == "SHORT"),
            strategy_id=pos.strategy_id,
            regime=pos.regime,
            mode=cfg.TRADE_MODE,
        )
        result = self.pnl_calc.calculate(record, initial_risk_usdt=pos.initial_risk)
        self.scaler.record_trade(result.net_pnl)

        self._emit(
            "INFO", symbol,
            f"CLOSE {reason} @ {exit_price} | Net={result.net_pnl:+.4f} USDT"
        )

    # ── MDD Halt ────────────────────────────────────────────────────────────

    def _check_mdd_halt(self):
        dd = self.scaler.drawdown_pct / 100
        if dd >= cfg.MAX_DRAWDOWN_HALT and not self.halted:
            self.halted = True
            self._emit("HALT", "PORTFOLIO",
                       f"MDD {dd*100:.1f}% breached — engine halted. No new trades.")
            logger.critical("[RISK] 🛑 ENGINE HALTED — max drawdown reached.")
        elif dd < cfg.MAX_DRAWDOWN_HALT * 0.8 and self.halted:
            self.halted = False
            self._emit("INFO", "PORTFOLIO", "Engine resumed — drawdown recovered.")
            logger.info("[RISK] ✅ Engine resumed.")

    # ── Force Close All ─────────────────────────────────────────────────────

    def emergency_close_all(self, prices: Dict[str, float]):
        symbols = list(self.positions.keys())
        for sym in symbols:
            price = prices.get(sym, self.positions[sym].entry_price)
            self._close_position(sym, price, "EMERGENCY")
        self._emit("HALT", "PORTFOLIO", "Emergency close — all positions liquidated.")

    # ── Event Log ───────────────────────────────────────────────────────────

    def _emit(self, event_type: str, symbol: str, detail: str):
        ev = RiskEvent(event_type=event_type, symbol=symbol, detail=detail)
        self.events.append(ev)
        self.events = self.events[-200:]   # bounded
        logger.info(f"[RISK] [{event_type}] {symbol}: {detail}")

    # ── State Snapshot ──────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            "halted":        self.halted,
            "open_positions": [asdict(p) for p in self.positions.values()],
            "drawdown_pct":  round(self.scaler.drawdown_pct, 2),
            "equity":        round(self.scaler.equity, 4),
            "streak":        self.scaler.streak,
            "recent_events": [asdict(e) for e in self.events[-20:]],
        }

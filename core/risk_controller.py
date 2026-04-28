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
class PendingLimitOrder:
    """A limit order waiting to be filled on the next tick(s)."""
    order_id:    str
    symbol:      str
    side:        str           # "LONG" | "SHORT"
    limit_price: float         # price at which we want to fill
    qty:         float
    stop_loss:   float
    take_profit: float
    strategy_id: str
    initial_risk: float
    regime:      str
    created_ts:  int
    ticks_open:  int = 0       # how many ticks this order has been waiting


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
    initial_stop_loss: float = 0.0  # immutable entry SL (for R-multiple tracking)
    regime:       str   = "UNKNOWN"  # market regime at entry
    order_type:   str   = "MARKET"   # "MARKET" | "LIMIT" — passed to PnL calc
    breakeven_armed: bool = False
    peak_r:       float = 0.0
    ticks_since_peak: int = 0


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
        self.pnl_calc        = pnl_calc
        self.scaler          = scaler
        self.positions:      Dict[str, OpenPosition]     = {}
        self.pending_orders: Dict[str, PendingLimitOrder] = {}
        self.events:         List[RiskEvent]             = []
        self.halted:         bool                        = False
        self.graceful_stop:  bool                        = False  # blocks new entries, lets positions run
        self._running        = False

    # ── Position Lifecycle ──────────────────────────────────────────────────

    def open_position(self, pos: OpenPosition, order_type: str = "MARKET") -> bool:
        if self.halted:
            self._emit("WARNING", pos.symbol, "Engine halted — position rejected.")
            return False
        if pos.symbol in self.positions:
            self._emit("WARNING", pos.symbol, "Duplicate position attempt — rejected.")
            return False
        pos.peak_price  = pos.entry_price
        if pos.initial_stop_loss == 0.0:
            pos.initial_stop_loss = pos.stop_loss
        pos.order_type  = order_type   # stored for PnL calc downstream
        self.positions[pos.symbol] = pos
        self._emit("INFO", pos.symbol,
                   f"OPEN {pos.side} [{order_type}] @ {pos.entry_price} "
                   f"SL={pos.stop_loss} TP={pos.take_profit}")
        return True

    def calculate_dynamic_edge(self, base_r: float, current_volatility: float) -> float:
        """
        Dynamic min-R threshold:
        Required_R = Base_R + Volatility_Premium
        where premium increases when ATR% rises above baseline.
        """
        baseline = max(cfg.VOL_BASELINE_ATR_PCT, 1e-6)
        volatility_premium = max(0.0, (current_volatility - baseline) / baseline) * cfg.VOL_PREMIUM_MULT
        return base_r + volatility_premium

    def _dry_spell_r_relaxation(self, minutes_no_trade: float) -> float:
        """
        Return temporary required_r relaxation during trade dry spells.
        Mirrors activator tiers but keeps a hard floor via cfg.RISK_R_FLOOR.
        """
        if minutes_no_trade >= cfg.ACTIVATOR_T3_MIN:
            return cfg.RISK_R_RELAX_T3
        if minutes_no_trade >= cfg.ACTIVATOR_T2_MIN:
            return cfg.RISK_R_RELAX_T2
        if minutes_no_trade >= cfg.ACTIVATOR_T1_MIN:
            return cfg.RISK_R_RELAX_T1
        return 0.0

    # Regime → base minimum-R lookup (Fix B)
    # Mean-reversion compensates lower R with higher win-rate; accept a tighter bar.
    _REGIME_BASE_R = {
        "TRENDING":             None,   # resolved from cfg at call time
        "MEAN_REVERTING":       None,
        "VOLATILITY_EXPANSION": None,
    }

    def _regime_base_r(self, regime: str) -> float:
        """Return the per-regime base minimum R, falling back to cfg.BASE_MIN_R."""
        return {
            "TRENDING":             cfg.REGIME_MIN_R_TRENDING,
            "MEAN_REVERTING":       cfg.REGIME_MIN_R_MEAN_REVERTING,
            "VOLATILITY_EXPANSION": cfg.REGIME_MIN_R_VOLATILE,
        }.get(regime, cfg.BASE_MIN_R)

    def get_trade_decision(
        self,
        *,
        side: str,
        entry: float,
        take_profit: float,
        stop_loss: float,
        qty: float,
        current_volatility: float,
        regime: str = "UNKNOWN",   # Fix B: receive live regime from on_tick
        minutes_no_trade: float = 0.0,
    ) -> tuple[bool, dict]:
        """
        Evaluate whether a trade has enough post-cost edge to justify entry.
        Uses conservative taker fees + slippage + ATR-based slippage premium.

        required_r behavior:
          1) Start with regime-aware base + volatility premium.
          2) During dry spells, apply tiered relaxation based on minutes_no_trade.
          3) Never go below cfg.RISK_R_FLOOR (hard protection).
        """
        if qty <= 0:
            return False, {"reason": "invalid_qty"}

        notional_entry = entry * qty
        notional_exit_tp = take_profit * qty
        gross_tp = abs(take_profit - entry) * qty
        risk_usdt = abs(entry - stop_loss) * qty
        rr = (gross_tp / risk_usdt) if risk_usdt > 0 else 0.0

        # Worst-case fill realism for entry filtering.
        fee_cost = (notional_entry + notional_exit_tp) * cfg.TAKER_FEE
        base_slippage_cost = (notional_entry + notional_exit_tp) * cfg.SLIPPAGE_EST
        atr_slippage_cost = current_volatility / 100.0 * cfg.ATR_SLIPPAGE_MULT * (entry * qty)
        total_cost = fee_cost + base_slippage_cost + atr_slippage_cost

        net_if_tp = gross_tp - total_cost
        rr_after_cost = (net_if_tp / risk_usdt) if risk_usdt > 0 else 0.0
        base_r = self._regime_base_r(regime)
        required_r_raw = self.calculate_dynamic_edge(base_r, current_volatility)
        r_relax = self._dry_spell_r_relaxation(minutes_no_trade)
        required_r = max(cfg.RISK_R_FLOOR, required_r_raw - r_relax)
        ok = (net_if_tp > 0) and (rr_after_cost >= required_r)

        return ok, {
            "side": side,
            "regime": regime,
            "gross_tp": gross_tp,
            "cost": total_cost,
            "fee_cost": fee_cost,
            "slippage_cost": base_slippage_cost + atr_slippage_cost,
            "net_if_tp": net_if_tp,
            "rr": rr,
            "rr_after_cost": rr_after_cost,
            "required_r": required_r,
            "required_r_raw": required_r_raw,
            "required_r_relax": r_relax,
            "base_r_used": base_r,
            "current_volatility": current_volatility,
            "minutes_no_trade": minutes_no_trade,
        }

    def submit_limit_order(
        self,
        symbol: str,
        side: str,
        limit_price: float,
        qty: float,
        stop_loss: float,
        take_profit: float,
        strategy_id: str,
        initial_risk: float,
        regime: str,
    ) -> bool:
        """
        Queue a limit order.  It will fill (or chase) on the next tick(s).
        Returns False if the engine is halted or a position/order already exists.
        """
        if self.halted:
            self._emit("WARNING", symbol, "Engine halted — limit order rejected.")
            return False
        if symbol in self.positions or symbol in self.pending_orders:
            return False
        order = PendingLimitOrder(
            order_id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            limit_price=limit_price,
            qty=qty,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_id=strategy_id,
            initial_risk=initial_risk,
            regime=regime,
            created_ts=int(time.time() * 1000),
        )
        self.pending_orders[symbol] = order
        offset_bps = cfg.LIMIT_ENTRY_OFFSET_BPS / 10_000
        self._emit(
            "INFO", symbol,
            f"LIMIT ORDER {side} qty={qty:.6f} @ {limit_price:.4f} "
            f"(offset={cfg.LIMIT_ENTRY_OFFSET_BPS:.1f}bps | "
            f"chase after {cfg.PRICE_CHASE_TICKS} ticks)"
        )
        return True

    def on_price_update(self, symbol: str, price: float) -> Optional[str]:
        """
        Call this on every tick for a symbol.
        1. Check pending limit orders: fill if price reached, else price-chase.
        2. Check open positions: trailing SL / TP.
        Returns action string if position was closed: "SL" | "TP" | None.
        """
        # ── Limit order fill / price-chase ──────────────────────────────────
        pending = self.pending_orders.get(symbol)
        if pending:
            pending.ticks_open += 1
            filled = False
            if pending.side == "LONG" and price <= pending.limit_price:
                filled = True
            elif pending.side == "SHORT" and price >= pending.limit_price:
                filled = True

            if filled:
                pos = OpenPosition(
                    position_id=pending.order_id,
                    symbol=pending.symbol,
                    side=pending.side,
                    entry_price=pending.limit_price,   # filled at our price
                    qty=pending.qty,
                    stop_loss=pending.stop_loss,
                    take_profit=pending.take_profit,
                    entry_ts=pending.created_ts,
                    strategy_id=pending.strategy_id,
                    initial_risk=pending.initial_risk,
                    regime=pending.regime,
                )
                del self.pending_orders[symbol]
                self.open_position(pos, order_type="LIMIT")
            elif pending.ticks_open >= cfg.PRICE_CHASE_TICKS:
                # Price hasn't come to us — chase: move limit to current market
                old_lp = pending.limit_price
                pending.limit_price = price
                pending.ticks_open  = 0
                self._emit(
                    "INFO", symbol,
                    f"PRICE CHASE {pending.side}: limit {old_lp:.4f} → {price:.4f} (market)"
                )
                # On next tick this will fill as market order (slippage applies)

        pos = self.positions.get(symbol)
        if not pos:
            return None

        action = None

        if pos.side == "LONG":
            # Trailing stop update
            if pos.trailing_sl and price > pos.peak_price:
                pos.peak_price = price
                pos.ticks_since_peak = 0
                # Trail SL up: maintain same distance from peak
                trail_dist     = pos.entry_price - pos.stop_loss
                new_sl         = pos.peak_price - trail_dist
                if new_sl > pos.stop_loss:
                    pos.stop_loss = new_sl
            else:
                pos.ticks_since_peak += 1

            # Peak profit tracking in R and BE jump
            entry_risk = max(pos.entry_price - pos.initial_stop_loss, 1e-9)
            pos.peak_r = max(pos.peak_r, (pos.peak_price - pos.entry_price) / entry_risk)
            if (not pos.breakeven_armed) and pos.peak_r >= cfg.BREAKEVEN_TRIGGER_R:
                cost_per_unit = pos.entry_price * (2 * cfg.TAKER_FEE + 2 * cfg.SLIPPAGE_EST)
                be_sl = pos.entry_price + cost_per_unit
                if be_sl > pos.stop_loss:
                    pos.stop_loss = be_sl
                pos.breakeven_armed = True

            if pos.peak_r >= cfg.SPEED_EXIT_TRIGGER_R and pos.ticks_since_peak >= cfg.SPEED_EXIT_STALL_TICKS:
                action = "SPEED"

            if price <= pos.stop_loss:
                action = "SL"
            elif price >= pos.take_profit:
                action = "TP"

        else:  # SHORT
            if pos.trailing_sl and price < pos.peak_price:
                pos.peak_price = price
                pos.ticks_since_peak = 0
                trail_dist     = pos.stop_loss - pos.entry_price
                new_sl         = pos.peak_price + trail_dist
                if new_sl < pos.stop_loss:
                    pos.stop_loss = new_sl
            else:
                pos.ticks_since_peak += 1

            entry_risk = max(pos.initial_stop_loss - pos.entry_price, 1e-9)
            pos.peak_r = max(pos.peak_r, (pos.entry_price - pos.peak_price) / entry_risk)
            if (not pos.breakeven_armed) and pos.peak_r >= cfg.BREAKEVEN_TRIGGER_R:
                cost_per_unit = pos.entry_price * (2 * cfg.TAKER_FEE + 2 * cfg.SLIPPAGE_EST)
                be_sl = pos.entry_price - cost_per_unit
                if be_sl < pos.stop_loss:
                    pos.stop_loss = be_sl
                pos.breakeven_armed = True

            if pos.peak_r >= cfg.SPEED_EXIT_TRIGGER_R and pos.ticks_since_peak >= cfg.SPEED_EXIT_STALL_TICKS:
                action = "SPEED"

            if price >= pos.stop_loss:
                action = "SL"
            elif price <= pos.take_profit:
                action = "TP"

        if action:
            action = self._close_position(symbol, price, action)

        # Portfolio MDD check
        self._check_mdd_halt()
        return action

    def _close_position(self, symbol: str, exit_price: float, reason: str) -> str:
        pos = self.positions.pop(symbol, None)
        if not pos:
            return reason

        order_type = getattr(pos, "order_type", "MARKET")
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
            order_type=order_type,
            stop_loss=pos.initial_stop_loss,   # FTD-REF-055: preserve initial SL
            take_profit=pos.take_profit,        # FTD-REF-055: preserve TP
        )
        result = self.pnl_calc.calculate(record, initial_risk_usdt=pos.initial_risk)
        self.scaler.record_trade(result.net_pnl)

        close_tag = reason
        if reason in ("SL", "SPEED"):
            if abs(result.net_pnl) <= cfg.BREAKEVEN_EPSILON_USDT:
                close_tag = "BE"
            elif result.net_pnl > 0:
                close_tag = "TSL+"
            else:
                close_tag = "SL"

        self._emit(
            "INFO", symbol,
            f"CLOSE {close_tag} [{order_type}] @ {exit_price} | "
            f"Net={result.net_pnl:+.4f} USDT | "
            f"Slip={result.slippage_cost:.4f} Fee={result.fee_entry+result.fee_exit:.4f}"
        )
        return close_tag

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
            "halted":          self.halted,
            "graceful_stop":   self.graceful_stop,
            "open_positions":  [asdict(p) for p in self.positions.values()],
            "pending_orders":  len(self.pending_orders),
            "drawdown_pct":    round(self.scaler.drawdown_pct, 2),
            "equity":          round(self.scaler.equity, 4),
            "streak":          self.scaler.streak,
            "recent_events":   [asdict(e) for e in self.events[-20:]],
        }

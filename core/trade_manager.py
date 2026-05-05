"""
EOW Quant Engine — Trade Manager (Adaptive Profit Protection)
Maximizes winners and minimizes losers through dynamic SL/TP management.

Lifecycle actions:
  1. FAST_FAIL   — exit within 5 min if r_mult < -0.45 (trend reversed at entry)
  2. TIME_EXIT   — exit stalling trades after 8 min with < 0.15R progress
  3. MOVE_BE     — move SL to break-even at BREAKEVEN_TRIGGER_R profit
  4. PARTIAL_TP  — book 50% of qty at PARTIAL_TP_R
  5. TRAIL_SL    — ATR-based trailing after break-even is set
  6. EXTEND_TP   — VTP: push TP further when price velocity is accelerating
  7. VTP_EXIT    — VTP: market-exit when velocity stalls after partial booking
  8. HOLD        — no action needed this tick

Mode-aware logic:
  TREND_FOLLOW  — standard thresholds (BE at 1.0R, full trail)
  RANGE_SCALP   — tighter BE (0.5R), faster stall exit (range TP is smaller)
  SHORT_HUNT    — same as TREND_FOLLOW with extra fast-fail sensitivity

Integration: call trade_manager.register() when a position opens,
trade_manager.update() on every price tick, and trade_manager.deregister()
when the position closes.  Apply returned ManagementAction to risk_ctrl.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from config import cfg


@dataclass
class ManagedPosition:
    symbol:         str
    side:           str     # "LONG" | "SHORT"
    entry_price:    float
    stop_loss:      float   # initial SL (updated as manager moves it)
    take_profit:    float   # updated by VTP
    initial_risk:   float   # |entry - stop_loss| in price terms
    qty:            float
    exec_mode:      str   = "TREND_FOLLOW"   # ExecMode from adaptive_mode_engine
    breakeven_set:  bool  = False
    partial_booked: bool  = False
    vtp_extended:   bool  = False            # True once EXTEND_TP has fired
    peak_price:     float = 0.0
    current_sl:     float = 0.0
    open_ts:        float = 0.0
    # VTP: rolling R-multiple history for velocity computation (last 5 ticks)
    r_history:      List[float] = field(default_factory=list)


# FTD-037: Time-based exit thresholds
_TIME_EXIT_SECONDS = 8 * 60    # tightened 12→8 min: exit stalling trades faster, reducing fee drag
_TIME_EXIT_MIN_R   = 0.15      # tightened 0.20→0.15R: earlier exit when momentum fails to develop

# FTD-LOSS: Early trend-failure fast exit — fires when trending signal reverses immediately
_FAST_FAIL_R       = -0.45     # if r_mult drops below -45% of risk within first 5 min, bail out
_FAST_FAIL_SECONDS = 5 * 60    # 5-minute window for fast-fail check

# VTP: Volatile Take-Profit thresholds
_VTP_HISTORY_LEN     = 5       # R-multiple ticks to maintain for velocity calc
_VTP_ACCEL_THRESHOLD = 0.15    # R gained per tick needed to trigger TP extension
_VTP_EXTEND_ATR_MULT = 2.0     # push TP by this many additional ATR units
_VTP_STALL_THRESHOLD = 0.0     # R velocity ≤ 0 after partial booking → potential exit
_VTP_STALL_PATIENCE  = 3       # ticks of zero/negative velocity before VTP_EXIT fires

# RANGE_SCALP mode: tighter breakeven because TP target is much smaller
_RANGE_BE_R          = 0.50    # move to BE at 0.5R in range mode (vs 1.0R in trend)


@dataclass
class ManagementAction:
    action:      str    # see lifecycle action list in module docstring
    new_sl:      float = 0.0
    new_tp:      float = 0.0   # set by EXTEND_TP
    partial_qty: float = 0.0
    reason:      str   = ""


class TradeManager:
    """
    Manages open position lifecycles to protect capital and compound gains.
    Seamlessly switches behavior between TREND_FOLLOW and RANGE_SCALP without
    session restarts — mode is stored per-position at registration time and
    can be updated via set_mode().
    """

    def __init__(self):
        self._positions: Dict[str, ManagedPosition] = {}
        self.be_r           = cfg.BREAKEVEN_TRIGGER_R
        self.partial_tp_r   = cfg.PARTIAL_TP_R
        self.trail_atr_mult = cfg.ATR_MULT_SL * 0.7
        self.be_epsilon     = cfg.BREAKEVEN_EPSILON_USDT
        logger.info(
            f"[TRADE-MANAGER] Adaptive activated | "
            f"be_r={self.be_r} range_be_r={_RANGE_BE_R} "
            f"partial_r={self.partial_tp_r} trail_mult={self.trail_atr_mult:.2f} "
            f"vtp_accel={_VTP_ACCEL_THRESHOLD} vtp_extend={_VTP_EXTEND_ATR_MULT}×ATR"
        )

    # ── Position lifecycle ────────────────────────────────────────────────────

    def register(self, pos: ManagedPosition):
        """Register a new position. exec_mode should be set before calling."""
        pos.peak_price = pos.entry_price
        pos.current_sl = pos.stop_loss
        pos.open_ts    = time.time()
        pos.r_history  = []
        self._positions[pos.symbol] = pos
        logger.debug(
            f"[TRADE-MANAGER] Registered {pos.symbol} {pos.side} "
            f"mode={pos.exec_mode} entry={pos.entry_price:.4f} "
            f"risk={pos.initial_risk:.4f} tp={pos.take_profit:.4f}"
        )

    def deregister(self, symbol: str):
        """Remove position on close."""
        self._positions.pop(symbol, None)

    def set_mode(self, symbol: str, new_mode: str):
        """
        Update execution mode for an open position mid-trade.
        Enables seamless mode switching without closing and reopening positions.
        """
        pos = self._positions.get(symbol)
        if pos and pos.exec_mode != new_mode:
            logger.info(
                f"[TRADE-MANAGER] {symbol} mode switch "
                f"{pos.exec_mode} → {new_mode}"
            )
            pos.exec_mode = new_mode

    # ── Per-tick update ───────────────────────────────────────────────────────

    def update(self, symbol: str, current_price: float, atr: float) -> ManagementAction:
        """
        Called on every price tick for managed positions.
        Priority: FAST_FAIL → TIME_EXIT → MOVE_BE → PARTIAL_TP →
                  EXTEND_TP(VTP) → VTP_EXIT → TRAIL_SL → HOLD
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

        elapsed = time.time() - pos.open_ts if pos.open_ts > 0 else 0.0

        # ── FTD-LOSS: Fast-fail exit ──────────────────────────────────────────
        # Trend reversed immediately after entry — cap drawdown before full SL.
        if (not pos.breakeven_set
                and pos.open_ts > 0
                and elapsed < _FAST_FAIL_SECONDS
                and r_mult < _FAST_FAIL_R):
            logger.info(
                f"[TRADE-MANAGER] {symbol} FAST_FAIL at {elapsed/60:.1f}min "
                f"(r={r_mult:.3f})"
            )
            return ManagementAction(
                action="TIME_EXIT",
                reason=f"Fast-fail: {elapsed/60:.1f}min r={r_mult:.3f}<{_FAST_FAIL_R}",
            )

        # ── FTD-037: Stale-trade time exit ───────────────────────────────────
        # Only before breakeven — after BE the position is self-protecting.
        if (not pos.breakeven_set
                and pos.open_ts > 0
                and elapsed > _TIME_EXIT_SECONDS
                and r_mult < _TIME_EXIT_MIN_R):
            logger.info(
                f"[TRADE-MANAGER] {symbol} TIME_EXIT after {elapsed/60:.1f}min "
                f"(r={r_mult:.3f})"
            )
            return ManagementAction(
                action="TIME_EXIT",
                reason=f"Stale: {elapsed/60:.1f}min r={r_mult:.3f}<{_TIME_EXIT_MIN_R}",
            )

        # ── 1. Move SL to break-even ──────────────────────────────────────────
        # RANGE_SCALP uses a tighter BE trigger since TP is much smaller.
        be_trigger = _RANGE_BE_R if pos.exec_mode == "RANGE_SCALP" else self.be_r
        if not pos.breakeven_set and r_mult >= be_trigger:
            # Cover round-trip fees + slippage so the BE exit truly breaks even net.
            # Fixed epsilon ($0.05) was smaller than typical fees ($0.13-$0.23) causing
            # all 210 "BREAKEVEN" exits to log a small loss (avg -$0.07, total -$14.72).
            cost_per_unit = pos.entry_price * (2 * cfg.TAKER_FEE + 2 * cfg.SLIPPAGE_EST)
            be_price = (pos.entry_price + cost_per_unit
                        if pos.side == "LONG"
                        else pos.entry_price - cost_per_unit)
            if ((pos.side == "LONG"  and be_price > pos.current_sl) or
                    (pos.side == "SHORT" and be_price < pos.current_sl)):
                pos.current_sl    = be_price
                pos.breakeven_set = True
                logger.info(
                    f"[TRADE-MANAGER] {symbol} BE @ {be_price:.4f} "
                    f"(mode={pos.exec_mode} trigger={be_trigger}R)"
                )
                return ManagementAction(
                    action="MOVE_BE", new_sl=be_price,
                    reason=f"R={r_mult:.2f}≥{be_trigger} mode={pos.exec_mode} → SL→BE",
                )

        # ── 2. Partial TP ─────────────────────────────────────────────────────
        if not pos.partial_booked and r_mult >= self.partial_tp_r:
            partial_qty = round(pos.qty * 0.50, 8)
            pos.partial_booked = True
            logger.info(
                f"[TRADE-MANAGER] {symbol} PARTIAL_TP {partial_qty:.6f} "
                f"@ {current_price:.4f} (R={r_mult:.2f})"
            )
            return ManagementAction(
                action="PARTIAL_TP", partial_qty=partial_qty,
                reason=f"R={r_mult:.2f}≥{self.partial_tp_r} → 50% exit",
            )

        # ── VTP: Volatile Take-Profit logic ───────────────────────────────────
        # Only active in TREND_FOLLOW / SHORT_HUNT — range scalps use fixed TP.
        if pos.exec_mode != "RANGE_SCALP":
            pos.r_history.append(r_mult)
            if len(pos.r_history) > _VTP_HISTORY_LEN:
                pos.r_history.pop(0)

            if len(pos.r_history) >= 3:
                # Velocity = average R gained per tick over the history window
                r_velocity = (pos.r_history[-1] - pos.r_history[0]) / len(pos.r_history)

                # 3. EXTEND_TP: accelerating momentum → push TP further (once)
                if (not pos.vtp_extended
                        and r_velocity >= _VTP_ACCEL_THRESHOLD
                        and atr > 0
                        and r_mult > 0):
                    if pos.side == "LONG":
                        new_tp = pos.take_profit + atr * _VTP_EXTEND_ATR_MULT
                    else:
                        new_tp = pos.take_profit - atr * _VTP_EXTEND_ATR_MULT
                    pos.take_profit  = new_tp
                    pos.vtp_extended = True
                    logger.info(
                        f"[TRADE-MANAGER] {symbol} VTP EXTEND_TP → {new_tp:.4f} "
                        f"(velocity={r_velocity:.3f})"
                    )
                    return ManagementAction(
                        action="EXTEND_TP", new_tp=new_tp,
                        reason=(f"VTP: r_velocity={r_velocity:.3f}≥{_VTP_ACCEL_THRESHOLD} "
                                f"→ TP pushed +{_VTP_EXTEND_ATR_MULT}×ATR"),
                    )

                # 4. VTP_EXIT: velocity stalled after partial booking → exit at market
                if (pos.partial_booked
                        and r_velocity <= _VTP_STALL_THRESHOLD
                        and r_mult >= cfg.VTP_EXIT_MIN_R):
                    stall_count = sum(
                        1 for i in range(1, len(pos.r_history))
                        if pos.r_history[i] <= pos.r_history[i - 1]
                    )
                    if stall_count >= _VTP_STALL_PATIENCE:
                        logger.info(
                            f"[TRADE-MANAGER] {symbol} VTP_EXIT stall={stall_count} "
                            f"r={r_mult:.3f} velocity={r_velocity:.3f}"
                        )
                        return ManagementAction(
                            action="VTP_EXIT",
                            reason=(f"VTP stall: {stall_count} flat ticks "
                                    f"r={r_mult:.3f} velocity={r_velocity:.3f}"),
                        )

        # ── 5. Trail SL after break-even is armed ────────────────────────────
        if pos.breakeven_set and atr > 0:
            trail_dist = atr * self.trail_atr_mult
            if pos.side == "LONG":
                candidate = pos.peak_price - trail_dist
                if candidate > pos.current_sl:
                    pos.current_sl = candidate
                    return ManagementAction(
                        action="TRAIL_SL", new_sl=candidate,
                        reason=f"peak={pos.peak_price:.4f} dist={trail_dist:.4f}",
                    )
            else:
                candidate = pos.peak_price + trail_dist
                if candidate < pos.current_sl:
                    pos.current_sl = candidate
                    return ManagementAction(
                        action="TRAIL_SL", new_sl=candidate,
                        reason=f"peak={pos.peak_price:.4f} dist={trail_dist:.4f}",
                    )

        return ManagementAction(action="HOLD")

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_current_sl(self, symbol: str) -> Optional[float]:
        pos = self._positions.get(symbol)
        return pos.current_sl if pos else None

    def get_current_tp(self, symbol: str) -> Optional[float]:
        pos = self._positions.get(symbol)
        return pos.take_profit if pos else None

    def is_managed(self, symbol: str) -> bool:
        return symbol in self._positions

    def summary(self) -> dict:
        modes = {}
        for sym, pos in self._positions.items():
            modes[sym] = pos.exec_mode
        return {
            "managed_count":   len(self._positions),
            "managed_symbols": list(self._positions.keys()),
            "active_modes":    modes,
            "be_r":            self.be_r,
            "range_be_r":      _RANGE_BE_R,
            "partial_tp_r":    self.partial_tp_r,
            "trail_atr_mult":  self.trail_atr_mult,
            "vtp_accel":       _VTP_ACCEL_THRESHOLD,
            "vtp_extend_atr":  _VTP_EXTEND_ATR_MULT,
            "module":          "TRADE_MANAGER",
            "phase":           5,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
trade_manager = TradeManager()

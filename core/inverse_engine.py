"""
EOW Quant Engine — Adaptive Inverse Engine  (A.I.E.)

A strategy is a reliable contra-indicator only when it is *significantly and
consistently* wrong — not merely average.  A 44% win-rate with a 2:1 RR is
actually profitable (0.44×2 − 0.56×1 = +0.32R per trade).  Only flip when
the system is demonstrably worse than random and improving nothing.

Design principles (root-cause corrected):
  1. Default state is NORMAL — never block trading due to insufficient data.
  2. NO_TRADE zone is removed.  A 40–60% WR strategy should keep trading;
     the RR ratio is what determines profitability, not WR alone.
  3. INVERSE only activates when WR < INVERSE_THRESHOLD (≤ 35%) after
     MIN_SAMPLES (≥ 30) fresh trades from the current (fixed) system.
  4. Historical trades from broken sessions are NOT fed in at startup —
     old fake-ATR losses are not representative of the fixed engine.

Per-strategy mode state machine (minimum MIN_SAMPLES fresh trades required):
  NORMAL    default / WR ≥ INVERSE_THRESHOLD  → trade as generated
  INVERSE   WR < INVERSE_THRESHOLD (≤ 35%)    → flip direction + mirror SL/TP
  CALIBRATE consecutive losses ≥ EQUITY_PROTECT_LOSSES → global pause

Signal inversion preserves RR by mirroring SL/TP distances around entry:
  Original LONG  entry=P, sl=P−d, tp=P+D  →  SHORT  sl=P+d, tp=P−D  (RR=D/d ✓)
  Original SHORT entry=P, sl=P+d, tp=P−D  →  LONG   sl=P−d, tp=P+D  (RR=D/d ✓)
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from loguru import logger


# ── Thresholds ────────────────────────────────────────────────────────────────
INVERSE_THRESHOLD      = 0.35   # only invert when WR < 35% (≈ PF < 0.54 at 1:1 RR)
MIN_SAMPLES            = 20     # mandate: 20 fresh trades before inversion can activate
ROLLING_WINDOW         = 50     # rolling window for win-rate calculation
EQUITY_PROTECT_LOSSES  = 6      # consecutive losses → global CALIBRATE pause
CALIBRATE_PAUSE_MIN    = 20     # minutes to pause before resuming NORMAL


class TradeMode(str, Enum):
    NORMAL    = "NORMAL"
    INVERSE   = "INVERSE"
    CALIBRATE = "CALIBRATE"


@dataclass
class InverseDecision:
    mode:            TradeMode
    original_signal: str          # "LONG" or "SHORT"
    final_signal:    str          # possibly flipped
    entry_price:     float
    stop_loss:       float
    take_profit:     float
    reason:          str
    inverted:        bool = False


class InverseEngine:
    """
    Stateful, per-strategy adaptive mode selector.

    Usage:
      # After every trade close:
      inverse_engine.record(strategy_type, won=net_pnl >= 0)

      # Before every new entry:
      decision = inverse_engine.get_decision(strategy_type, signal, entry, sl, tp)
      if decision.mode == TradeMode.CALIBRATE:
          skip(decision.reason)
      use(decision.final_signal, decision.stop_loss, decision.take_profit)
    """

    def __init__(self):
        self._outcomes:      Dict[str, List[bool]] = {}   # strategy → rolling outcomes
        self._consec_losses: Dict[str, int]         = {}  # strategy → consecutive loss count
        self._calibrate_until: float = 0.0                # epoch when global pause expires

    # ── Public ────────────────────────────────────────────────────────────────

    def record(self, strategy_id: str, won: bool) -> None:
        """Record a live trade result.  Do NOT call for historical replay."""
        history = self._outcomes.setdefault(strategy_id, [])
        history.append(won)
        if len(history) > ROLLING_WINDOW:
            history.pop(0)

        if won:
            self._consec_losses[strategy_id] = 0
        else:
            streak = self._consec_losses.get(strategy_id, 0) + 1
            self._consec_losses[strategy_id] = streak
            if streak >= EQUITY_PROTECT_LOSSES:
                self._calibrate_until = time.time() + CALIBRATE_PAUSE_MIN * 60
                logger.warning(
                    f"[AIE] ⛔ Equity Protector — {strategy_id} hit "
                    f"{streak} consecutive losses → {CALIBRATE_PAUSE_MIN}min pause."
                )

    def get_decision(
        self,
        strategy_id: str,
        signal:      str,
        entry_price: float,
        stop_loss:   float,
        take_profit: float,
    ) -> InverseDecision:
        """Return the final (possibly inverted) signal and SL/TP levels."""
        mode = self._mode(strategy_id)
        wr   = self._win_rate(strategy_id)
        n    = len(self._outcomes.get(strategy_id, []))

        if mode in (TradeMode.NORMAL, TradeMode.CALIBRATE):
            return InverseDecision(
                mode=mode, original_signal=signal, final_signal=signal,
                entry_price=entry_price, stop_loss=stop_loss,
                take_profit=take_profit,
                reason=f"AIE_{mode.value}(WR={wr*100:.1f}% n={n})",
            )

        # ── INVERSE: mirror SL/TP distances to preserve RR ratio ─────────────
        sl_dist = abs(entry_price - stop_loss)
        tp_dist = abs(take_profit - entry_price)
        if signal == "LONG":
            final_signal, new_sl, new_tp = (
                "SHORT", entry_price + sl_dist, entry_price - tp_dist
            )
        else:
            final_signal, new_sl, new_tp = (
                "LONG", entry_price - sl_dist, entry_price + tp_dist
            )

        logger.info(
            f"[AIE] 🔄 INVERSE {strategy_id}: {signal}→{final_signal} "
            f"WR={wr*100:.1f}%<{INVERSE_THRESHOLD*100:.0f}% (n={n}) "
            f"entry={entry_price:.4f} sl={new_sl:.4f} tp={new_tp:.4f}"
        )
        return InverseDecision(
            mode=mode, original_signal=signal, final_signal=final_signal,
            entry_price=entry_price, stop_loss=new_sl, take_profit=new_tp,
            reason=f"AIE_INVERSE(WR={wr*100:.1f}%<{INVERSE_THRESHOLD*100:.0f}%)",
            inverted=True,
        )

    def current_mode(self, strategy_id: str) -> TradeMode:
        return self._mode(strategy_id)

    def summary(self) -> dict:
        return {
            s: {
                "mode":          self._mode(s).value,
                "win_rate":      round(self._win_rate(s), 3),
                "samples":       len(self._outcomes.get(s, [])),
                "consec_losses": self._consec_losses.get(s, 0),
            }
            for s in self._outcomes
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _win_rate(self, strategy_id: str) -> float:
        h = self._outcomes.get(strategy_id, [])
        return sum(h) / len(h) if h else 1.0

    def _mode(self, strategy_id: str) -> TradeMode:
        if time.time() < self._calibrate_until:
            return TradeMode.CALIBRATE

        outcomes = self._outcomes.get(strategy_id, [])
        if len(outcomes) < MIN_SAMPLES:
            return TradeMode.NORMAL   # not enough fresh data — keep trading

        return (
            TradeMode.INVERSE
            if self._win_rate(strategy_id) < INVERSE_THRESHOLD
            else TradeMode.NORMAL
        )


# ── Module-level singleton ────────────────────────────────────────────────────
inverse_engine = InverseEngine()

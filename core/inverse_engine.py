"""
EOW Quant Engine — Adaptive Inverse Engine  (A.I.E.)

Blueprint: if a strategy is consistently wrong it is a reliable contra-indicator.
Instead of patching a broken strategy, we detect when its win-rate drops below
a threshold and flip every signal it produces — turning losses into profits.

Per-strategy mode state machine (requires MIN_SAMPLES before activating):
  NORMAL    win_rate ≥ WIN_THRESHOLD  (≥ 60%)  → trade as generated
  NO_TRADE  WIN_THRESHOLD > win_rate ≥ INVERSE_THRESHOLD (40–60%) → skip entry
                                                   (slow-death avoidance zone)
  INVERSE   win_rate < INVERSE_THRESHOLD (< 40%) → flip direction + mirror SL/TP

Signal inversion preserves RR ratio by mirroring SL/TP distances around entry:
  Original LONG  entry=P, sl=P−d, tp=P+D  →  SHORT  sl=P+d, tp=P−D  (RR = D/d ✓)
  Original SHORT entry=P, sl=P+d, tp=P−D  →  LONG   sl=P−d, tp=P+D  (RR = D/d ✓)

Equity Protector:
  If any strategy accumulates EQUITY_PROTECT_LOSSES consecutive losses while in
  INVERSE mode, a global CALIBRATE pause is triggered. All strategies pause for
  CALIBRATE_PAUSE_MIN minutes then restart in NORMAL mode.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from loguru import logger


# ── Thresholds ────────────────────────────────────────────────────────────────
WIN_THRESHOLD          = 0.60   # ≥ 60% WR → NORMAL
INVERSE_THRESHOLD      = 0.40   # < 40% WR → INVERSE
MIN_SAMPLES            = 10     # minimum trades before mode can change from NORMAL
ROLLING_WINDOW         = 50     # look back at most last 50 trades per strategy
EQUITY_PROTECT_LOSSES  = 5      # consecutive losses (any mode) → CALIBRATE pause
CALIBRATE_PAUSE_MIN    = 30     # minutes to pause before resuming NORMAL


class TradeMode(str, Enum):
    NORMAL    = "NORMAL"
    INVERSE   = "INVERSE"
    NO_TRADE  = "NO_TRADE"
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
      # After trade closes:
      inverse_engine.record(strategy_type, won=net_pnl >= 0)

      # Before opening a new trade:
      decision = inverse_engine.get_decision(strategy_type, signal, entry, sl, tp)
      if decision.mode in (TradeMode.NO_TRADE, TradeMode.CALIBRATE):
          skip_entry(decision.reason)
      use(decision.final_signal, decision.stop_loss, decision.take_profit)
    """

    def __init__(self):
        self._outcomes:      Dict[str, List[bool]] = {}   # strategy → rolling win list
        self._consec_losses: Dict[str, int]         = {}  # strategy → current streak
        self._calibrate_until: float = 0.0                # epoch when global pause expires

    # ── Public ────────────────────────────────────────────────────────────────

    def record(self, strategy_id: str, won: bool) -> None:
        """Record a trade result.  Call once per trade close."""
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
                    f"{streak} consecutive losses → {CALIBRATE_PAUSE_MIN}min "
                    f"CALIBRATE pause."
                )

    def get_decision(
        self,
        strategy_id: str,
        signal:      str,    # "LONG" or "SHORT"
        entry_price: float,
        stop_loss:   float,
        take_profit: float,
    ) -> InverseDecision:
        """
        Return an InverseDecision with the final (possibly flipped) signal and levels.
        Callers must use decision.final_signal / .stop_loss / .take_profit.
        """
        mode = self._mode(strategy_id)
        wr   = self._win_rate(strategy_id)
        n    = len(self._outcomes.get(strategy_id, []))

        # Pass-through modes — no change to signal
        if mode in (TradeMode.NORMAL, TradeMode.CALIBRATE):
            return InverseDecision(
                mode=mode, original_signal=signal, final_signal=signal,
                entry_price=entry_price, stop_loss=stop_loss,
                take_profit=take_profit,
                reason=f"AIE_{mode.value}(WR={wr*100:.1f}% n={n})",
            )

        if mode == TradeMode.NO_TRADE:
            return InverseDecision(
                mode=mode, original_signal=signal, final_signal=signal,
                entry_price=entry_price, stop_loss=stop_loss,
                take_profit=take_profit,
                reason=(
                    f"AIE_NO_TRADE(WR={wr*100:.1f}% in 40–60% "
                    f"slow-death zone, n={n})"
                ),
            )

        # ── INVERSE mode: mirror-flip signal, preserve RR ratio ───────────────
        sl_dist = abs(entry_price - stop_loss)
        tp_dist = abs(take_profit - entry_price)

        if signal == "LONG":
            final_signal = "SHORT"
            new_sl = entry_price + sl_dist   # above entry — SHORT gets stopped going up
            new_tp = entry_price - tp_dist   # below entry — SHORT profits going down
        else:
            final_signal = "LONG"
            new_sl = entry_price - sl_dist   # below entry — LONG gets stopped going down
            new_tp = entry_price + tp_dist   # above entry — LONG profits going up

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
        """Human-readable engine state for /api/inverse-engine."""
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
        return sum(h) / len(h) if h else 1.0   # optimistic default before data

    def _mode(self, strategy_id: str) -> TradeMode:
        # Global calibration pause overrides everything
        if time.time() < self._calibrate_until:
            return TradeMode.CALIBRATE

        outcomes = self._outcomes.get(strategy_id, [])
        if len(outcomes) < MIN_SAMPLES:
            return TradeMode.NORMAL   # not enough data — default to normal

        wr = self._win_rate(strategy_id)
        if wr < INVERSE_THRESHOLD:
            return TradeMode.INVERSE
        if wr < WIN_THRESHOLD:
            return TradeMode.NO_TRADE
        return TradeMode.NORMAL


# ── Module-level singleton ────────────────────────────────────────────────────
inverse_engine = InverseEngine()

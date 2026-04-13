"""
EOW Quant Engine — Signal Quality Filter  (FTD-REF-MASTER-001)
High-quality trade gate. A signal must pass ALL checks before reaching
the execution layer.

Gate conditions (all must be True):
  1. RR (reward-to-risk)   ≥ MIN_RR
  2. ATR%                  ≥ MIN_ATR_PCT
  3. Regime confidence     ≥ MIN_CONFIDENCE
  4. Execution cost        < MAX_COST_FRACTION of gross TP

Protective pause:
  - 3 consecutive losses on any symbol → that symbol pauses for PAUSE_MINUTES
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from loguru import logger


# ── Gate thresholds ───────────────────────────────────────────────────────────
MIN_RR             = 1.8    # minimum reward-to-risk ratio
MIN_ATR_PCT        = 0.20   # minimum ATR% (liquidity / move size floor)
MIN_CONFIDENCE     = 0.60   # minimum regime AI confidence
MAX_COST_FRACTION  = 0.30   # cost must be < 30% of gross TP distance

# ── Consecutive-loss protection ───────────────────────────────────────────────
MAX_CONSECUTIVE_LOSSES = 3
PAUSE_MINUTES          = 60   # pause new entries after N consecutive losses


@dataclass
class FilterResult:
    ok:     bool
    reason: str  = ""     # populated when ok=False
    rr:     float = 0.0
    cost_fraction: float = 0.0


class SignalFilter:
    """
    Stateful signal quality gate with per-symbol consecutive-loss tracking.
    """

    def __init__(self):
        # symbol → consecutive loss count
        self._consec_losses: Dict[str, int]   = {}
        # symbol → epoch ms of last loss that triggered pause
        self._pause_until:   Dict[str, float] = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def check(
        self,
        symbol:     str,
        entry:      float,
        take_profit: float,
        stop_loss:  float,
        cost_usdt:  float,      # total round-trip cost in USDT
        atr_pct:    float,
        confidence: float,      # from RegimeAI.classify()
    ) -> FilterResult:
        """
        Returns FilterResult(ok=True) if the signal passes all gates.
        Returns FilterResult(ok=False, reason=…) if any gate fails.
        """
        # 0. Consecutive-loss pause
        pause_exp = self._pause_until.get(symbol, 0.0)
        if time.time() < pause_exp:
            remaining = (pause_exp - time.time()) / 60
            return FilterResult(
                ok=False,
                reason=f"LOSS_PAUSE({self._consec_losses.get(symbol,0)} losses, "
                       f"{remaining:.0f}min remaining)",
            )

        # 1. RR gate
        gross_tp = abs(take_profit - entry)
        gross_sl = abs(entry - stop_loss)
        rr = (gross_tp / gross_sl) if gross_sl > 0 else 0.0
        if rr < MIN_RR:
            return FilterResult(
                ok=False, reason=f"LOW_RR({rr:.2f}<{MIN_RR})", rr=rr
            )

        # 2. ATR% gate
        if atr_pct < MIN_ATR_PCT:
            return FilterResult(
                ok=False,
                reason=f"LOW_ATR({atr_pct:.3f}%<{MIN_ATR_PCT}%)",
                rr=rr,
            )

        # 3. Confidence gate
        if confidence < MIN_CONFIDENCE:
            return FilterResult(
                ok=False,
                reason=f"LOW_CONFIDENCE({confidence:.2f}<{MIN_CONFIDENCE})",
                rr=rr,
            )

        # 4. Cost fraction gate
        cost_fraction = (cost_usdt / gross_tp) if gross_tp > 0 else 1.0
        if cost_fraction >= MAX_COST_FRACTION:
            return FilterResult(
                ok=False,
                reason=f"COST_HIGH({cost_fraction:.0%}>={MAX_COST_FRACTION:.0%})",
                rr=rr, cost_fraction=cost_fraction,
            )

        return FilterResult(ok=True, rr=round(rr, 3), cost_fraction=round(cost_fraction, 3))

    def record_loss(self, symbol: str):
        """
        Call after every losing trade on *symbol*.
        If consecutive losses reach MAX_CONSECUTIVE_LOSSES, pause the symbol.
        """
        count = self._consec_losses.get(symbol, 0) + 1
        self._consec_losses[symbol] = count
        if count >= MAX_CONSECUTIVE_LOSSES:
            self._pause_until[symbol] = time.time() + PAUSE_MINUTES * 60
            logger.warning(
                f"[SIG-FILTER] {symbol} paused for {PAUSE_MINUTES}min "
                f"after {count} consecutive losses."
            )

    def record_win(self, symbol: str):
        """Reset consecutive loss counter after a win."""
        self._consec_losses[symbol] = 0

    def is_paused(self, symbol: str) -> bool:
        return time.time() < self._pause_until.get(symbol, 0.0)

    def consecutive_losses(self, symbol: str) -> int:
        return self._consec_losses.get(symbol, 0)

    def summary(self) -> dict:
        now = time.time()
        paused = {
            sym: round((self._pause_until[sym] - now) / 60, 1)
            for sym in self._pause_until
            if now < self._pause_until[sym]
        }
        return {
            "consecutive_losses": dict(self._consec_losses),
            "paused_symbols":     paused,
            "thresholds": {
                "min_rr":          MIN_RR,
                "min_atr_pct":     MIN_ATR_PCT,
                "min_confidence":  MIN_CONFIDENCE,
                "max_cost_frac":   MAX_COST_FRACTION,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
signal_filter = SignalFilter()

"""
EOW Quant Engine — Regime Debounce
Suppresses redundant regime log spam.
Only logs (and fires callbacks) when the regime actually transitions
for a given symbol — prevents thousands of identical INFO lines.
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional

from loguru import logger

from core.regime_detector import Regime, RegimeState


class RegimeDebounce:
    """
    Wraps regime state tracking with transition-only logging.
    Feed every regime update through push(); it silently drops duplicates.
    """

    def __init__(self):
        self._last:   Dict[str, Regime] = {}
        self._ts:     Dict[str, int]    = {}   # epoch ms of last regime change
        self._counts: Dict[str, int]    = {}   # consecutive candles in current regime
        self._cbs:    List[Callable]    = []

    # ── Public ────────────────────────────────────────────────────────────────

    def register_callback(self, fn: Callable[[str, Optional[Regime], Regime], None]):
        """
        Register a function called only on genuine transitions.
        Signature: fn(symbol, old_regime_or_None, new_regime)
        """
        self._cbs.append(fn)

    def push(self, symbol: str, new_regime: Regime,
             state: Optional[RegimeState] = None):
        """
        Feed the latest regime classification for a symbol.
        Logs + fires callbacks only on change.
        """
        old = self._last.get(symbol)
        self._counts[symbol] = self._counts.get(symbol, 0) + 1

        if old == new_regime:
            return   # same regime — nothing to do

        # Genuine transition (or first observation)
        self._last[symbol] = new_regime
        self._ts[symbol]   = int(time.time() * 1000)

        details = ""
        if state:
            details = (
                f" ADX={state.adx:.1f} ATR%={state.atr_pct:.2f} "
                f"BB%={state.bb_width:.2f} conf={state.confidence:.2f}"
            )

        if old is None:
            logger.info(f"[REGIME-DB] {symbol} initial → {new_regime.value}{details}")
        else:
            logger.info(
                f"[REGIME-DB] {symbol} {old.value} → {new_regime.value}{details}"
            )

        for cb in self._cbs:
            try:
                cb(symbol, old, new_regime)
            except Exception as exc:
                logger.debug(f"[REGIME-DB] callback error: {exc}")

    # ── Query helpers ─────────────────────────────────────────────────────────

    def get_last(self, symbol: str) -> Optional[Regime]:
        return self._last.get(symbol)

    def transition_ts(self, symbol: str) -> int:
        """Epoch ms of last regime change for symbol, or 0 if never seen."""
        return self._ts.get(symbol, 0)

    def candle_count(self, symbol: str) -> int:
        """Number of candles pushed for this symbol (resets on new symbol)."""
        return self._counts.get(symbol, 0)

    def summary(self) -> dict:
        return {
            sym: {
                "regime":       self._last[sym].value,
                "since_ms":     self._ts.get(sym, 0),
                "candle_count": self._counts.get(sym, 0),
            }
            for sym in self._last
        }


# ── Module-level singleton ────────────────────────────────────────────────────
regime_debounce = RegimeDebounce()

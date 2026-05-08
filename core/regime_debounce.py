"""
EOW Quant Engine — Regime Debounce
Suppresses redundant regime log spam.
Only logs (and fires callbacks) when the regime actually transitions
for a given symbol — prevents thousands of identical INFO lines.

Persistence window (MIN_PERSIST_CANDLES):
A new regime must hold for this many consecutive candles before the transition
is confirmed and callbacks are fired. Absorbs single-candle noise around ADX=20
without delaying genuine trend detection. Set to 1 to restore original behavior.
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional

from loguru import logger

from core.regime_detector import Regime, RegimeState


# New regime must hold this many consecutive candles before confirmed.
# 3 candles = minimal noise filter; does not meaningfully delay real transitions.
MIN_PERSIST_CANDLES = 3


class RegimeDebounce:
    """
    Wraps regime state tracking with transition-only logging.
    Feed every regime update through push(); it silently drops duplicates
    and absorbs short-lived oscillations via the persistence window.
    """

    def __init__(self):
        self._last:      Dict[str, Regime] = {}
        self._ts:        Dict[str, int]    = {}   # epoch ms of last confirmed change
        self._counts:    Dict[str, int]    = {}   # total candles pushed per symbol
        self._candidate: Dict[str, Regime] = {}   # unconfirmed pending regime
        self._cand_ct:   Dict[str, int]    = {}   # consecutive candles in candidate
        self._cbs:       List[Callable]    = []

    # ── Public ────────────────────────────────────────────────────────────────

    def register_callback(self, fn: Callable[[str, Optional[Regime], Regime], None]):
        """
        Register a function called only on confirmed transitions.
        Signature: fn(symbol, old_regime_or_None, new_regime)
        """
        self._cbs.append(fn)

    def push(self, symbol: str, new_regime: Regime,
             state: Optional[RegimeState] = None):
        """
        Feed the latest regime classification for a symbol.
        Logs + fires callbacks only on confirmed transitions.
        First observation bypasses persistence (no prior state to debounce).
        """
        old = self._last.get(symbol)
        self._counts[symbol] = self._counts.get(symbol, 0) + 1

        # ── First observation: no prior state, confirm immediately ─────────
        if old is None:
            self._candidate.pop(symbol, None)
            self._cand_ct.pop(symbol, None)
            self._confirm(symbol, old, new_regime, state)
            return

        # ── Same as confirmed regime: clear any pending candidate ──────────
        if old == new_regime:
            self._candidate.pop(symbol, None)
            self._cand_ct.pop(symbol, None)
            return

        # ── Different from confirmed regime: apply persistence window ──────
        cand = self._candidate.get(symbol)

        if cand == new_regime:
            # Candidate continues — increment counter
            count = self._cand_ct.get(symbol, 1) + 1
            self._cand_ct[symbol] = count
            if count < MIN_PERSIST_CANDLES:
                logger.debug(
                    f"[REGIME-DB] {symbol} candidate {new_regime.value} "
                    f"({count}/{MIN_PERSIST_CANDLES})"
                )
                return
            # Persistence met — confirm
            self._candidate.pop(symbol, None)
            self._cand_ct.pop(symbol, None)
            self._confirm(symbol, old, new_regime, state)
        else:
            # New candidate (or candidate changed mid-oscillation)
            self._candidate[symbol] = new_regime
            self._cand_ct[symbol]   = 1
            logger.debug(
                f"[REGIME-DB] {symbol} candidate {new_regime.value} "
                f"(1/{MIN_PERSIST_CANDLES})"
            )

    # ── Query helpers ─────────────────────────────────────────────────────────

    def get_last(self, symbol: str) -> Optional[Regime]:
        """Return the last *confirmed* regime for symbol."""
        return self._last.get(symbol)

    def get_candidate(self, symbol: str) -> Optional[Regime]:
        """Return the pending (unconfirmed) candidate regime, or None."""
        return self._candidate.get(symbol)

    def transition_ts(self, symbol: str) -> int:
        """Epoch ms of last confirmed regime change, or 0 if never seen."""
        return self._ts.get(symbol, 0)

    def candle_count(self, symbol: str) -> int:
        """Total candles pushed for this symbol."""
        return self._counts.get(symbol, 0)

    def summary(self) -> dict:
        symbols = set(self._last) | set(self._candidate)
        return {
            sym: {
                "regime":          self._last[sym].value if sym in self._last else None,
                "candidate":       self._candidate[sym].value if sym in self._candidate else None,
                "candidate_count": self._cand_ct.get(sym, 0),
                "since_ms":        self._ts.get(sym, 0),
                "candle_count":    self._counts.get(sym, 0),
            }
            for sym in symbols
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _confirm(
        self,
        symbol:     str,
        old:        Optional[Regime],
        new_regime: Regime,
        state:      Optional[RegimeState],
    ) -> None:
        """Commit a confirmed regime transition: update state, log, fire callbacks."""
        self._last[symbol] = new_regime
        self._ts[symbol]   = int(time.time() * 1000)

        details = ""
        if state:
            details = (
                f" ADX={state.adx:.1f} ATR%={state.atr_pct:.2f} "
                f"BB%={state.bb_width:.2f} conf={state.confidence:.2f}"
            )

        if old is None:
            if new_regime.value == "UNKNOWN":
                logger.debug(f"[REGIME-DB] {symbol} initial → UNKNOWN (warming up)")
            else:
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


# ── Module-level singleton ────────────────────────────────────────────────────
regime_debounce = RegimeDebounce()

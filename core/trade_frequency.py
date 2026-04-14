"""
EOW Quant Engine — Trade Frequency Controller  (FTD-REF-023)
Detects dry spells and returns a relaxation factor to loosen signal filters.

Rules:
  - 0 trades in last 30 min  → relaxation_factor = 0.88 (−12%)
  - < 2 trades in last 2 hr  → relaxation_factor = 0.92 (−8%)
  - Otherwise                → relaxation_factor = 1.0  (no relaxation)

Relaxation is multiplicative with signal_filter thresholds, i.e.:
  effective_min_rr = base_min_rr × relaxation_factor
"""
from __future__ import annotations

import time
from collections import deque
from typing import Deque

from loguru import logger


# ── Dry-spell windows ─────────────────────────────────────────────────────────
WINDOW_SHORT_SEC  = 30 * 60    # 30 minutes
WINDOW_LONG_SEC   = 2  * 3600  # 2 hours
MIN_TRADES_LONG   = 2          # threshold for long-window check

RELAX_SHORT       = 0.88       # factor when 30-min window is empty
RELAX_LONG        = 0.92       # factor when 2-hr window has < 2 trades
MAX_HISTORY       = 500        # max timestamps to keep in memory


class TradeFrequency:
    """
    Tracks trade timestamps and provides a relaxation_factor for SignalFilter.
    Call record_trade() every time a trade is opened.
    Call get_relaxation_factor() before calling signal_filter.check().
    """

    def __init__(self):
        # Ring buffer of trade open timestamps (epoch seconds)
        self._timestamps: Deque[float] = deque(maxlen=MAX_HISTORY)

    # ── Public ────────────────────────────────────────────────────────────────

    def record_trade(self):
        """Call when a new position is opened."""
        self._timestamps.append(time.time())

    def get_relaxation_factor(self) -> float:
        """
        Returns a factor in [0.88, 1.0].
        A lower factor → looser signal filter thresholds.
        """
        now = time.time()
        self._purge_old(now)

        count_short = self._count_since(now - WINDOW_SHORT_SEC)
        count_long  = self._count_since(now - WINDOW_LONG_SEC)

        if count_short == 0:
            factor = RELAX_SHORT
            logger.debug(
                f"[TRADE-FREQ] 0 trades in 30 min → relax factor={factor}"
            )
        elif count_long < MIN_TRADES_LONG:
            factor = RELAX_LONG
            logger.debug(
                f"[TRADE-FREQ] {count_long} trades in 2 hr → relax factor={factor}"
            )
        else:
            factor = 1.0

        return factor

    def trades_in_window(self, seconds: float) -> int:
        """How many trades were opened in the last *seconds* seconds."""
        now = time.time()
        return self._count_since(now - seconds)

    def summary(self) -> dict:
        now = time.time()
        return {
            "trades_last_30min": self._count_since(now - WINDOW_SHORT_SEC),
            "trades_last_2hr":   self._count_since(now - WINDOW_LONG_SEC),
            "trades_last_24hr":  self._count_since(now - 86400),
            "relaxation_factor": self.get_relaxation_factor(),
        }

    # ── Internals ────────────────────────────────────────────────────────────

    def _count_since(self, since: float) -> int:
        return sum(1 for ts in self._timestamps if ts >= since)

    def _purge_old(self, now: float):
        # Keep only timestamps from the last 24 hours
        cutoff = now - 86400
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()


# ── Module-level singleton ────────────────────────────────────────────────────
trade_frequency = TradeFrequency()

"""
EOW Quant Engine — Learning Engine  (FTD-REF-023 + FTD-REF-024)
Tracks per-regime win-rate and dynamically adjusts confidence weights.

How it works:
  - Every closed trade is recorded with its regime and outcome (win/loss).
  - Per-regime win-rate is computed over a rolling window (default 50 trades).
  - A weight multiplier is derived (FTD-REF-024 adds drastic tier at <40%):

      win_rate ≥ 55%      → weight = 1.00  (regime performing well)
      win_rate 45 – 55%   → interpolated  0.80 → 1.00
      win_rate 40 – 45%   → interpolated  0.50 → 0.80
      win_rate < 40%      → weight = 0.50  (drastically reduced — FTD-REF-024)

  - The multiplier is applied to confidence before SignalFilter so the engine
    is more conservative when a regime has been consistently losing.

Usage:
  learning_engine.record(regime="TRENDING", won=True)
  weight = learning_engine.get_regime_weight("TRENDING")  # e.g. 0.93
  adjusted_confidence = raw_confidence * weight
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Deque, List, Tuple

from loguru import logger


# ── Tuning constants ──────────────────────────────────────────────────────────
WINDOW_SIZE          = 50     # rolling window of trades per regime
MIN_SAMPLES          = 5      # need at least this many trades before adjusting weight
WR_HIGH_THRESH       = 0.55   # ≥ 55% win-rate → full weight (1.0)
WR_LOW_THRESH        = 0.45   # 45–55% win-rate → interpolate 0.80→1.00
WR_DRASTIC_THRESH    = 0.40   # < 40% win-rate → drastic reduction (FTD-REF-024)
WEIGHT_AT_HIGH_WR    = 1.00   # multiplier when win-rate is at or above WR_HIGH_THRESH
WEIGHT_AT_LOW_WR     = 0.80   # multiplier at WR_LOW_THRESH boundary
WEIGHT_AT_DRASTIC_WR = 0.50   # multiplier when win-rate < WR_DRASTIC_THRESH


@dataclass
class RegimeStats:
    regime:      str
    n_trades:    int
    n_wins:      int
    win_rate:    float
    weight:      float
    window_size: int


class LearningEngine:
    """
    Stateful per-regime performance tracker.
    Thread-safe for single asyncio event loop (no locks needed).
    """

    def __init__(self, window_size: int = WINDOW_SIZE):
        self._window = window_size
        # regime → deque of bool (True=win, False=loss)
        self._history: Dict[str, Deque[bool]] = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def record(self, regime: str, won: bool):
        """
        Record the result of a closed trade.
        regime — Regime.value string (e.g. "TRENDING")
        won    — True if the trade was profitable (net_pnl > 0)
        """
        if regime not in self._history:
            self._history[regime] = deque(maxlen=self._window)
        self._history[regime].append(won)

        stats = self._compute_stats(regime)
        logger.debug(
            f"[LEARN-ENG] {regime}: win_rate={stats.win_rate:.1%} "
            f"weight={stats.weight:.2f} ({stats.n_trades} trades)"
        )

    def get_regime_weight(self, regime: str) -> float:
        """
        Returns a confidence multiplier for the given regime.
        1.0 = no adjustment, 0.80 = 20% penalty.
        Falls back to 1.0 if regime has insufficient data.
        """
        if regime not in self._history:
            return 1.0
        history = self._history[regime]
        if len(history) < MIN_SAMPLES:
            return 1.0
        return self._weight_from_wr(self._win_rate(history))

    def stats(self, regime: str) -> RegimeStats:
        """Return a snapshot of stats for a given regime."""
        return self._compute_stats(regime)

    def all_stats(self) -> List[RegimeStats]:
        return [self._compute_stats(r) for r in self._history]

    def summary(self) -> dict:
        return {
            "window_size":  self._window,
            "min_samples":  MIN_SAMPLES,
            "thresholds":   {
                "wr_high":       WR_HIGH_THRESH,
                "wr_low":        WR_LOW_THRESH,
                "weight_at_low": WEIGHT_AT_LOW_WR,
            },
            "regimes": {
                r: {
                    "n_trades":  len(h),
                    "win_rate":  round(self._win_rate(h), 3),
                    "weight":    round(self.get_regime_weight(r), 3),
                }
                for r, h in self._history.items()
            },
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _compute_stats(self, regime: str) -> RegimeStats:
        history  = self._history.get(regime, deque())
        n        = len(history)
        n_wins   = sum(1 for x in history if x)
        wr       = self._win_rate(history)
        weight   = self._weight_from_wr(wr) if n >= MIN_SAMPLES else 1.0
        return RegimeStats(
            regime=regime,
            n_trades=n,
            n_wins=n_wins,
            win_rate=round(wr, 3),
            weight=round(weight, 3),
            window_size=self._window,
        )

    @staticmethod
    def _win_rate(history: Deque[bool]) -> float:
        if not history:
            return 0.0
        return sum(1 for x in history if x) / len(history)

    @staticmethod
    def _weight_from_wr(win_rate: float) -> float:
        """
        Three-tier linear interpolation (FTD-REF-024 adds drastic tier):
          ≥ 55%      → 1.00
          45–55%     → 0.80 → 1.00 (linear)
          40–45%     → 0.50 → 0.80 (linear)
          < 40%      → 0.50 (drastic — significantly under-performing regime)
        """
        if win_rate >= WR_HIGH_THRESH:
            return WEIGHT_AT_HIGH_WR

        if win_rate >= WR_LOW_THRESH:
            # Interpolate between 0.80 and 1.00
            ratio = (win_rate - WR_LOW_THRESH) / (WR_HIGH_THRESH - WR_LOW_THRESH)
            return WEIGHT_AT_LOW_WR + ratio * (WEIGHT_AT_HIGH_WR - WEIGHT_AT_LOW_WR)

        if win_rate >= WR_DRASTIC_THRESH:
            # Interpolate between 0.50 and 0.80 (FTD-REF-024)
            ratio = (win_rate - WR_DRASTIC_THRESH) / (WR_LOW_THRESH - WR_DRASTIC_THRESH)
            return WEIGHT_AT_DRASTIC_WR + ratio * (WEIGHT_AT_LOW_WR - WEIGHT_AT_DRASTIC_WR)

        # Below 40%: drastic weight reduction
        return WEIGHT_AT_DRASTIC_WR


# ── Module-level singleton ────────────────────────────────────────────────────
learning_engine = LearningEngine()

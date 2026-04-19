"""
EOW Quant Engine — Phase 5: Confidence Decay Engine
Reduces trust in overused or repetitive signal patterns.

Decay mechanism:
  - Pattern frequency: count how many times the same strategy fired on
    the same symbol within the last DECAY_FREQ_WINDOW_MIN minutes.
  - When count > DECAY_FREQ_MAX, apply 10% confidence reduction per
    extra occurrence (minimum floor: DECAY_MIN_FACTOR of base confidence).

Formula:
  DecayedConf = BaseConf × decay_factor
  decay_factor = max(DECAY_MIN_FACTOR, 1.0 − DECAY_PER_EXTRA × over_count)
  over_count   = max(0, frequency − DECAY_FREQ_MAX)

Rationale: a strategy firing repeatedly on the same symbol without a
trade being taken means the pattern is not "fresh" — the market has
already absorbed that information and the setup is stale.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Tuple

from loguru import logger

from config import cfg


@dataclass
class DecayResult:
    decayed_confidence: float
    decay_factor:       float
    frequency:          int
    reason:             str = ""


class ConfidenceDecayEngine:
    """
    Tracks signal frequency per (symbol, strategy_id) within a rolling time
    window and applies a proportional confidence penalty to repeated patterns.
    """

    def __init__(self):
        # (symbol, strategy_id) → deque of timestamps (epoch seconds)
        self._signal_ts: Dict[Tuple[str, str], Deque[float]] = defaultdict(
            lambda: deque(maxlen=100)
        )
        self._window_sec   = cfg.DECAY_FREQ_WINDOW_MIN * 60
        self._freq_max     = cfg.DECAY_FREQ_MAX
        self._per_extra    = cfg.DECAY_PER_EXTRA
        self._min_factor   = cfg.DECAY_MIN_FACTOR
        logger.info(
            f"[CONF-DECAY] Phase 5 activated | "
            f"window={cfg.DECAY_FREQ_WINDOW_MIN}min "
            f"freq_max={self._freq_max} "
            f"decay_per_extra={self._per_extra:.0%} "
            f"min_factor={self._min_factor}"
        )

    def decay(
        self,
        symbol:      str,
        strategy_id: str,
        base_conf:   float,
        record_signal: bool = True,
    ) -> DecayResult:
        """
        Apply frequency-based confidence decay.

        Args:
            symbol:        trading symbol
            strategy_id:   strategy that generated the signal
            base_conf:     confidence from scorer (0–1)
            record_signal: whether to record this signal occurrence (True on real signals)

        Returns DecayResult with decayed_confidence ready to use.
        """
        key = (symbol, strategy_id)
        now = time.time()
        cutoff = now - self._window_sec

        # Trim stale timestamps
        ts_queue = self._signal_ts[key]
        while ts_queue and ts_queue[0] < cutoff:
            ts_queue.popleft()

        frequency = len(ts_queue)

        # Record this signal occurrence
        if record_signal:
            ts_queue.append(now)
            frequency = len(ts_queue)

        # Compute decay factor
        over_count = max(0, frequency - self._freq_max)
        if over_count > 0:
            decay_factor = max(self._min_factor, 1.0 - self._per_extra * over_count)
            reason = (f"FREQ_DECAY(count={frequency}>{self._freq_max} "
                      f"over={over_count} factor={decay_factor:.2f})")
            logger.debug(f"[CONF-DECAY] {symbol}@{strategy_id} {reason}")
        else:
            decay_factor = 1.0
            reason = f"NO_DECAY(count={frequency}≤{self._freq_max})"

        return DecayResult(
            decayed_confidence=round(base_conf * decay_factor, 4),
            decay_factor=round(decay_factor, 4),
            frequency=frequency,
            reason=reason,
        )

    def get_frequency(self, symbol: str, strategy_id: str) -> int:
        """Return current signal count in the tracking window."""
        key = (symbol, strategy_id)
        now = time.time()
        cutoff = now - self._window_sec
        ts_queue = self._signal_ts.get(key, deque())
        return sum(1 for t in ts_queue if t >= cutoff)

    def reset(self, symbol: str, strategy_id: str):
        """Reset frequency counter when a trade is taken (fresh start)."""
        self._signal_ts[(symbol, strategy_id)].clear()

    def summary(self) -> dict:
        now = time.time()
        cutoff = now - self._window_sec
        active = {
            f"{sym}@{strat}": sum(1 for t in q if t >= cutoff)
            for (sym, strat), q in self._signal_ts.items()
            if any(t >= cutoff for t in q)
        }
        return {
            "window_min":   cfg.DECAY_FREQ_WINDOW_MIN,
            "freq_max":     self._freq_max,
            "decay_per_extra": self._per_extra,
            "min_factor":   self._min_factor,
            "active_counts": active,
            "module":       "CONFIDENCE_DECAY",
            "phase":        5,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
confidence_decay = ConfidenceDecayEngine()

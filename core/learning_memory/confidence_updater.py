"""
FTD-030B Part 3 — Confidence Updater

Formula: confidence = success_rate × recency × regime_bonus × 100
  success_rate  = success / samples
  recency       = 0.95 ^ age   (age = cycle_seq - last_seen)
  regime_bonus  = 1.1 if multi-regime (contexts span ≥ 2 distinct regimes) else 1.0

Result is clamped to [0, 100].
"""
from __future__ import annotations
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import PatternRecord

RECENCY_DECAY    = 0.95
REGIME_BONUS     = 1.10
MULTI_REGIME_MIN = 2      # contexts must include ≥ 2 distinct regime prefixes


class ConfidenceUpdater:

    MODULE = "CONFIDENCE_UPDATER"
    PHASE  = "030B"

    def update(self, pattern: "PatternRecord", current_cycle: int) -> float:
        """Recompute and store pattern.confidence. Returns the new value."""
        if pattern.samples == 0:
            pattern.confidence = 0.0
            return 0.0

        success_rate = pattern.success / pattern.samples
        age          = max(0, current_cycle - pattern.last_seen)
        recency      = RECENCY_DECAY ** age
        bonus        = REGIME_BONUS if self._is_multi_regime(pattern) else 1.0

        raw = success_rate * recency * bonus * 100.0
        pattern.confidence = round(min(100.0, max(0.0, raw)), 2)
        return pattern.confidence

    def update_all(self, patterns: list, current_cycle: int) -> None:
        for p in patterns:
            self.update(p, current_cycle)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_multi_regime(pattern: "PatternRecord") -> bool:
        regimes = {ctx.split("/")[0] for ctx in pattern.contexts if ctx}
        return len(regimes) >= MULTI_REGIME_MIN

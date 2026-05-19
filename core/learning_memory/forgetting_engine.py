"""
FTD-030B Part 6 — Forgetting Engine

Prevents drift by aging and pruning low-confidence patterns.
Rules:
  - Time decay applied via ConfidenceUpdater (0.95 ^ age)
  - Rollback penalty: confidence × 0.7
  - Remove pattern if confidence < 25 after update
  - Sub-formation patterns (< FORMATION_MIN_SAMPLES) are immune from pruning:
    confidence on fewer than 20 observations is statistically unreliable and
    early pruning creates a thrashing cycle where patterns can never accumulate
    to the formation gate.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import PatternEngine, PatternRecord

ROLLBACK_PENALTY     = 0.70   # multiply confidence by this on rollback
REMOVAL_THRESHOLD    = 25.0   # remove pattern when confidence drops below this

# Mirror of PatternEngine.FORMATION_MIN_SAMPLES — avoid circular import.
# Patterns below this sample count are immune from confidence-based pruning.
_PRUNE_MIN_SAMPLES   = 20


class ForgettingEngine:

    MODULE = "FORGETTING_ENGINE"
    PHASE  = "030B"

    def apply_rollback_penalty(self, pattern: "PatternRecord") -> None:
        """Apply rollback penalty to a pattern's confidence."""
        pattern.confidence = round(pattern.confidence * ROLLBACK_PENALTY, 2)

    def prune(self, engine: "PatternEngine") -> List[str]:
        """
        Remove all patterns with confidence < threshold.
        Returns list of removed pattern_ids.
        """
        to_remove = [
            key for key, pat in engine._patterns.items()
            if pat.confidence < REMOVAL_THRESHOLD
            and pat.samples >= _PRUNE_MIN_SAMPLES
        ]
        removed_ids = []
        for key in to_remove:
            pat = engine._patterns.pop(key, None)
            if pat:
                removed_ids.append(pat.pattern_id)
        return removed_ids

    def run(self, engine: "PatternEngine", current_cycle: int) -> List[str]:
        """
        Full forgetting pass: update all confidences via decay then prune weak patterns.
        Returns list of pruned pattern_ids.
        """
        from core.learning_memory.confidence_updater import ConfidenceUpdater
        updater = ConfidenceUpdater()
        updater.update_all(engine.all_patterns(), current_cycle)
        return self.prune(engine)

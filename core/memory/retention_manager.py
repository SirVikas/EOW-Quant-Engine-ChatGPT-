"""
FTD-030B — Forgetting Engine (Retention Manager)
Applies ALL three decay mechanisms (Q10-D): time decay + performance decay + confidence purge.

Decay rules (spec §PART 6):
  - time decay:      0.95^age_days
  - rollback penalty: ×0.7 on bad outcomes
  - remove if confidence (weight) < 0.25 (spec: remove if confidence < 25)
"""
from __future__ import annotations
import time
from typing import Any, Dict

from core.memory.memory_store import MemoryStore

TIME_DECAY_BASE   = 0.95    # per-day time decay factor (spec: 0.95^age)
PERF_DECAY_FACTOR = 0.70    # rollback penalty multiplier (spec ×0.7)
PURGE_THRESHOLD   = 0.25    # remove when weight < 0.25 (spec: confidence < 25)


class RetentionManager:

    def __init__(self, store: MemoryStore):
        self._store = store

    def apply_decay(self) -> Dict[str, Any]:
        """
        For every entry:
          1. Time decay  — exponential half-life
          2. Perf decay  — bad outcomes shrink weight faster
        Then purge entries whose weight fell below threshold.
        """
        now_ms = int(time.time() * 1000)
        updates: Dict[str, float] = {}

        for entry in self._store.all_entries():
            w = entry.decay_weight
            # Time decay: 0.95^age_days (spec §PART 6)
            age_days = (now_ms - entry.ts) / (1000.0 * 86400.0)
            w       *= TIME_DECAY_BASE ** age_days
            # Rollback/bad-outcome penalty: ×0.7
            if entry.outcome_score <= -0.5 or entry.rolled_back:
                w *= PERF_DECAY_FACTOR
            updates[entry.entry_id] = max(0.0, w)

        self._store.update_weights(updates)
        purged = self._store.purge_below_weight(PURGE_THRESHOLD)
        return {"updated": len(updates), "purged": purged}

    def summary(self) -> Dict[str, Any]:
        entries = self._store.all_entries()
        if not entries:
            return {"total_entries": 0, "avg_weight": 0.0, "min_weight": 0.0}
        weights = [e.decay_weight for e in entries]
        return {
            "total_entries": len(entries),
            "avg_weight":    round(sum(weights) / len(weights), 4),
            "min_weight":    round(min(weights), 4),
        }

"""
FTD-030B — forgetting_engine.py
Anti-drift mechanism: decays, penalises, and removes stale/bad patterns.

Rules:
  - Time decay:         confidence × 0.95^age_cycles  (applied per cycle)
  - Rollback penalty:   confidence × 0.70             (applied per rollback event)
  - Removal threshold:  if confidence < 25.0 → remove from active memory
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

from core.learning_memory.confidence_updater import apply_rollback_penalty, apply_time_decay

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import Pattern, PatternEngine

REMOVAL_THRESHOLD = 25.0   # patterns below this confidence are removed


class ForgettingEngine:
    """
    Runs at the end of each correction cycle to apply decay and prune patterns.
    Returns lists of decayed and removed pattern IDs for audit purposes.
    """

    def __init__(self):
        self._total_removed:  int = 0
        self._total_decayed:  int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def run_cycle(self, engine: "PatternEngine") -> Dict[str, list]:
        """
        Apply one cycle of time decay to all patterns.
        Remove patterns whose confidence drops below REMOVAL_THRESHOLD.

        Returns:
            {"decayed": [pattern_id, ...], "removed": [pattern_id, ...]}
        """
        decayed: List[str] = []
        to_remove: List[str] = []

        for pat in engine.all_patterns():
            old_conf = pat.confidence
            pat.confidence = apply_time_decay(pat.confidence, age_delta=1)

            if pat.confidence < old_conf:
                decayed.append(pat.pattern_id)
                self._total_decayed += 1

            if pat.confidence < REMOVAL_THRESHOLD:
                to_remove.append(pat.pattern_id)

        for pid in to_remove:
            engine.remove(pid)
            self._total_removed += 1

        return {"decayed": decayed, "removed": to_remove}

    def apply_rollback_penalty(
        self, engine: "PatternEngine", pattern_id: str
    ) -> Tuple[float, float]:
        """
        Apply rollback penalty to the specified pattern.
        Returns (before_confidence, after_confidence).
        """
        pat = engine.get(pattern_id)
        if pat is None:
            return 0.0, 0.0
        before = pat.confidence
        pat.confidence = apply_rollback_penalty(pat.confidence)
        return before, pat.confidence

    def summary(self) -> Dict[str, int]:
        return {
            "total_removed": self._total_removed,
            "total_decayed": self._total_decayed,
            "removal_threshold": REMOVAL_THRESHOLD,
            "module": "FORGETTING_ENGINE",
            "phase":  "030B",
        }

"""
FTD-030 — Memory Validator
Validates memory maturity: ALL three gates (Q5-D):
  1. min 20 total samples
  2. pattern confidence ≥ 70
  3. stability across 3 consecutive validation cycles
"""
from __future__ import annotations
from typing import Any, Dict, List

from core.memory.pattern_detector import Pattern

MIN_TOTAL_SAMPLES    = 20
MIN_PATTERN_CONF     = 70.0
STABILITY_WINDOW     = 3       # pattern must pass for 3 consecutive calls


class MemoryValidator:

    def __init__(self):
        self._stability_counts: Dict[str, int] = {}

    def validate_patterns(self, patterns: Dict[str, Pattern]) -> Dict[str, Any]:
        valid:   List[str] = []
        invalid: List[str] = []

        for pid, p in patterns.items():
            if p.sample_count >= MIN_TOTAL_SAMPLES and p.confidence >= MIN_PATTERN_CONF:
                self._stability_counts[pid] = self._stability_counts.get(pid, 0) + 1
            else:
                self._stability_counts[pid] = 0

            if self._stability_counts.get(pid, 0) >= STABILITY_WINDOW:
                valid.append(pid)
            else:
                invalid.append(pid)

        # Remove stale patterns that no longer exist
        active_pids = set(patterns.keys())
        self._stability_counts = {
            k: v for k, v in self._stability_counts.items() if k in active_pids
        }

        total_samples = sum(p.sample_count for p in patterns.values())
        memory_ready  = total_samples >= MIN_TOTAL_SAMPLES and len(valid) > 0

        return {
            "memory_ready":     memory_ready,
            "total_samples":    total_samples,
            "valid_patterns":   valid,
            "invalid_patterns": invalid,
            "stability_counts": dict(self._stability_counts),
        }

    def reset_stability(self, pattern_id: str) -> None:
        self._stability_counts.pop(pattern_id, None)

    def reset_all(self) -> None:
        self._stability_counts.clear()

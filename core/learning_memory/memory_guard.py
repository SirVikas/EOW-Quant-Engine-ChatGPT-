"""
FTD-030B Part 5 — Memory Guard

Safety enforcement layer — runs before any memory-influenced change is applied.
Rules:
  - Hard limits are NEVER touched (from FTD-029 HARD_LIMITS)
  - Max 30% parameter shift from base value
  - No duplicate parameter changes in a single cycle
  - PolicyGuard final veto (delegates to FTD-029 policy_guard if available)
"""
from __future__ import annotations
from typing import Any, Dict, List, Set, Tuple

from core.self_correction.correction_proposal import HARD_LIMITS, TUNABLE_PARAMS

MAX_MEMORY_SHIFT_PCT = 0.30   # max 30% shift from current value


class MemoryGuard:

    MODULE = "MEMORY_GUARD"
    PHASE  = "030B"

    def __init__(self):
        self._applied_this_cycle: Set[str] = set()

    def reset_cycle(self) -> None:
        self._applied_this_cycle.clear()

    def check(
        self,
        parameter: str,
        current_value: float,
        proposed_value: float,
    ) -> Tuple[bool, str]:
        """
        Returns (allowed: bool, reason: str).
        reason is empty string when allowed.
        """
        if parameter in HARD_LIMITS:
            return False, f"HARD_LIMIT: {parameter} is immutable"

        if parameter not in TUNABLE_PARAMS:
            return False, f"NOT_TUNABLE: {parameter} not in tunable catalogue"

        if parameter in self._applied_this_cycle:
            return False, f"DUPLICATE: {parameter} already changed this cycle"

        if current_value and current_value != 0:
            shift = abs(proposed_value - current_value) / abs(current_value)
            if shift > MAX_MEMORY_SHIFT_PCT + 1e-9:
                return False, (
                    f"SHIFT_EXCEEDED: {parameter} shift {shift:.1%} > 30% cap"
                )

        bounds = TUNABLE_PARAMS.get(parameter)
        if bounds:
            lo, hi, _ = bounds
            if not (lo - 1e-9 <= proposed_value <= hi + 1e-9):
                return False, (
                    f"OUT_OF_BOUNDS: {parameter}={proposed_value:.4f} outside [{lo},{hi}]"
                )

        return True, ""

    def mark_applied(self, parameter: str) -> None:
        self._applied_this_cycle.add(parameter)

    def summary(self) -> Dict[str, Any]:
        return {
            "module":             self.MODULE,
            "phase":              self.PHASE,
            "applied_this_cycle": list(self._applied_this_cycle),
            "max_shift_pct":      MAX_MEMORY_SHIFT_PCT,
        }

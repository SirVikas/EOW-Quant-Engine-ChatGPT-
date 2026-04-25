"""
FTD-030B — memory_guard.py
Safety enforcement for memory-influenced corrections.

Rules (ALL mandatory):
  1. HARD_LIMITS are NEVER touched
  2. Memory cannot shift any parameter by more than 30% of its max_change_pct
  3. No duplicate in-flight parameter changes
  4. PolicyGuard final veto (enforced upstream — checked here for guard completeness)

Any violation returns GuardResult(allowed=False, reason=...).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from core.self_correction.correction_proposal import HARD_LIMITS, TUNABLE_PARAMS, max_change_pct

MAX_MEMORY_SHIFT_FRACTION = 0.30   # memory can shift at most 30% of the param's allowed delta


@dataclass
class GuardResult:
    allowed:  bool
    reason:   str = ""
    code:     str = ""

    @classmethod
    def ok(cls) -> "GuardResult":
        return cls(allowed=True, reason="ALL_CLEAR", code="OK")

    @classmethod
    def block(cls, reason: str, code: str = "BLOCKED") -> "GuardResult":
        return cls(allowed=False, reason=reason, code=code)


class MemoryGuard:
    """
    Validates that a memory-suggested parameter change is safe to apply.
    Must be called before any memory influence is blended into the final proposal.
    """

    def __init__(self):
        self._in_flight: Set[str] = set()   # parameters currently being adjusted

    # ── Public API ────────────────────────────────────────────────────────────

    def check(
        self,
        parameter:      str,
        current_value:  float,
        proposed_value: float,
        current_params: Optional[Dict[str, float]] = None,
    ) -> GuardResult:
        """
        Check all memory guard rules for a proposed change.

        Args:
            parameter:      Name of the tunable parameter being changed
            current_value:  Current live value
            proposed_value: Memory-suggested target value
            current_params: Full live params dict (for duplicate detection)

        Returns:
            GuardResult(allowed=True)  → safe to apply
            GuardResult(allowed=False) → memory influence must be blocked
        """
        # Rule 1: Hard limits are absolutely immutable
        if parameter in HARD_LIMITS:
            return GuardResult.block(
                f"HARD_LIMIT: {parameter} is immutable",
                code="HARD_LIMIT_VIOLATION",
            )

        # Rule 2: Parameter must be in the tunable set
        if parameter not in TUNABLE_PARAMS:
            return GuardResult.block(
                f"NOT_TUNABLE: {parameter} is not in TUNABLE_PARAMS",
                code="NOT_TUNABLE",
            )

        # Rule 3: Max memory shift ≤ 30% of allowed delta
        allowed_full_delta = max_change_pct(parameter) * current_value
        actual_delta       = abs(proposed_value - current_value)
        max_memory_delta   = allowed_full_delta * MAX_MEMORY_SHIFT_FRACTION

        if actual_delta > max_memory_delta:
            return GuardResult.block(
                f"SHIFT_TOO_LARGE: {parameter} delta={actual_delta:.6f} "
                f"> memory_cap={max_memory_delta:.6f} (30% of allowed)",
                code="SHIFT_CAP_EXCEEDED",
            )

        # Rule 4: No duplicate in-flight changes
        if parameter in self._in_flight:
            return GuardResult.block(
                f"DUPLICATE_INFLIGHT: {parameter} already has a pending change",
                code="DUPLICATE_CHANGE",
            )

        return GuardResult.ok()

    def register_inflight(self, parameter: str) -> None:
        """Mark a parameter as having an in-flight change."""
        self._in_flight.add(parameter)

    def clear_inflight(self, parameter: str) -> None:
        """Clear in-flight status after resolution."""
        self._in_flight.discard(parameter)

    def clear_all_inflight(self) -> None:
        self._in_flight.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "in_flight_params": list(self._in_flight),
            "hard_limits":      list(HARD_LIMITS.keys()),
            "max_shift_pct":    MAX_MEMORY_SHIFT_FRACTION * 100,
            "module": "MEMORY_GUARD",
            "phase":  "030B",
        }

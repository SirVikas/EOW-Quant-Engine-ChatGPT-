"""
FTD-030B — Memory Guard (spec §PART 5)

Enforces:
  - Hard limits NEVER touched (Q15)
  - Max 30% parameter shift per suggestion
  - No duplicate changes (idempotent guard)
  - PolicyGuard final veto (integration with FTD-029 bounds)
"""
from __future__ import annotations
from typing import Any, Dict, List, Set, Tuple

from core.self_correction.correction_proposal import HARD_LIMITS, TUNABLE_PARAMS

MAX_SHIFT_PCT   = 0.30    # max 30% parameter shift (spec §PART 5)


class MemoryGuard:
    """
    Validates and filters suggestions before they reach the live system.
    Stateful: tracks applied changes this session to prevent duplicates.
    """

    def __init__(self):
        self._applied_this_session: Set[str] = set()

    # ── Public ────────────────────────────────────────────────────────────────

    def validate(
        self,
        suggestions: List[Dict[str, Any]],
        policy_ok:   bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns (allowed, blocked) lists.

        Blocks when:
          - Parameter is in HARD_LIMITS
          - Shift exceeds MAX_SHIFT_PCT
          - Duplicate in this session
          - policy_ok is False (PolicyGuard veto)
        """
        allowed: List[Dict[str, Any]] = []
        blocked: List[Dict[str, Any]] = []

        if not policy_ok:
            for s in suggestions:
                blocked.append({**s, "guard_reason": "POLICY_VETO"})
            return [], blocked

        for s in suggestions:
            param   = s["parameter"]
            cur     = s["current_value"]
            prop    = s["suggested_value"]

            # Hard limit check (Q15)
            if param in HARD_LIMITS:
                blocked.append({**s, "guard_reason": "HARD_LIMIT"})
                continue

            # Shift magnitude check (spec §PART 5: max 30%)
            if cur != 0:
                shift_pct = abs(prop - cur) / abs(cur)
                if shift_pct > MAX_SHIFT_PCT:
                    blocked.append({**s, "guard_reason": f"MAX_SHIFT_EXCEEDED({shift_pct:.1%})"})
                    continue

            # Duplicate check
            dup_key = f"{param}:{s['direction']}"
            if dup_key in self._applied_this_session:
                blocked.append({**s, "guard_reason": "DUPLICATE"})
                continue

            self._applied_this_session.add(dup_key)
            allowed.append({**s, "guard_reason": "PASSED"})

        return allowed, blocked

    def reset_session(self) -> None:
        """Clear duplicate tracker for new trading session."""
        self._applied_this_session.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "applied_this_session": list(self._applied_this_session),
            "session_count": len(self._applied_this_session),
            "max_shift_pct": MAX_SHIFT_PCT,
        }

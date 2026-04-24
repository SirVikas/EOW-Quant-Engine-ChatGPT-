"""
FTD-029 Part 4b — Collision Handler

When multiple change plans conflict (same param, or mutually exclusive changes):
  - Apply the higher-priority plan
  - Queue lower-priority conflicting plans for next correction cycle
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Tuple


class CollisionHandler:
    """
    Detects parameter conflicts among proposed change plans and splits them
    into safe (non-conflicting) and queued (deferred to next cycle) lists.
    """

    MODULE = "COLLISION_HANDLER"
    PHASE  = "029"

    def __init__(self):
        self._queue: List[Dict[str, Any]] = []

    def resolve(
        self,
        plans: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Args:
            plans: ordered list of change plans (highest priority first)

        Returns:
            safe:   plans with no conflicts — apply immediately
            queued: lower-priority conflicting plans — deferred to next cycle
        """
        seen_params: Dict[str, int] = {}   # param → index of first accepted plan
        safe:   List[Dict[str, Any]] = []
        queued: List[Dict[str, Any]] = []

        for plan in plans:
            param = plan.get("parameter", "")

            if param in seen_params:
                # Conflict: same parameter proposed by lower-priority issue
                queued.append({**plan, "_queued_reason": f"conflicts with plan at index {seen_params[param]}"})
            else:
                seen_params[param] = len(safe)
                safe.append(plan)

        # Persist queue for next cycle
        self._queue = queued

        return safe, queued

    def pending_queue(self) -> List[Dict[str, Any]]:
        """Returns plans queued from previous cycle."""
        return list(self._queue)

    def clear_queue(self) -> None:
        self._queue.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "module":       self.MODULE,
            "phase":        self.PHASE,
            "queued_count": len(self._queue),
            "queued_params": [p.get("parameter") for p in self._queue],
            "snapshot_ts":  int(time.time() * 1000),
        }

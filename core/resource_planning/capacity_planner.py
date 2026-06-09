"""Capacity Planner — plans capacity against demand."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CapacityPlan:
    plan_id: str
    resource_type: str
    current_capacity: float
    required_capacity: float
    gap_units: float
    gap_pct: float
    plan_date: datetime


class CapacityPlanner:
    def __init__(self):
        self._lock = threading.RLock()
        self._plans: dict[str, CapacityPlan] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CAP-{self._counter:03d}"

    def record_plan(self, resource_type: str, current_capacity: float,
                    required_capacity: float) -> CapacityPlan:
        with self._lock:
            gap = required_capacity - current_capacity
            gap_pct = (gap / required_capacity * 100) if required_capacity > 0 else 0.0
            plan = CapacityPlan(
                plan_id=self._next_id(),
                resource_type=resource_type,
                current_capacity=current_capacity,
                required_capacity=required_capacity,
                gap_units=gap,
                gap_pct=round(gap_pct, 1),
                plan_date=datetime.utcnow(),
            )
            self._plans[plan.plan_id] = plan
            return plan

    def capacity_gaps(self) -> list[dict]:
        with self._lock:
            return [
                {"plan_id": p.plan_id, "resource_type": p.resource_type,
                 "gap_units": p.gap_units, "gap_pct": p.gap_pct}
                for p in self._plans.values() if p.gap_units > 0
            ]

    def capacity_summary(self) -> dict:
        with self._lock:
            gaps = [p for p in self._plans.values() if p.gap_units > 0]
            return {
                "total_plans": len(self._plans),
                "plans_with_gaps": len(gaps),
                "resource_types": list({p.resource_type for p in self._plans.values()}),
            }


capacity_planner = CapacityPlanner()

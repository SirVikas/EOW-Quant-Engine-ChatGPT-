"""Resource Cost Engine — tracks resource costs."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


ResourceType = Literal["COMPUTE", "STORAGE", "API", "INTELLIGENCE"]


@dataclass
class CostRecord:
    cost_id: str
    resource_type: ResourceType
    unit_cost: float
    usage_units: float
    total_cost: float
    period: str
    recorded_at: datetime = field(default_factory=datetime.utcnow)


class ResourceCostEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[CostRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CST-{self._counter:03d}"

    def record_cost(self, resource_type: ResourceType, unit_cost: float, usage_units: float, period: str) -> CostRecord:
        with self._lock:
            rec = CostRecord(
                cost_id=self._next_id(),
                resource_type=resource_type,
                unit_cost=unit_cost,
                usage_units=usage_units,
                total_cost=unit_cost * usage_units,
                period=period,
            )
            self._records.append(rec)
            return rec

    def cost_by_type(self) -> dict:
        with self._lock:
            result: dict = {}
            for r in self._records:
                result[r.resource_type] = result.get(r.resource_type, 0.0) + r.total_cost
            return result

    def total_spend(self) -> float:
        with self._lock:
            return sum(r.total_cost for r in self._records)


resource_cost_engine = ResourceCostEngine()

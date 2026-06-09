"""Organization Registry — registry of org units/departments."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OrgUnit:
    unit_id: str
    name: str
    unit_type: str
    parent_id: Optional[str]
    head_agent_id: Optional[str]
    created_at: datetime


class OrganizationRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._units: dict[str, OrgUnit] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ORG-{self._counter:03d}"

    def create_unit(self, name: str, unit_type: str,
                    parent_id: Optional[str] = None) -> OrgUnit:
        with self._lock:
            unit = OrgUnit(
                unit_id=self._next_id(),
                name=name,
                unit_type=unit_type,
                parent_id=parent_id,
                head_agent_id=None,
                created_at=datetime.utcnow(),
            )
            self._units[unit.unit_id] = unit
            return unit

    def assign_head(self, unit_id: str, agent_id: str) -> bool:
        with self._lock:
            unit = self._units.get(unit_id)
            if unit:
                unit.head_agent_id = agent_id
                return True
            return False

    def org_tree(self) -> list[dict]:
        with self._lock:
            return [
                {"unit_id": u.unit_id, "name": u.name, "unit_type": u.unit_type,
                 "parent_id": u.parent_id, "head_agent_id": u.head_agent_id}
                for u in self._units.values()
            ]

    def unit_summary(self) -> dict:
        with self._lock:
            by_type: dict[str, int] = {}
            for u in self._units.values():
                by_type[u.unit_type] = by_type.get(u.unit_type, 0) + 1
            return {"total_units": len(self._units), "by_type": by_type}


organization_registry = OrganizationRegistry()

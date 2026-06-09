"""
PHOENIX PCAO — Priority Director
Directs strategic priorities to specific layers with deadlines and weights.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
import uuid


@dataclass
class DirectedPriority:
    priority_id: str
    objective: str
    source: str     # STRATEGIC/OPERATIONAL/RISK/LEARNING
    target_layer: str
    deadline_days: int
    weight: float
    status: str     # ACTIVE/COMPLETED/CANCELLED
    created_at: str


class PriorityDirector:
    def __init__(self):
        self._lock = threading.RLock()
        self._priorities: Dict[str, DirectedPriority] = {}

    def direct(
        self,
        objective: str,
        source: str,
        target_layer: str,
        deadline_days: int = 30,
        weight: float = 0.5,
    ) -> dict:
        priority_id = f"PRI-{uuid.uuid4().hex[:8].upper()}"
        dp = DirectedPriority(
            priority_id=priority_id,
            objective=objective,
            source=source,
            target_layer=target_layer,
            deadline_days=deadline_days,
            weight=weight,
            status="ACTIVE",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._priorities[priority_id] = dp
        return asdict(dp)

    def active_priorities(self) -> list:
        with self._lock:
            items = [p for p in self._priorities.values() if p.status == "ACTIVE"]
        items.sort(key=lambda x: x.weight, reverse=True)
        return [asdict(p) for p in items]

    def complete(self, priority_id: str) -> dict:
        with self._lock:
            p = self._priorities.get(priority_id)
            if p:
                p.status = "COMPLETED"
                return asdict(p)
        return {"error": f"{priority_id} not found"}

    def priority_load(self, target_layer: str) -> float:
        with self._lock:
            return sum(
                p.weight
                for p in self._priorities.values()
                if p.target_layer == target_layer and p.status == "ACTIVE"
            )

    def director_stats(self) -> dict:
        with self._lock:
            items = list(self._priorities.values())
        by_layer: Dict[str, int] = {}
        for p in items:
            if p.status == "ACTIVE":
                by_layer[p.target_layer] = by_layer.get(p.target_layer, 0) + 1
        return {
            "total": len(items),
            "active": sum(1 for p in items if p.status == "ACTIVE"),
            "completed": sum(1 for p in items if p.status == "COMPLETED"),
            "cancelled": sum(1 for p in items if p.status == "CANCELLED"),
            "by_layer": by_layer,
        }


priority_director = PriorityDirector()

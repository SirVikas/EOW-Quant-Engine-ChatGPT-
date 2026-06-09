"""
PHOENIX PCAO — Resource Allocator
Allocates and rebalances priority resources across layers.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
import uuid


@dataclass
class Allocation:
    alloc_id: str
    layer_id: str
    focus_area: str
    allocated_priority: float  # 0-100
    rationale: str
    allocated_at: str


class ResourceAllocator:
    def __init__(self):
        self._lock = threading.RLock()
        self._allocations: Dict[str, Allocation] = {}

    def allocate(
        self,
        layer_id: str,
        focus_area: str,
        allocated_priority: float,
        rationale: str,
    ) -> dict:
        alloc_id = f"ALLOC-{uuid.uuid4().hex[:8].upper()}"
        alloc = Allocation(
            alloc_id=alloc_id,
            layer_id=layer_id,
            focus_area=focus_area,
            allocated_priority=allocated_priority,
            rationale=rationale,
            allocated_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._allocations[alloc_id] = alloc
        return asdict(alloc)

    def current_allocations(self) -> list:
        with self._lock:
            return [asdict(a) for a in self._allocations.values()]

    def rebalance(self) -> dict:
        try:
            from core.pccp.resource_governor import resource_governor
            summary = resource_governor.rebalance_resources()
        except Exception as e:
            summary = {"note": f"Resource governor unavailable: {e}"}
        return {"rebalance_result": summary, "rebalanced_at": datetime.now(timezone.utc).isoformat()}

    def allocation_report(self) -> dict:
        with self._lock:
            items = list(self._allocations.values())
        by_layer: Dict[str, float] = {}
        for a in items:
            by_layer[a.layer_id] = by_layer.get(a.layer_id, 0) + a.allocated_priority
        return {
            "total_allocations": len(items),
            "by_layer": by_layer,
            "total_priority_allocated": sum(a.allocated_priority for a in items),
        }


resource_allocator = ResourceAllocator()

"""Capital allocator — strategy allocation tracking."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class AllocationRecord:
    record_id: str
    strategy_name: str
    allocated_pct: float
    max_drawdown_limit_pct: float
    expected_return_pct: float
    allocation_rationale: str
    status: str
    created_at: str


class CapitalAllocator:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list = []
        self._counter = 0

    def allocate(self, strategy_name: str, allocated_pct: float, max_drawdown_limit_pct: float,
                 expected_return_pct: float, rationale: str) -> dict:
        with self._lock:
            self._counter += 1
            r = AllocationRecord(
                record_id=f"ALLOC-{self._counter:04d}",
                strategy_name=strategy_name,
                allocated_pct=allocated_pct,
                max_drawdown_limit_pct=max_drawdown_limit_pct,
                expected_return_pct=expected_return_pct,
                allocation_rationale=rationale,
                status="ACTIVE",
                created_at=datetime.utcnow().isoformat(),
            )
            self._records.append(r)
            return asdict(r)

    def suspend(self, strategy_name: str, reason: str) -> bool:
        with self._lock:
            for r in reversed(self._records):
                if r.strategy_name == strategy_name and r.status == "ACTIVE":
                    r.status = "SUSPENDED"
                    return True
            return False

    def reduce(self, strategy_name: str, new_pct: float, reason: str) -> bool:
        with self._lock:
            for r in reversed(self._records):
                if r.strategy_name == strategy_name and r.status == "ACTIVE":
                    r.allocated_pct = new_pct
                    r.status = "REDUCED"
                    return True
            return False

    def active_allocations(self) -> list:
        with self._lock:
            return [asdict(r) for r in self._records if r.status == "ACTIVE"]

    def total_allocated_pct(self) -> float:
        with self._lock:
            return sum(r.allocated_pct for r in self._records if r.status == "ACTIVE")

    def allocation_report(self) -> dict:
        with self._lock:
            active = [r for r in self._records if r.status == "ACTIVE"]
            suspended = [r for r in self._records if r.status == "SUSPENDED"]
            total = sum(r.allocated_pct for r in active)
            return {
                "total_allocated_pct": total,
                "active_strategies": len(active),
                "suspended_strategies": len(suspended),
                "over_allocated": total > 100,
            }


capital_allocator = CapitalAllocator()

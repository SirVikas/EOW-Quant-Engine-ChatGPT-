"""Institutional Cost Engine — tracks total cost of running PHOENIX."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CostEntry:
    cost_entry_id: str
    cost_category: str
    amount: float
    period: str
    recorded_at: datetime


class InstitutionalCostEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._entries: dict[str, CostEntry] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ICE-{self._counter:03d}"

    def record(self, cost_category: str, amount: float, period: str) -> CostEntry:
        with self._lock:
            entry = CostEntry(
                cost_entry_id=self._next_id(),
                cost_category=cost_category,
                amount=amount,
                period=period,
                recorded_at=datetime.utcnow(),
            )
            self._entries[entry.cost_entry_id] = entry
            return entry

    def cost_by_category(self) -> dict:
        with self._lock:
            result: dict[str, float] = {}
            for e in self._entries.values():
                result[e.cost_category] = result.get(e.cost_category, 0.0) + e.amount
            return result

    def total_cost(self, period: Optional[str] = None) -> float:
        with self._lock:
            entries = self._entries.values()
            if period:
                entries = [e for e in entries if e.period == period]
            return sum(e.amount for e in entries)


institutional_cost_engine = InstitutionalCostEngine()

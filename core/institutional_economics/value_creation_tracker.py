"""Value Creation Tracker — tracks value created by PHOENIX."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ValueRecord:
    value_id: str
    value_type: str
    estimated_value: float
    period: str
    evidence: str
    recorded_at: datetime


class ValueCreationTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, ValueRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"VCT-{self._counter:03d}"

    def record(self, value_type: str, estimated_value: float,
               period: str, evidence: str) -> ValueRecord:
        with self._lock:
            rec = ValueRecord(
                value_id=self._next_id(),
                value_type=value_type,
                estimated_value=estimated_value,
                period=period,
                evidence=evidence,
                recorded_at=datetime.utcnow(),
            )
            self._records[rec.value_id] = rec
            return rec

    def value_by_type(self) -> dict:
        with self._lock:
            result: dict[str, float] = {}
            for r in self._records.values():
                result[r.value_type] = result.get(r.value_type, 0.0) + r.estimated_value
            return result

    def total_value(self, period: Optional[str] = None) -> float:
        with self._lock:
            records = self._records.values()
            if period:
                records = [r for r in records if r.period == period]
            return sum(r.estimated_value for r in records)


value_creation_tracker = ValueCreationTracker()

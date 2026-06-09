"""Capital Efficiency Tracker — measures capital utilization improvements from recommendations."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class EfficiencyRecord:
    record_id: str
    rec_id: str
    capital_utilization_before: float
    capital_utilization_after: float
    efficiency_delta: float
    recovery_speed_improvement: float
    recorded_at: float


class CapitalEfficiencyTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, EfficiencyRecord] = {}
        self._counter = 0

    def record(self, rec_id: str, util_before: float, util_after: float,
               recovery_improvement: float = 0.0) -> str:
        with self._lock:
            self._counter += 1
            rid = f"CET-{self._counter:04d}"
            delta = util_after - util_before
            self._records[rec_id] = EfficiencyRecord(
                record_id=rid,
                rec_id=rec_id,
                capital_utilization_before=util_before,
                capital_utilization_after=util_after,
                efficiency_delta=round(delta, 4),
                recovery_speed_improvement=recovery_improvement,
                recorded_at=time.time(),
            )
            return rid

    def all_records(self, limit: int = 50) -> list:
        with self._lock:
            recs = list(self._records.values())
            return [asdict(r) for r in recs[-limit:]]

    def efficiency_stats(self) -> dict:
        with self._lock:
            recs = list(self._records.values())
            if not recs:
                return {"total_records": 0, "avg_efficiency_delta": 0,
                        "avg_recovery_improvement": 0, "positive_impact_pct": 0}
            avg_delta = sum(r.efficiency_delta for r in recs) / len(recs)
            avg_rec = sum(r.recovery_speed_improvement for r in recs) / len(recs)
            positive = sum(1 for r in recs if r.efficiency_delta > 0)
            return {
                "total_records": len(recs),
                "avg_efficiency_delta": round(avg_delta, 4),
                "avg_recovery_improvement": round(avg_rec, 4),
                "positive_impact_pct": round(positive / len(recs) * 100, 2),
            }


capital_efficiency_tracker = CapitalEfficiencyTracker()

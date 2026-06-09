"""Resource ROI Tracker — tracks ROI per resource type."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ROIRecord:
    roi_id: str
    resource_type: str
    investment: float
    return_value: float
    roi_pct: float
    period: str
    recorded_at: datetime = field(default_factory=datetime.utcnow)


class ResourceROITracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[ROIRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ROI-{self._counter:03d}"

    def record_roi(self, resource_type: str, investment: float, return_value: float, period: str) -> ROIRecord:
        with self._lock:
            roi_pct = ((return_value - investment) / investment * 100) if investment else 0.0
            rec = ROIRecord(self._next_id(), resource_type, investment, return_value, round(roi_pct, 2), period)
            self._records.append(rec)
            return rec

    def roi_by_type(self) -> dict:
        with self._lock:
            result: dict = {}
            for r in self._records:
                if r.resource_type not in result:
                    result[r.resource_type] = []
                result[r.resource_type].append(r.roi_pct)
            return {k: round(sum(v) / len(v), 2) for k, v in result.items()}

    def best_roi_resources(self) -> List[dict]:
        with self._lock:
            by_type = self.roi_by_type()
            sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
            return [{"resource_type": k, "avg_roi_pct": v} for k, v in sorted_types]


resource_roi_tracker = ResourceROITracker()

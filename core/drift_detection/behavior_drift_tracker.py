"""
Behavior drift tracker — detects when system component behavior deviates from baseline.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class BehaviorDrift:
    drift_id: str
    component: str
    behavior_metric: str
    baseline_value: float
    current_value: float
    drift_pct: float
    drift_status: str   # STABLE / DRIFTING / CRITICAL
    detected_at: str


class BehaviorDriftTracker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[BehaviorDrift] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"BDT-{self._counter:03d}"

    def record(
        self,
        component: str,
        behavior_metric: str,
        baseline_value: float,
        current_value: float,
    ) -> BehaviorDrift:
        drift_pct = round(
            abs(current_value - baseline_value) / abs(baseline_value) * 100, 2
        ) if baseline_value != 0 else 0.0

        if drift_pct >= 30:
            status = "CRITICAL"
        elif drift_pct >= 10:
            status = "DRIFTING"
        else:
            status = "STABLE"

        with self._lock:
            rec = BehaviorDrift(
                drift_id=self._next_id(),
                component=component,
                behavior_metric=behavior_metric,
                baseline_value=baseline_value,
                current_value=current_value,
                drift_pct=drift_pct,
                drift_status=status,
                detected_at=datetime.utcnow().isoformat(),
            )
            self._records.append(rec)
            return rec

    def drifting_components(self) -> List[BehaviorDrift]:
        with self._lock:
            return [r for r in self._records if r.drift_status in ("DRIFTING", "CRITICAL")]

    def drift_summary(self) -> dict:
        with self._lock:
            return {
                "total_tracked": len(self._records),
                "stable": sum(1 for r in self._records if r.drift_status == "STABLE"),
                "drifting": sum(1 for r in self._records if r.drift_status == "DRIFTING"),
                "critical": sum(1 for r in self._records if r.drift_status == "CRITICAL"),
                "components": list({r.component for r in self._records if r.drift_status != "STABLE"}),
            }


behavior_drift_tracker = BehaviorDriftTracker()

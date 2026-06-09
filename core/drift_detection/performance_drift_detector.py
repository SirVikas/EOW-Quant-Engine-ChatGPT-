"""
Performance drift detector — compares current vs baseline performance metrics.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class PerformanceDrift:
    det_id: str
    metric_name: str
    baseline_period: str
    current_period: str
    baseline_value: float
    current_value: float
    drift_pct: float
    alert_triggered: bool
    detected_at: str


class PerformanceDriftDetector:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[PerformanceDrift] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"PDD-{self._counter:03d}"

    def detect(
        self,
        metric_name: str,
        baseline_period: str,
        baseline_value: float,
        current_period: str,
        current_value: float,
        alert_threshold_pct: float = 20.0,
    ) -> PerformanceDrift:
        drift_pct = round(
            abs(current_value - baseline_value) / abs(baseline_value) * 100, 2
        ) if baseline_value != 0 else 0.0
        alert = drift_pct >= alert_threshold_pct

        with self._lock:
            rec = PerformanceDrift(
                det_id=self._next_id(),
                metric_name=metric_name,
                baseline_period=baseline_period,
                current_period=current_period,
                baseline_value=baseline_value,
                current_value=current_value,
                drift_pct=drift_pct,
                alert_triggered=alert,
                detected_at=datetime.utcnow().isoformat(),
            )
            self._records.append(rec)
            return rec

    def triggered_alerts(self) -> List[PerformanceDrift]:
        with self._lock:
            return [r for r in self._records if r.alert_triggered]

    def performance_drift_report(self) -> dict:
        with self._lock:
            return {
                "total_detections": len(self._records),
                "alerts_triggered": sum(1 for r in self._records if r.alert_triggered),
                "avg_drift_pct": round(
                    sum(r.drift_pct for r in self._records) / len(self._records), 2
                ) if self._records else 0.0,
                "metrics": [
                    {
                        "metric_name": r.metric_name,
                        "drift_pct": r.drift_pct,
                        "alert_triggered": r.alert_triggered,
                    }
                    for r in self._records
                ],
            }


performance_drift_detector = PerformanceDriftDetector()

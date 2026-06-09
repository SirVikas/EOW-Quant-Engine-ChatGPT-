"""SLO Tracker — tracks SLO compliance measurements."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


MetricType = Literal["AVAILABILITY", "LATENCY", "THROUGHPUT"]


@dataclass
class SLOMeasurement:
    slo_id: str
    service_name: str
    metric_type: MetricType
    target_value: float
    actual_value: float
    compliant: bool
    measured_at: datetime = field(default_factory=datetime.utcnow)


class SLOTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._measurements: List[SLOMeasurement] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SLO-{self._counter:03d}"

    def record_measurement(self, service_name: str, metric_type: MetricType, target: float, actual: float) -> SLOMeasurement:
        with self._lock:
            # For LATENCY, compliant means actual <= target; for others actual >= target
            compliant = actual <= target if metric_type == "LATENCY" else actual >= target
            rec = SLOMeasurement(self._next_id(), service_name, metric_type, target, actual, compliant)
            self._measurements.append(rec)
            return rec

    def non_compliant_slos(self) -> List[dict]:
        with self._lock:
            return [vars(m) for m in self._measurements if not m.compliant]

    def compliance_rate_pct(self) -> float:
        with self._lock:
            if not self._measurements:
                return 100.0
            compliant = sum(1 for m in self._measurements if m.compliant)
            return round(compliant / len(self._measurements) * 100, 2)


slo_tracker = SLOTracker()

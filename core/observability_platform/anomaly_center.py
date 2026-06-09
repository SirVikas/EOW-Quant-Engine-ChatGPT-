"""Anomaly detection center for cross-layer metrics."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Anomaly:
    anomaly_id: str
    layer: str
    metric_name: str
    expected_range: tuple
    observed_value: float
    severity: str
    detected_at: str
    resolved: bool = False


class AnomalyCenter:
    THRESHOLDS = {
        "health_score": (40, 100),
        "avg_trust_score": (0.3, 1.0),
        "economic_health_score": (30, 100),
        "constitutional_health_score": (0.5, 1.0),
        "active_failovers": (0, 2),
        "degraded_layers": (0, 3),
    }

    def __init__(self):
        self._lock = threading.RLock()
        self._anomalies: list = []
        self._counter = 0

    def _severity(self, metric_name: str, value: float) -> str:
        lo, hi = self.THRESHOLDS.get(metric_name, (None, None))
        if lo is None:
            return "INFO"
        outside = value < lo or value > hi
        if not outside:
            return "INFO"
        # distance from range
        dist = max(lo - value, value - hi, 0)
        span = max(hi - lo, 1)
        if dist / span > 0.3:
            return "CRITICAL"
        return "WARNING"

    def scan(self) -> dict:
        from core.observability_platform.real_time_metrics_bus import real_time_metrics_bus as bus
        all_latest = bus.all_latest()
        found = []
        with self._lock:
            for layer, metrics in all_latest.items():
                for metric_name, value in metrics.items():
                    if metric_name not in self.THRESHOLDS:
                        continue
                    lo, hi = self.THRESHOLDS[metric_name]
                    if value < lo or value > hi:
                        sev = self._severity(metric_name, value)
                        self._counter += 1
                        a = Anomaly(
                            anomaly_id=f"ANO-{self._counter:03d}",
                            layer=layer,
                            metric_name=metric_name,
                            expected_range=(lo, hi),
                            observed_value=value,
                            severity=sev,
                            detected_at=datetime.utcnow().isoformat(),
                        )
                        self._anomalies.append(a)
                        found.append(asdict(a))
        critical = sum(1 for a in found if a["severity"] == "CRITICAL")
        warning = sum(1 for a in found if a["severity"] == "WARNING")
        return {"anomalies_found": len(found), "critical": critical, "warning": warning, "anomalies": found}

    def all_anomalies(self, resolved: bool = False) -> list:
        with self._lock:
            return [asdict(a) for a in self._anomalies if a.resolved == resolved]

    def resolve(self, anomaly_id: str) -> bool:
        with self._lock:
            for a in self._anomalies:
                if a.anomaly_id == anomaly_id:
                    a.resolved = True
                    return True
            return False

    def anomaly_stats(self) -> dict:
        with self._lock:
            total = len(self._anomalies)
            active = sum(1 for a in self._anomalies if not a.resolved)
            resolved = total - active
            by_sev: dict = {}
            for a in self._anomalies:
                by_sev[a.severity] = by_sev.get(a.severity, 0) + 1
            return {"total": total, "active": active, "resolved": resolved, "by_severity": by_sev}


anomaly_center = AnomalyCenter()

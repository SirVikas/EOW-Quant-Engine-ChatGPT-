"""
Drift alert generator — creates and tracks drift alerts across all drift dimensions.
"""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class DriftAlert:
    alert_id: str
    alert_type: str    # PERFORMANCE / BEHAVIOR / STRATEGY / ECONOMIC
    severity: str      # CRITICAL / HIGH / MEDIUM / LOW
    description: str
    component: str
    acknowledged: bool
    generated_at: str


class AlertGenerator:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._alerts: List[DriftAlert] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DRF-{self._counter:03d}"

    def generate(
        self,
        alert_type: str,
        severity: str,
        description: str,
        component: str,
    ) -> DriftAlert:
        with self._lock:
            alert = DriftAlert(
                alert_id=self._next_id(),
                alert_type=alert_type,
                severity=severity,
                description=description,
                component=component,
                acknowledged=False,
                generated_at=datetime.utcnow().isoformat(),
            )
            self._alerts.append(alert)
            return alert

    def acknowledge(self, alert_id: str) -> bool:
        with self._lock:
            for a in self._alerts:
                if a.alert_id == alert_id:
                    a.acknowledged = True
                    return True
            return False

    def active_alerts(self) -> List[DriftAlert]:
        with self._lock:
            return [a for a in self._alerts if not a.acknowledged]

    def alert_stats(self) -> dict:
        with self._lock:
            active = [a for a in self._alerts if not a.acknowledged]
            return {
                "total_generated": len(self._alerts),
                "active": len(active),
                "acknowledged": len(self._alerts) - len(active),
                "by_severity": {
                    "CRITICAL": sum(1 for a in active if a.severity == "CRITICAL"),
                    "HIGH": sum(1 for a in active if a.severity == "HIGH"),
                    "MEDIUM": sum(1 for a in active if a.severity == "MEDIUM"),
                    "LOW": sum(1 for a in active if a.severity == "LOW"),
                },
                "by_type": {
                    "PERFORMANCE": sum(1 for a in active if a.alert_type == "PERFORMANCE"),
                    "BEHAVIOR": sum(1 for a in active if a.alert_type == "BEHAVIOR"),
                    "STRATEGY": sum(1 for a in active if a.alert_type == "STRATEGY"),
                    "ECONOMIC": sum(1 for a in active if a.alert_type == "ECONOMIC"),
                },
            }


alert_generator = AlertGenerator()

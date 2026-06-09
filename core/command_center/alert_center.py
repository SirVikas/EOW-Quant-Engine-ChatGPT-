"""Alert center — command center alert management."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Alert:
    alert_id: str
    title: str
    source_system: str
    severity: str
    message: str
    action_required: bool
    created_at: str
    acknowledged: bool
    acknowledged_by: str


class AlertCenter:
    def __init__(self):
        self._lock = threading.RLock()
        self._alerts: list = []
        self._counter = 0

    def raise_alert(self, title: str, source_system: str, severity: str, message: str,
                    action_required: bool = False) -> str:
        with self._lock:
            self._counter += 1
            alert_id = f"ALC-{self._counter:04d}"
            a = Alert(
                alert_id=alert_id, title=title, source_system=source_system,
                severity=severity, message=message, action_required=action_required,
                created_at=datetime.utcnow().isoformat(), acknowledged=False, acknowledged_by="",
            )
            self._alerts.append(a)
            return alert_id

    def acknowledge(self, alert_id: str, acknowledged_by: str) -> bool:
        with self._lock:
            for a in self._alerts:
                if a.alert_id == alert_id:
                    a.acknowledged = True
                    a.acknowledged_by = acknowledged_by
                    return True
            return False

    def active_alerts(self, severity_filter: Optional[str] = None) -> list:
        with self._lock:
            result = [a for a in self._alerts if not a.acknowledged]
            if severity_filter:
                result = [a for a in result if a.severity == severity_filter]
            return [asdict(a) for a in result]

    def alert_stats(self) -> dict:
        with self._lock:
            total = len(self._alerts)
            active = sum(1 for a in self._alerts if not a.acknowledged)
            acknowledged = total - active
            by_sev: dict = {}
            for a in self._alerts:
                by_sev[a.severity] = by_sev.get(a.severity, 0) + 1
            emergency_count = by_sev.get("EMERGENCY", 0)
            return {"total": total, "active": active, "acknowledged": acknowledged,
                    "by_severity": by_sev, "emergency_count": emergency_count}


alert_center = AlertCenter()

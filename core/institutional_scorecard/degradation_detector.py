"""Degradation detector — institutional KPI threshold alerting."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DegradationAlert:
    alert_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    detected_at: str
    resolved: bool = False


class DegradationDetector:
    # (warning_threshold, critical_threshold)
    DEGRADATION_THRESHOLDS = {
        "TRUST_SCORE": (60, 40),
        "GOVERNANCE_COMPLIANCE": (80, 60),
        "SAFETY_SCORE": (75, 55),
        "ECONOMIC_ACCURACY": (50, 30),
    }

    def __init__(self):
        self._lock = threading.RLock()
        self._alerts: list = []
        self._counter = 0

    def scan(self) -> dict:
        from core.institutional_scorecard.institutional_kpi_tracker import institutional_kpi_tracker
        kpis = institutional_kpi_tracker.all_kpis()
        found = []
        with self._lock:
            for kpi in kpis:
                name = kpi["name"]
                value = kpi["current_value"]
                if name not in self.DEGRADATION_THRESHOLDS:
                    continue
                warn_thresh, crit_thresh = self.DEGRADATION_THRESHOLDS[name]
                if value <= crit_thresh:
                    sev = "CRITICAL"
                    thresh = crit_thresh
                elif value <= warn_thresh:
                    sev = "WARNING"
                    thresh = warn_thresh
                else:
                    continue
                self._counter += 1
                a = DegradationAlert(
                    alert_id=f"DEG-{self._counter:03d}",
                    metric_name=name,
                    current_value=value,
                    threshold=thresh,
                    severity=sev,
                    detected_at=datetime.utcnow().isoformat(),
                )
                self._alerts.append(a)
                found.append(asdict(a))
        critical = sum(1 for a in found if a["severity"] == "CRITICAL")
        warning = sum(1 for a in found if a["severity"] == "WARNING")
        return {"alerts_found": len(found), "critical": critical, "warning": warning}

    def active_alerts(self) -> list:
        with self._lock:
            return [asdict(a) for a in self._alerts if not a.resolved]

    def resolve_alert(self, alert_id: str) -> bool:
        with self._lock:
            for a in self._alerts:
                if a.alert_id == alert_id:
                    a.resolved = True
                    return True
            return False


degradation_detector = DegradationDetector()

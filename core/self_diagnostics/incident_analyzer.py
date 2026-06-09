"""Incident analyzer for self-diagnostic reconstruction engine."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Incident:
    incident_id: str
    title: str
    description: str
    severity: str
    affected_layers: list
    root_cause: str
    detected_at: str
    resolved_at: Optional[str]
    status: str


class IncidentAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._incidents: list = []
        self._counter = 0

    def report_incident(self, title: str, description: str, severity: str,
                        affected_layers: list) -> str:
        with self._lock:
            self._counter += 1
            incident_id = f"INC-{self._counter:03d}"
            i = Incident(
                incident_id=incident_id, title=title, description=description,
                severity=severity, affected_layers=affected_layers, root_cause="",
                detected_at=datetime.utcnow().isoformat(), resolved_at=None, status="OPEN",
            )
            self._incidents.append(i)
            return incident_id

    def investigate(self, incident_id: str) -> dict:
        with self._lock:
            for i in self._incidents:
                if i.incident_id == incident_id:
                    i.status = "INVESTIGATING"
                    # Auto-determine root cause from affected layers
                    if i.affected_layers:
                        i.root_cause = f"Primary failure in layer: {i.affected_layers[0]}"
                    else:
                        i.root_cause = "Root cause under investigation"
                    return asdict(i)
            return {}

    def resolve(self, incident_id: str) -> bool:
        with self._lock:
            for i in self._incidents:
                if i.incident_id == incident_id:
                    i.status = "RESOLVED"
                    i.resolved_at = datetime.utcnow().isoformat()
                    return True
            return False

    def all_incidents(self, status_filter: Optional[str] = None) -> list:
        with self._lock:
            if status_filter:
                return [asdict(i) for i in self._incidents if i.status == status_filter]
            return [asdict(i) for i in self._incidents]

    def incident_stats(self) -> dict:
        with self._lock:
            total = len(self._incidents)
            open_count = sum(1 for i in self._incidents if i.status == "OPEN")
            resolved = sum(1 for i in self._incidents if i.status == "RESOLVED")
            by_sev: dict = {}
            for i in self._incidents:
                by_sev[i.severity] = by_sev.get(i.severity, 0) + 1
            durations = []
            for i in self._incidents:
                if i.resolved_at and i.detected_at:
                    try:
                        s = datetime.fromisoformat(i.detected_at)
                        e = datetime.fromisoformat(i.resolved_at)
                        durations.append((e - s).total_seconds() / 3600)
                    except Exception:
                        pass
            avg_hours = sum(durations) / len(durations) if durations else 0
            return {"total": total, "open": open_count, "resolved": resolved,
                    "by_severity": by_sev, "avg_resolution_time_hours": avg_hours}


incident_analyzer = IncidentAnalyzer()

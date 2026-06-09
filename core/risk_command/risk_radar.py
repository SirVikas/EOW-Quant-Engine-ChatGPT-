"""Risk Radar — aggregates risks from all subsystems into unified radar."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RadarEntry:
    radar_entry_id: str
    source_system: str
    risk_name: str
    severity: str
    detected_at: datetime
    acknowledged: bool


class RiskRadar:
    def __init__(self):
        self._lock = threading.RLock()
        self._entries: dict[str, RadarEntry] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RAD-{self._counter:03d}"

    def detect(self, source_system: str, risk_name: str, severity: str) -> RadarEntry:
        with self._lock:
            entry = RadarEntry(
                radar_entry_id=self._next_id(),
                source_system=source_system,
                risk_name=risk_name,
                severity=severity,
                detected_at=datetime.utcnow(),
                acknowledged=False,
            )
            self._entries[entry.radar_entry_id] = entry
            return entry

    def acknowledge(self, radar_entry_id: str) -> bool:
        with self._lock:
            entry = self._entries.get(radar_entry_id)
            if entry:
                entry.acknowledged = True
                return True
            return False

    def active_risks(self) -> list[dict]:
        with self._lock:
            return [
                {"radar_entry_id": e.radar_entry_id, "source_system": e.source_system,
                 "risk_name": e.risk_name, "severity": e.severity,
                 "detected_at": e.detected_at.isoformat(), "acknowledged": e.acknowledged}
                for e in self._entries.values() if not e.acknowledged
            ]

    def radar_summary(self) -> dict:
        with self._lock:
            by_severity: dict[str, int] = {}
            for e in self._entries.values():
                by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
            return {
                "total_detected": len(self._entries),
                "unacknowledged": sum(1 for e in self._entries.values() if not e.acknowledged),
                "by_severity": by_severity,
            }


risk_radar = RiskRadar()

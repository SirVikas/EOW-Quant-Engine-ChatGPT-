"""GAP-06: Incident Center — manages operational incidents."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from loguru import logger


@dataclass
class Incident:
    inc_id: str
    title: str
    severity: str  # P1/P2/P3/P4
    component: str
    description: str
    status: str  # OPEN/INVESTIGATING/RESOLVED/CLOSED
    opened_at: int
    resolved_at: Optional[int]


class IncidentCenter:
    """Manages operational incidents. Thread-safe."""

    VALID_SEVERITIES = {"P1", "P2", "P3", "P4"}
    VALID_STATUSES = {"OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"}

    def __init__(self):
        self._lock = threading.RLock()
        self._incidents: Dict[str, Incident] = {}
        self._counter = 0
        logger.info("[GAP-06] IncidentCenter initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"INC-{self._counter:03d}"

    def open_incident(self, title: str, severity: str, component: str, description: str) -> str:
        with self._lock:
            iid = self._next_id()
            self._incidents[iid] = Incident(
                inc_id=iid,
                title=title,
                severity=severity if severity in self.VALID_SEVERITIES else "P3",
                component=component,
                description=description,
                status="OPEN",
                opened_at=int(time.time() * 1000),
                resolved_at=None,
            )
            return iid

    def resolve(self, inc_id: str) -> bool:
        with self._lock:
            inc = self._incidents.get(inc_id)
            if inc is None:
                return False
            inc.status = "RESOLVED"
            inc.resolved_at = int(time.time() * 1000)
            return True

    def open_incidents(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(i) for i in self._incidents.values() if i.status in {"OPEN", "INVESTIGATING"}]

    def incident_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._incidents)
            open_count = sum(1 for i in self._incidents.values() if i.status in {"OPEN", "INVESTIGATING"})
            p1 = sum(1 for i in self._incidents.values() if i.severity == "P1" and i.status in {"OPEN", "INVESTIGATING"})
            p2 = sum(1 for i in self._incidents.values() if i.severity == "P2" and i.status in {"OPEN", "INVESTIGATING"})
            resolved = sum(1 for i in self._incidents.values() if i.status in {"RESOLVED", "CLOSED"})
            return {
                "total_incidents": total,
                "open_incidents": open_count,
                "open_p1": p1,
                "open_p2": p2,
                "resolved_incidents": resolved,
                "ts": int(time.time() * 1000),
            }


incident_center = IncidentCenter()

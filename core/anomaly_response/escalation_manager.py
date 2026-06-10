"""
Escalation manager — maps anomaly severity to an escalation level and keeps
an escalation log for resolution tracking.
"""
import threading
import time
from typing import List

ESCALATION_LEVELS = {
    "LOW": "MONITOR",
    "MEDIUM": "REVIEW",
    "HIGH": "ESCALATE",
    "CRITICAL": "IMMEDIATE",
}


class EscalationManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._escalations: List[dict] = []
        self._counter = 0

    def escalate(self, response_id: str, severity: str) -> dict:
        level = ESCALATION_LEVELS.get(str(severity).upper(), "REVIEW")
        with self._lock:
            self._counter += 1
            escalation = {
                "escalation_id": f"ARE-{self._counter:03d}",
                "response_id": response_id,
                "severity": str(severity).upper(),
                "level": level,
                "escalated_at": time.time(),
            }
            self._escalations.append(escalation)
            return escalation

    def escalation_summary(self) -> dict:
        with self._lock:
            escalations = list(self._escalations)
            by_level: dict = {}
            for e in escalations:
                by_level[e["level"]] = by_level.get(e["level"], 0) + 1
            return {
                "total": len(escalations),
                "by_level": by_level,
                "recent": escalations[-10:],
            }


escalation_manager = EscalationManager()

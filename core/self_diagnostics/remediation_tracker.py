"""Remediation action tracker for self-diagnostics."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class RemediationAction:
    action_id: str
    incident_id: str
    action_description: str
    owner: str
    due_days: int
    status: str
    created_at: str
    completed_at: Optional[str]


class RemediationTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._actions: list = []
        self._counter = 0

    def add_action(self, incident_id: str, action_description: str, owner: str,
                   due_days: int = 7) -> dict:
        with self._lock:
            self._counter += 1
            a = RemediationAction(
                action_id=f"REM-{self._counter:03d}",
                incident_id=incident_id,
                action_description=action_description,
                owner=owner,
                due_days=due_days,
                status="OPEN",
                created_at=datetime.utcnow().isoformat(),
                completed_at=None,
            )
            self._actions.append(a)
            return asdict(a)

    def complete(self, action_id: str) -> bool:
        with self._lock:
            for a in self._actions:
                if a.action_id == action_id:
                    a.status = "COMPLETED"
                    a.completed_at = datetime.utcnow().isoformat()
                    return True
            return False

    def waive(self, action_id: str, reason: str) -> bool:
        with self._lock:
            for a in self._actions:
                if a.action_id == action_id:
                    a.status = "WAIVED"
                    return True
            return False

    def open_actions(self, incident_id: Optional[str] = None) -> list:
        with self._lock:
            result = [a for a in self._actions if a.status in ("OPEN", "IN_PROGRESS")]
            if incident_id:
                result = [a for a in result if a.incident_id == incident_id]
            return [asdict(a) for a in result]

    def action_stats(self) -> dict:
        with self._lock:
            total = len(self._actions)
            open_count = sum(1 for a in self._actions if a.status in ("OPEN", "IN_PROGRESS"))
            completed = sum(1 for a in self._actions if a.status == "COMPLETED")
            waived = sum(1 for a in self._actions if a.status == "WAIVED")
            now = datetime.utcnow()
            overdue = 0
            for a in self._actions:
                if a.status in ("OPEN", "IN_PROGRESS"):
                    try:
                        created = datetime.fromisoformat(a.created_at)
                        if (now - created).days > a.due_days:
                            overdue += 1
                    except Exception:
                        pass
            return {"total": total, "open": open_count, "completed": completed,
                    "waived": waived, "overdue_count": overdue}


remediation_tracker = RemediationTracker()

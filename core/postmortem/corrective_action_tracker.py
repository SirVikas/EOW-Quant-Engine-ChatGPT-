"""
Corrective action tracker — manages follow-up actions arising from post-mortems.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class CorrectiveAction:
    action_id: str
    incident_id: str
    action_text: str
    owner: str
    due_date_days: int
    status: str   # OPEN / IN_PROGRESS / COMPLETED / WAIVED
    created_at: str


class CorrectiveActionTracker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._actions: List[CorrectiveAction] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CAT-{self._counter:03d}"

    def create(
        self,
        incident_id: str,
        action_text: str,
        owner: str,
        due_date_days: int,
    ) -> CorrectiveAction:
        with self._lock:
            action = CorrectiveAction(
                action_id=self._next_id(),
                incident_id=incident_id,
                action_text=action_text,
                owner=owner,
                due_date_days=due_date_days,
                status="OPEN",
                created_at=datetime.utcnow().isoformat(),
            )
            self._actions.append(action)
            return action

    def complete(self, action_id: str) -> bool:
        with self._lock:
            for a in self._actions:
                if a.action_id == action_id:
                    a.status = "COMPLETED"
                    return True
            return False

    def overdue_actions(self) -> List[CorrectiveAction]:
        # Without tracking actual elapsed days, return all OPEN/IN_PROGRESS
        # for now — in live use this would compare created_at + due_date_days
        with self._lock:
            return [a for a in self._actions if a.status in ("OPEN", "IN_PROGRESS")]

    def action_summary(self) -> dict:
        with self._lock:
            return {
                "total": len(self._actions),
                "open": sum(1 for a in self._actions if a.status == "OPEN"),
                "in_progress": sum(1 for a in self._actions if a.status == "IN_PROGRESS"),
                "completed": sum(1 for a in self._actions if a.status == "COMPLETED"),
                "waived": sum(1 for a in self._actions if a.status == "WAIVED"),
            }


corrective_action_tracker = CorrectiveActionTracker()

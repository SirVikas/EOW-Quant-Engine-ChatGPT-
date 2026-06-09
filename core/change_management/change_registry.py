"""Change Registry — tracks proposed changes."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


ChangeType = Literal["ARCHITECTURAL", "POLICY", "GOVERNANCE", "STRATEGIC"]
ChangeStatus = Literal["PROPOSED", "UNDER_REVIEW", "APPROVED", "REJECTED", "IMPLEMENTED", "ROLLED_BACK"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass
class ChangeRecord:
    change_id: str
    title: str
    change_type: ChangeType
    requester: str
    status: ChangeStatus
    risk_level: RiskLevel
    submitted_at: datetime = field(default_factory=datetime.utcnow)


class ChangeRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._changes: List[ChangeRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CHG-{self._counter:03d}"

    def propose(self, title: str, change_type: ChangeType, requester: str, risk_level: RiskLevel) -> ChangeRecord:
        with self._lock:
            rec = ChangeRecord(self._next_id(), title, change_type, requester, "PROPOSED", risk_level)
            self._changes.append(rec)
            return rec

    def update_status(self, change_id: str, status: ChangeStatus) -> bool:
        with self._lock:
            for c in self._changes:
                if c.change_id == change_id:
                    c.status = status
                    return True
            return False

    def pending_changes(self) -> List[dict]:
        with self._lock:
            return [vars(c) for c in self._changes if c.status in ("PROPOSED", "UNDER_REVIEW")]

    def change_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for c in self._changes:
                summary[c.status] = summary.get(c.status, 0) + 1
            return {"total_changes": len(self._changes), "by_status": summary}

    def get(self, change_id: str):
        with self._lock:
            return next((c for c in self._changes if c.change_id == change_id), None)


change_registry = ChangeRegistry()

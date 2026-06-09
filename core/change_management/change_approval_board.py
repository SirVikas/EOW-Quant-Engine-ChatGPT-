"""Change Approval Board — manages approval decisions."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


Decision = Literal["APPROVED", "REJECTED"]


@dataclass
class ApprovalRecord:
    approval_id: str
    change_id: str
    approver: str
    decision: Decision
    rationale: str
    decided_at: datetime = field(default_factory=datetime.utcnow)


class ChangeApprovalBoard:
    def __init__(self):
        self._lock = threading.RLock()
        self._approvals: List[ApprovalRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"APR-{self._counter:03d}"

    def approve(self, change_id: str, approver: str, rationale: str) -> ApprovalRecord:
        from core.change_management.change_registry import change_registry
        with self._lock:
            change_registry.update_status(change_id, "APPROVED")
            rec = ApprovalRecord(self._next_id(), change_id, approver, "APPROVED", rationale)
            self._approvals.append(rec)
            return rec

    def reject(self, change_id: str, approver: str, rationale: str) -> ApprovalRecord:
        from core.change_management.change_registry import change_registry
        with self._lock:
            change_registry.update_status(change_id, "REJECTED")
            rec = ApprovalRecord(self._next_id(), change_id, approver, "REJECTED", rationale)
            self._approvals.append(rec)
            return rec

    def approvals_for(self, change_id: str) -> List[dict]:
        with self._lock:
            return [vars(a) for a in self._approvals if a.change_id == change_id]


change_approval_board = ChangeApprovalBoard()

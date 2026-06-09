"""Policy approval workflow engine."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class PolicyApproval:
    approval_id: str
    policy_id: str
    version_id: str
    submitted_by: str
    status: str
    submitted_at: str
    decided_at: Optional[str]
    decision_notes: str


class PolicyApprovalWorkflow:
    def __init__(self):
        self._lock = threading.RLock()
        self._approvals: list = []
        self._counter = 0

    def submit(self, policy_id: str, version_id: str, submitted_by: str) -> str:
        with self._lock:
            self._counter += 1
            approval_id = f"PAP-{self._counter:03d}"
            a = PolicyApproval(
                approval_id=approval_id, policy_id=policy_id, version_id=version_id,
                submitted_by=submitted_by, status="DRAFT",
                submitted_at=datetime.utcnow().isoformat(), decided_at=None, decision_notes="",
            )
            self._approvals.append(a)
            return approval_id

    def send_for_review(self, approval_id: str) -> bool:
        with self._lock:
            for a in self._approvals:
                if a.approval_id == approval_id:
                    a.status = "REVIEW"
                    return True
            return False

    def approve(self, approval_id: str, decision_notes: str = "") -> bool:
        with self._lock:
            for a in self._approvals:
                if a.approval_id == approval_id:
                    a.status = "APPROVED"
                    a.decided_at = datetime.utcnow().isoformat()
                    a.decision_notes = decision_notes
                    return True
            return False

    def reject(self, approval_id: str, decision_notes: str) -> bool:
        with self._lock:
            for a in self._approvals:
                if a.approval_id == approval_id:
                    a.status = "REJECTED"
                    a.decided_at = datetime.utcnow().isoformat()
                    a.decision_notes = decision_notes
                    return True
            return False

    def pending_approvals(self) -> list:
        with self._lock:
            return [asdict(a) for a in self._approvals if a.status in ("DRAFT", "REVIEW")]


policy_approval_workflow = PolicyApprovalWorkflow()

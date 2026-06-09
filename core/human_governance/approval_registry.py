"""Approval Registry — tracks human approval requests for system actions."""
import threading
import time
from dataclasses import dataclass


@dataclass
class ApprovalRecord:
    approval_id: str
    subject_id: str
    subject_type: str
    action_requested: str
    requested_by: str
    approved_by: str  # empty string if not yet decided
    status: str  # PENDING/APPROVED/REJECTED/EXPIRED
    requested_at: float
    decided_at: float
    expiry_seconds: int


class ApprovalRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, ApprovalRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"HAP-{self._counter:03d}"

    def request_approval(self, subject_id: str, subject_type: str, action_requested: str,
                          requested_by: str, expiry_seconds: int = 86400) -> str:
        with self._lock:
            aid = self._next_id()
            self._records[aid] = ApprovalRecord(
                approval_id=aid,
                subject_id=subject_id,
                subject_type=subject_type,
                action_requested=action_requested,
                requested_by=requested_by,
                approved_by="",
                status="PENDING",
                requested_at=time.time(),
                decided_at=0.0,
                expiry_seconds=expiry_seconds,
            )
            return aid

    def approve(self, approval_id: str, approved_by: str) -> bool:
        with self._lock:
            r = self._records.get(approval_id)
            if not r:
                return False
            r.status = "APPROVED"
            r.approved_by = approved_by
            r.decided_at = time.time()
            return True

    def reject(self, approval_id: str, approved_by: str, reason: str = "") -> bool:
        with self._lock:
            r = self._records.get(approval_id)
            if not r:
                return False
            r.status = "REJECTED"
            r.approved_by = approved_by
            r.decided_at = time.time()
            return True

    def is_approved(self, approval_id: str) -> bool:
        with self._lock:
            r = self._records.get(approval_id)
            if not r:
                return False
            if r.status == "APPROVED":
                # Check expiry
                if time.time() - r.decided_at > r.expiry_seconds:
                    r.status = "EXPIRED"
                    return False
                return True
            return False

    def pending_approvals(self) -> list:
        with self._lock:
            now = time.time()
            result = []
            for r in self._records.values():
                if r.status == "PENDING":
                    if now - r.requested_at > r.expiry_seconds:
                        r.status = "EXPIRED"
                    else:
                        result.append(vars(r))
            return result

    def approval_stats(self) -> dict:
        with self._lock:
            items = list(self._records.values())
            total = len(items)
            # Refresh expired
            now = time.time()
            for r in items:
                if r.status == "PENDING" and now - r.requested_at > r.expiry_seconds:
                    r.status = "EXPIRED"
            return {
                "total": total,
                "approved": sum(1 for r in items if r.status == "APPROVED"),
                "rejected": sum(1 for r in items if r.status == "REJECTED"),
                "pending": sum(1 for r in items if r.status == "PENDING"),
                "expired": sum(1 for r in items if r.status == "EXPIRED"),
            }


approval_registry = ApprovalRegistry()

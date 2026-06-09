"""Data Retention Engine — enforces data retention policies."""
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Literal


ActionOnExpiry = Literal["ARCHIVE", "DELETE", "ANONYMIZE"]
PolicyStatus = Literal["ACTIVE", "EXPIRED"]


@dataclass
class RetentionPolicy:
    policy_id: str
    dataset_name: str
    retention_days: int
    action_on_expiry: ActionOnExpiry
    status: PolicyStatus
    created_at: datetime = field(default_factory=datetime.utcnow)


class DataRetentionEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._policies: List[RetentionPolicy] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RET-{self._counter:03d}"

    def set_policy(self, dataset_name: str, retention_days: int, action: ActionOnExpiry) -> RetentionPolicy:
        with self._lock:
            pol = RetentionPolicy(
                policy_id=self._next_id(),
                dataset_name=dataset_name,
                retention_days=retention_days,
                action_on_expiry=action,
                status="ACTIVE",
            )
            self._policies.append(pol)
            return pol

    def due_for_action(self) -> List[dict]:
        """Policies where retention period has elapsed since creation."""
        with self._lock:
            now = datetime.utcnow()
            due = []
            for p in self._policies:
                if p.status == "ACTIVE" and (now - p.created_at) >= timedelta(days=p.retention_days):
                    due.append(vars(p))
            return due

    def retention_summary(self) -> dict:
        with self._lock:
            return {
                "total_policies": len(self._policies),
                "active": sum(1 for p in self._policies if p.status == "ACTIVE"),
                "expired": sum(1 for p in self._policies if p.status == "EXPIRED"),
                "due_for_action": len(self.due_for_action()),
            }


data_retention_engine = DataRetentionEngine()

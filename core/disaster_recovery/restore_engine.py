"""Disaster Recovery — Restore Engine."""
import threading, time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RestoreOperation:
    restore_id: str
    backup_id: str
    restored_by: str
    restore_type: str
    status: str
    initiated_at: float
    completed_at: Optional[float]


class RestoreEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._operations: List[RestoreOperation] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RST-{self._counter:03d}"

    def initiate_restore(self, backup_id: str, restored_by: str, restore_type: str = "FULL") -> str:
        with self._lock:
            rid = self._next_id()
            op = RestoreOperation(
                restore_id=rid,
                backup_id=backup_id,
                restored_by=restored_by,
                restore_type=restore_type,
                status="IN_PROGRESS",
                initiated_at=time.time(),
                completed_at=None,
            )
            self._operations.append(op)
        return rid

    def complete_restore(self, restore_id: str) -> bool:
        with self._lock:
            for op in self._operations:
                if op.restore_id == restore_id:
                    op.status = "COMPLETED"
                    op.completed_at = time.time()
                    return True
        return False

    def fail_restore(self, restore_id: str, reason: str) -> bool:
        with self._lock:
            for op in self._operations:
                if op.restore_id == restore_id:
                    op.status = "FAILED"
                    op.completed_at = time.time()
                    return True
        return False

    def restore_history(self, limit: int = 10) -> List[dict]:
        with self._lock:
            ops = self._operations[-limit:]
        return [
            {
                "restore_id": o.restore_id,
                "backup_id": o.backup_id,
                "restored_by": o.restored_by,
                "restore_type": o.restore_type,
                "status": o.status,
                "initiated_at": o.initiated_at,
                "completed_at": o.completed_at,
            }
            for o in reversed(ops)
        ]

    def restore_stats(self) -> dict:
        with self._lock:
            total = len(self._operations)
            completed = sum(1 for o in self._operations if o.status == "COMPLETED")
            failed = sum(1 for o in self._operations if o.status == "FAILED")
            last = self._operations[-1].initiated_at if self._operations else None
        return {"total_restores": total, "completed": completed, "failed": failed, "last_restore_at": last}


restore_engine = RestoreEngine()

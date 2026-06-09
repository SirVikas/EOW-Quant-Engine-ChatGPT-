"""Knowledge Retirement Engine — retires stale/superseded knowledge."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RetirementRecord:
    retirement_id: str
    item_id: str
    reason: str
    retired_by: str
    retired_at: datetime


class KnowledgeRetirementEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, RetirementRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"KRT-{self._counter:03d}"

    def retire(self, item_id: str, reason: str, retired_by: str) -> RetirementRecord:
        from core.knowledge_operations.knowledge_lifecycle_engine import knowledge_lifecycle_engine
        knowledge_lifecycle_engine.retire(item_id)
        with self._lock:
            rec = RetirementRecord(
                retirement_id=self._next_id(),
                item_id=item_id,
                reason=reason,
                retired_by=retired_by,
                retired_at=datetime.utcnow(),
            )
            self._records[rec.retirement_id] = rec
            return rec

    def retired_items(self) -> list[dict]:
        with self._lock:
            return [
                {"retirement_id": r.retirement_id, "item_id": r.item_id,
                 "reason": r.reason, "retired_by": r.retired_by,
                 "retired_at": r.retired_at.isoformat()}
                for r in self._records.values()
            ]

    def retirement_summary(self) -> dict:
        with self._lock:
            return {
                "total_retirements": len(self._records),
                "retired_by": list({r.retired_by for r in self._records.values()}),
            }


knowledge_retirement_engine = KnowledgeRetirementEngine()

"""Knowledge Lifecycle Engine — tracks knowledge items through lifecycle stages."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


STAGES = ["DRAFT", "CANDIDATE", "APPROVED", "INSTITUTIONAL", "RETIRED"]


@dataclass
class KnowledgeItem:
    item_id: str
    title: str
    domain: str
    stage: str
    created_at: datetime
    promoted_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None


class KnowledgeLifecycleEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._items: dict[str, KnowledgeItem] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"KNW-{self._counter:03d}"

    def create(self, title: str, domain: str) -> KnowledgeItem:
        with self._lock:
            item = KnowledgeItem(
                item_id=self._next_id(),
                title=title,
                domain=domain,
                stage="DRAFT",
                created_at=datetime.utcnow(),
            )
            self._items[item.item_id] = item
            return item

    def promote(self, item_id: str) -> Optional[KnowledgeItem]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return None
            idx = STAGES.index(item.stage)
            if idx < len(STAGES) - 2:  # don't advance past INSTITUTIONAL via promote
                item.stage = STAGES[idx + 1]
                item.promoted_at = datetime.utcnow()
            return item

    def retire(self, item_id: str) -> Optional[KnowledgeItem]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return None
            item.stage = "RETIRED"
            item.retired_at = datetime.utcnow()
            return item

    def by_stage(self, stage: str) -> list[dict]:
        with self._lock:
            return [
                {"item_id": i.item_id, "title": i.title, "domain": i.domain,
                 "stage": i.stage, "created_at": i.created_at.isoformat()}
                for i in self._items.values() if i.stage == stage
            ]

    def lifecycle_summary(self) -> dict:
        with self._lock:
            by_stage: dict[str, int] = {s: 0 for s in STAGES}
            for i in self._items.values():
                by_stage[i.stage] = by_stage.get(i.stage, 0) + 1
            return {"total_items": len(self._items), "by_stage": by_stage}


knowledge_lifecycle_engine = KnowledgeLifecycleEngine()

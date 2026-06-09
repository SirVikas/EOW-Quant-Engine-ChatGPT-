"""Evidence Registry — core store for all institutional evidence items."""
import threading
import time
from dataclasses import dataclass, field


@dataclass
class EvidenceItem:
    item_id: str
    evidence_type: str  # TRUST/ECONOMIC/SIMULATION/RECOMMENDATION/VALIDATION/EVOLUTION/GOVERNANCE
    subject_id: str
    source_layer: str
    content: dict
    quality: float  # 0-1
    created_at: float
    tags: list


class EvidenceRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._items: dict[str, EvidenceItem] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"EW-{self._counter:03d}"

    def store(self, evidence_type: str, subject_id: str, source_layer: str,
              content: dict, quality: float = 0.5, tags: list = None) -> str:
        with self._lock:
            item_id = self._next_id()
            self._items[item_id] = EvidenceItem(
                item_id=item_id,
                evidence_type=evidence_type,
                subject_id=subject_id,
                source_layer=source_layer,
                content=content,
                quality=quality,
                created_at=time.time(),
                tags=tags or [],
            )
            return item_id

    def get(self, item_id: str) -> dict:
        with self._lock:
            item = self._items.get(item_id)
            return vars(item) if item else {}

    def query(self, evidence_type: str = None, subject_id: str = None,
              source_layer: str = None, min_quality: float = 0.0) -> list:
        with self._lock:
            items = list(self._items.values())
            if evidence_type:
                items = [i for i in items if i.evidence_type == evidence_type]
            if subject_id:
                items = [i for i in items if i.subject_id == subject_id]
            if source_layer:
                items = [i for i in items if i.source_layer == source_layer]
            items = [i for i in items if i.quality >= min_quality]
            return [vars(i) for i in items]

    def all_evidence(self, limit: int = 100) -> list:
        with self._lock:
            items = list(self._items.values())[-limit:]
            return [vars(i) for i in items]

    def registry_stats(self) -> dict:
        with self._lock:
            items = list(self._items.values())
            total = len(items)
            by_type: dict = {}
            by_layer: dict = {}
            for i in items:
                by_type[i.evidence_type] = by_type.get(i.evidence_type, 0) + 1
                by_layer[i.source_layer] = by_layer.get(i.source_layer, 0) + 1
            qualities = [i.quality for i in items]
            return {
                "total": total,
                "by_type": by_type,
                "by_source_layer": by_layer,
                "avg_quality": sum(qualities) / len(qualities) if qualities else 0.0,
            }


evidence_registry = EvidenceRegistry()

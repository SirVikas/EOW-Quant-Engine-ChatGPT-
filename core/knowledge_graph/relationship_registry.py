"""Relationship Registry — Knowledge Graph edge store."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional

REL_TYPES = {
    "CAUSED_BY", "LED_TO", "RESOLVED_BY", "VALIDATED_BY",
    "IMPACTS", "DEPENDS_ON", "IMPROVES",
}


@dataclass
class Relationship:
    rel_id: str
    source_id: str
    target_id: str
    rel_type: str
    label: str
    weight: float
    created_at: float


class RelationshipRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._relationships: dict[str, Relationship] = {}

    def create(self, source_id: str, target_id: str, rel_type: str,
               label: str = "", weight: float = 1.0) -> str:
        ts = int(time.time() * 1000)
        rel_id = f"REL-{rel_type[:3].upper()}-{ts}"
        rel = Relationship(
            rel_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            label=label,
            weight=weight,
            created_at=time.time(),
        )
        with self._lock:
            self._relationships[rel_id] = rel
        return rel_id

    def get_outgoing(self, entity_id: str) -> list:
        with self._lock:
            return [asdict(r) for r in self._relationships.values() if r.source_id == entity_id]

    def get_incoming(self, entity_id: str) -> list:
        with self._lock:
            return [asdict(r) for r in self._relationships.values() if r.target_id == entity_id]

    def all_relationships(self, rel_type: Optional[str] = None) -> list:
        with self._lock:
            if rel_type:
                return [asdict(r) for r in self._relationships.values() if r.rel_type == rel_type]
            return [asdict(r) for r in self._relationships.values()]


relationship_registry = RelationshipRegistry()

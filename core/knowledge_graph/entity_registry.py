"""Entity Registry — Knowledge Graph node store."""
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

ENTITY_TYPES = {
    "FINDING", "ROOT_CAUSE", "RECOMMENDATION", "IMPLEMENTATION",
    "OUTCOME", "TRUST_SCORE", "LAYER", "RISK", "DECISION",
}


@dataclass
class Entity:
    entity_id: str
    entity_type: str
    label: str
    properties: dict
    created_at: float


class EntityRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._entities: dict[str, Entity] = {}

    def register(self, entity_type: str, label: str, properties: Optional[dict] = None) -> str:
        ts = int(time.time() * 1000)
        entity_id = f"ENT-{entity_type[:3].upper()}-{ts}"
        entity = Entity(
            entity_id=entity_id,
            entity_type=entity_type,
            label=label,
            properties=properties or {},
            created_at=time.time(),
        )
        with self._lock:
            self._entities[entity_id] = entity
        return entity_id

    def get(self, entity_id: str) -> Optional[dict]:
        with self._lock:
            e = self._entities.get(entity_id)
            return asdict(e) if e else None

    def all_entities(self, entity_type: Optional[str] = None) -> list:
        with self._lock:
            if entity_type:
                return [asdict(e) for e in self._entities.values() if e.entity_type == entity_type]
            return [asdict(e) for e in self._entities.values()]

    def entity_count(self) -> dict:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entities.values():
                counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
            return counts


entity_registry = EntityRegistry()

"""CTAO — CT Knowledge Vault: institutional memory of all CT scan learnings."""
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class KnowledgeEntry:
    entry_id: str
    entry_type: str
    title: str
    content: str
    tags: List[str]
    importance: float
    created_at: float


class CTKnowledgeVault:
    def __init__(self):
        self._lock = threading.RLock()
        self._entries: List[KnowledgeEntry] = []

    def store(self, entry_type: str, title: str, content: str,
              tags: List[str] = None, importance: float = 5.0) -> str:
        with self._lock:
            entry_id = str(uuid.uuid4())
            e = KnowledgeEntry(
                entry_id=entry_id,
                entry_type=entry_type,
                title=title,
                content=content,
                tags=tags or [],
                importance=importance,
                created_at=time.time(),
            )
            self._entries.append(e)
            return entry_id

    def search(self, query: str, entry_type: str = None) -> List[dict]:
        with self._lock:
            q = query.lower()
            result = []
            for e in self._entries:
                if entry_type and e.entry_type != entry_type:
                    continue
                if q in e.title.lower() or q in e.content.lower():
                    result.append(asdict(e))
            return result

    def patterns(self) -> dict:
        with self._lock:
            groups: dict = {}
            for e in self._entries:
                key = e.entry_type
                groups.setdefault(key, []).append(e.title)
            return {k: {"count": len(v), "titles": v[:5]} for k, v in groups.items()}

    def vault_stats(self) -> dict:
        with self._lock:
            total = len(self._entries)
            by_type: dict = {}
            for e in self._entries:
                by_type[e.entry_type] = by_type.get(e.entry_type, 0) + 1
            top3 = sorted(self._entries, key=lambda x: x.importance, reverse=True)[:3]
            return {
                "total_entries": total,
                "by_type": by_type,
                "most_important_3": [asdict(e) for e in top3],
            }

    def top_lessons(self, limit: int = 10) -> List[dict]:
        with self._lock:
            lessons = [e for e in self._entries if e.entry_type == "LESSON"]
            return [asdict(e) for e in sorted(lessons, key=lambda x: x.importance, reverse=True)[:limit]]


ct_knowledge_vault = CTKnowledgeVault()

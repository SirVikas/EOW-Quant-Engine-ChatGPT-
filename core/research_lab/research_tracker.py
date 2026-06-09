"""Research tracker for institutional research lab."""
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class ResearchItem:
    item_id: str
    title: str
    item_type: str
    source: str
    summary: str
    tags: list
    relevance_score: float
    added_at: str


class ResearchTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._items: list = []
        self._counter = 0

    def add(self, title: str, item_type: str, source: str, summary: str,
            tags: Optional[list] = None, relevance_score: float = 0.5) -> dict:
        with self._lock:
            self._counter += 1
            item = ResearchItem(
                item_id=f"RI-{self._counter:04d}",
                title=title, item_type=item_type, source=source,
                summary=summary, tags=tags or [], relevance_score=relevance_score,
                added_at=datetime.utcnow().isoformat(),
            )
            self._items.append(item)
            return asdict(item)

    def search(self, query: str, item_type: Optional[str] = None) -> list:
        with self._lock:
            q = query.lower()
            results = []
            for item in self._items:
                if item_type and item.item_type != item_type:
                    continue
                if q in item.title.lower() or q in item.summary.lower():
                    results.append(asdict(item))
            return results

    def top_relevant(self, limit: int = 10) -> list:
        with self._lock:
            return [asdict(i) for i in sorted(self._items, key=lambda x: x.relevance_score, reverse=True)[:limit]]

    def research_stats(self) -> dict:
        with self._lock:
            total = len(self._items)
            by_type: dict = {}
            for i in self._items:
                by_type[i.item_type] = by_type.get(i.item_type, 0) + 1
            avg_rel = sum(i.relevance_score for i in self._items) / max(1, total)
            recent = [asdict(i) for i in self._items[-5:]]
            return {"total": total, "by_type": by_type, "avg_relevance": avg_rel, "recent_5": recent}


research_tracker = ResearchTracker()

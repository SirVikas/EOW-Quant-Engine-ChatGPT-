"""Knowledge Importance Tracker — monitors which knowledge items matter most."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ImportanceRecord:
    subject_id: str
    knowledge_type: str
    importance_score: float  # 0-100
    access_frequency: int
    citation_count: int
    last_accessed: str
    created_at: str


class KnowledgeImportanceTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, ImportanceRecord] = {}

    def record(self, subject_id: str, knowledge_type: str,
               initial_importance: float = 50) -> str:
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            r = ImportanceRecord(
                subject_id=subject_id,
                knowledge_type=knowledge_type,
                importance_score=initial_importance,
                access_frequency=0,
                citation_count=0,
                last_accessed=now,
                created_at=now,
            )
            self._records[subject_id] = r
            return subject_id

    def access(self, subject_id: str) -> bool:
        with self._lock:
            r = self._records.get(subject_id)
            if r is None:
                return False
            r.access_frequency += 1
            r.importance_score = min(100.0, r.importance_score + 1)
            r.last_accessed = datetime.now(timezone.utc).isoformat()
            return True

    def cite(self, subject_id: str) -> bool:
        with self._lock:
            r = self._records.get(subject_id)
            if r is None:
                return False
            r.citation_count += 1
            r.importance_score = min(100.0, r.importance_score + 2)
            return True

    def decay_importance(self, subject_id: str, amount: float = 1) -> bool:
        with self._lock:
            r = self._records.get(subject_id)
            if r is None:
                return False
            r.importance_score = max(0.0, r.importance_score - amount)
            return True

    def top_knowledge(self, limit: int = 20) -> List[dict]:
        with self._lock:
            sorted_records = sorted(self._records.values(),
                                    key=lambda x: x.importance_score, reverse=True)
            return [asdict(r) for r in sorted_records[:limit]]

    def all_records(self) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._records.values()]

    def importance_stats(self) -> dict:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total": 0, "avg_importance": 0, "top_3_subjects": []}
            avg = sum(r.importance_score for r in self._records.values()) / total
            top3 = sorted(self._records.values(), key=lambda x: x.importance_score, reverse=True)[:3]
            return {
                "total": total,
                "avg_importance": avg,
                "top_3_subjects": [r.subject_id for r in top3],
            }


knowledge_importance_tracker = KnowledgeImportanceTracker()

"""Long-Term Lesson Archive — persistent institutional knowledge store."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ArchivedLesson:
    archive_id: str
    title: str
    content: str
    source_type: str  # FAILURE/SUCCESS/GOVERNANCE/EVOLUTION/STRATEGIC
    period_label: str
    importance: float  # 0-10
    preserved_at: str
    access_count: int = 0


class LongTermLessonArchive:
    def __init__(self):
        self._lock = threading.RLock()
        self._lessons: dict[str, ArchivedLesson] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ARC-{self._counter:03d}"

    def archive(self, title: str, content: str, source_type: str,
                importance: float = 5, period_label: str = "") -> str:
        with self._lock:
            archive_id = self._next_id()
            lesson = ArchivedLesson(
                archive_id=archive_id,
                title=title,
                content=content,
                source_type=source_type,
                period_label=period_label,
                importance=importance,
                preserved_at=datetime.now(timezone.utc).isoformat(),
            )
            self._lessons[archive_id] = lesson
            return archive_id

    def retrieve(self, archive_id: str) -> Optional[dict]:
        with self._lock:
            lesson = self._lessons.get(archive_id)
            if lesson is None:
                return None
            lesson.access_count += 1
            return asdict(lesson)

    def search(self, query: str, source_type: Optional[str] = None) -> List[dict]:
        with self._lock:
            q = query.lower()
            results = []
            for lesson in self._lessons.values():
                if source_type and lesson.source_type != source_type:
                    continue
                if q in lesson.title.lower() or q in lesson.content.lower():
                    results.append(asdict(lesson))
            return results

    def most_accessed(self, limit: int = 10) -> List[dict]:
        with self._lock:
            sorted_lessons = sorted(self._lessons.values(),
                                    key=lambda x: x.access_count, reverse=True)
            return [asdict(l) for l in sorted_lessons[:limit]]

    def archive_stats(self) -> dict:
        with self._lock:
            by_type: dict[str, int] = {}
            total_importance = 0.0
            most_accessed_id = None
            max_access = -1
            for lesson in self._lessons.values():
                by_type[lesson.source_type] = by_type.get(lesson.source_type, 0) + 1
                total_importance += lesson.importance
                if lesson.access_count > max_access:
                    max_access = lesson.access_count
                    most_accessed_id = lesson.archive_id
            total = len(self._lessons)
            return {
                "total": total,
                "by_source_type": by_type,
                "avg_importance": total_importance / total if total else 0,
                "most_accessed_id": most_accessed_id,
            }

    def top_lessons(self, limit: int = 20) -> List[dict]:
        with self._lock:
            sorted_lessons = sorted(self._lessons.values(),
                                    key=lambda x: x.importance, reverse=True)
            return [asdict(l) for l in sorted_lessons[:limit]]


long_term_lesson_archive = LongTermLessonArchive()

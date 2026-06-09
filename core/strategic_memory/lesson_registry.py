"""Lesson Registry — institutional lessons learned store."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Lesson:
    lesson_id: str
    title: str
    content: str
    evidence_count: int
    confidence: float
    source_type: str  # FAILURE/SUCCESS/PATTERN/MANUAL
    created_at: float
    validated: bool


class LessonRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._lessons: dict[str, Lesson] = {}
        self._counter = 0

    def record_lesson(self, title: str, content: str, evidence_count: int = 1,
                      confidence: float = 0.5, source_type: str = "MANUAL") -> str:
        with self._lock:
            self._counter += 1
            lid = f"LES-{self._counter:04d}"
            lesson = Lesson(
                lesson_id=lid,
                title=title,
                content=content,
                evidence_count=evidence_count,
                confidence=confidence,
                source_type=source_type,
                created_at=time.time(),
                validated=False,
            )
            self._lessons[lid] = lesson
            return lid

    def validate_lesson(self, lesson_id: str) -> bool:
        with self._lock:
            if lesson_id in self._lessons:
                self._lessons[lesson_id].validated = True
                return True
            return False

    def all_lessons(self, validated_only: bool = False) -> list:
        with self._lock:
            if validated_only:
                return [asdict(l) for l in self._lessons.values() if l.validated]
            return [asdict(l) for l in self._lessons.values()]

    def top_lessons(self, limit: int = 10) -> list:
        with self._lock:
            sorted_lessons = sorted(
                self._lessons.values(),
                key=lambda l: l.confidence * l.evidence_count,
                reverse=True,
            )
            return [asdict(l) for l in sorted_lessons[:limit]]


lesson_registry = LessonRegistry()

"""
Lesson extractor — captures institutional lessons from incident post-mortems.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class Lesson:
    lesson_id: str
    incident_id: str
    lesson_text: str
    lesson_type: str    # TECHNICAL / PROCESS / GOVERNANCE / STRATEGY
    applicable_to: List[str]
    extracted_at: str


class LessonExtractor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._lessons: List[Lesson] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"LES-{self._counter:03d}"

    def extract(
        self,
        incident_id: str,
        lesson_text: str,
        lesson_type: str,
        applicable_to: List[str],
    ) -> Lesson:
        with self._lock:
            lesson = Lesson(
                lesson_id=self._next_id(),
                incident_id=incident_id,
                lesson_text=lesson_text,
                lesson_type=lesson_type,
                applicable_to=applicable_to,
                extracted_at=datetime.utcnow().isoformat(),
            )
            self._lessons.append(lesson)
            return lesson

    def lessons_for(self, incident_id: str) -> List[Lesson]:
        with self._lock:
            return [l for l in self._lessons if l.incident_id == incident_id]

    def lessons_by_type(self, lesson_type: str) -> List[Lesson]:
        with self._lock:
            return [l for l in self._lessons if l.lesson_type == lesson_type]


lesson_extractor = LessonExtractor()

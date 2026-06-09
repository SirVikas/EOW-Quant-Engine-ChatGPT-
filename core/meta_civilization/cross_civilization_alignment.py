"""Cross Civilization Alignment — tracks alignment between civilizations."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AlignmentAssessment:
    alignment_id: str
    civ_a: str
    civ_b: str
    topic: str
    alignment_score: int
    assessed_at: datetime


class CrossCivilizationAlignment:
    def __init__(self):
        self._lock = threading.RLock()
        self._assessments: dict[str, AlignmentAssessment] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"XCA-{self._counter:03d}"

    def assess(self, civ_a: str, civ_b: str, topic: str,
               alignment_score: int) -> AlignmentAssessment:
        with self._lock:
            a = AlignmentAssessment(
                alignment_id=self._next_id(),
                civ_a=civ_a,
                civ_b=civ_b,
                topic=topic,
                alignment_score=max(0, min(100, alignment_score)),
                assessed_at=datetime.utcnow(),
            )
            self._assessments[a.alignment_id] = a
            return a

    def misaligned_pairs(self, threshold: int = 60) -> list[dict]:
        with self._lock:
            return [
                {"alignment_id": a.alignment_id, "civ_a": a.civ_a, "civ_b": a.civ_b,
                 "topic": a.topic, "alignment_score": a.alignment_score}
                for a in self._assessments.values() if a.alignment_score < threshold
            ]

    def alignment_matrix(self) -> list[dict]:
        with self._lock:
            return [
                {"alignment_id": a.alignment_id, "civ_a": a.civ_a, "civ_b": a.civ_b,
                 "topic": a.topic, "alignment_score": a.alignment_score,
                 "assessed_at": a.assessed_at.isoformat()}
                for a in self._assessments.values()
            ]


cross_civilization_alignment = CrossCivilizationAlignment()

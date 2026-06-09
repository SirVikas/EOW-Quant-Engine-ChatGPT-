"""CTAO — Recommendation Cemetery: graveyard of failed/rejected/harmful recommendations."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class BuriedRecommendation:
    rec_id: str
    original_description: str
    reason_buried: str
    failure_evidence: str
    buried_at: float
    never_suggest_again: bool
    lesson_learned: str


class RecommendationCemetery:
    def __init__(self):
        self._lock = threading.RLock()
        self._buried: List[BuriedRecommendation] = []

    def bury(self, rec_id: str, original_description: str, reason_buried: str,
             failure_evidence: str, lesson_learned: str, never_suggest_again: bool = True) -> dict:
        with self._lock:
            b = BuriedRecommendation(
                rec_id=rec_id,
                original_description=original_description,
                reason_buried=reason_buried,
                failure_evidence=failure_evidence,
                buried_at=time.time(),
                never_suggest_again=never_suggest_again,
                lesson_learned=lesson_learned,
            )
            self._buried.append(b)
            return asdict(b)

    def is_blacklisted(self, description_keywords: str) -> bool:
        with self._lock:
            keywords = description_keywords.lower().split()
            for b in self._buried:
                if not b.never_suggest_again:
                    continue
                desc_lower = b.original_description.lower()
                if any(kw in desc_lower for kw in keywords):
                    return True
            return False

    def all_buried(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(b) for b in self._buried[-limit:]]

    def cemetery_stats(self) -> dict:
        with self._lock:
            total = len(self._buried)
            by_reason: dict = {}
            for b in self._buried:
                by_reason[b.reason_buried] = by_reason.get(b.reason_buried, 0) + 1
            blacklisted = sum(1 for b in self._buried if b.never_suggest_again)
            lessons = sum(1 for b in self._buried if b.lesson_learned)
            return {
                "total_buried": total,
                "by_reason": by_reason,
                "blacklisted_count": blacklisted,
                "lessons_count": lessons,
            }


recommendation_cemetery = RecommendationCemetery()

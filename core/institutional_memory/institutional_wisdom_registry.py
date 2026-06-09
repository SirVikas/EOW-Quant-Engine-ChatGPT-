"""Institutional Wisdom Registry — elevated principles distilled from archived lessons."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


def _compute_status(times_validated: int, confidence: float) -> str:
    if times_validated >= 10 and confidence >= 0.85:
        return "CANONICAL"
    if times_validated >= 5 and confidence >= 0.7:
        return "ESTABLISHED"
    return "TENTATIVE"


@dataclass
class Wisdom:
    wisdom_id: str
    principle: str
    domain: str
    confidence: float  # 0-1
    supporting_lessons: List[str]
    times_validated: int
    times_contradicted: int
    status: str  # TENTATIVE/ESTABLISHED/CANONICAL/DEPRECATED


class InstitutionalWisdomRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._wisdom: dict[str, Wisdom] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"WIS-{self._counter:03d}"

    def record(self, principle: str, domain: str, confidence: float = 0.5) -> str:
        with self._lock:
            wisdom_id = self._next_id()
            w = Wisdom(
                wisdom_id=wisdom_id,
                principle=principle,
                domain=domain,
                confidence=confidence,
                supporting_lessons=[],
                times_validated=0,
                times_contradicted=0,
                status=_compute_status(0, confidence),
            )
            self._wisdom[wisdom_id] = w
            return wisdom_id

    def validate(self, wisdom_id: str) -> bool:
        with self._lock:
            w = self._wisdom.get(wisdom_id)
            if w is None:
                return False
            w.times_validated += 1
            w.status = _compute_status(w.times_validated, w.confidence)
            return True

    def contradict(self, wisdom_id: str) -> bool:
        with self._lock:
            w = self._wisdom.get(wisdom_id)
            if w is None:
                return False
            w.times_contradicted += 1
            w.confidence = max(0.0, w.confidence - 0.1)
            w.status = _compute_status(w.times_validated, w.confidence)
            return True

    def canonical_wisdom(self) -> List[dict]:
        with self._lock:
            return [asdict(w) for w in self._wisdom.values()
                    if w.status in ("CANONICAL", "ESTABLISHED")]

    def all_wisdom(self) -> List[dict]:
        with self._lock:
            return [asdict(w) for w in self._wisdom.values()]

    def wisdom_stats(self) -> dict:
        with self._lock:
            by_domain: dict[str, int] = {}
            counts = {"CANONICAL": 0, "ESTABLISHED": 0, "TENTATIVE": 0, "DEPRECATED": 0}
            for w in self._wisdom.values():
                counts[w.status] = counts.get(w.status, 0) + 1
                by_domain[w.domain] = by_domain.get(w.domain, 0) + 1
            return {
                "total": len(self._wisdom),
                "canonical": counts["CANONICAL"],
                "established": counts["ESTABLISHED"],
                "tentative": counts["TENTATIVE"],
                "deprecated": counts["DEPRECATED"],
                "by_domain": by_domain,
            }


institutional_wisdom_registry = InstitutionalWisdomRegistry()

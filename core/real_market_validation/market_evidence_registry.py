"""Market Evidence Registry — tracks real-market observations for validation subjects."""
import threading
import time
from dataclasses import dataclass, field


@dataclass
class MarketEvidence:
    evidence_id: str
    subject_id: str
    subject_type: str  # RECOMMENDATION/EVOLUTION/STRATEGY/POLICY
    market_condition: str
    observation_date: float
    confirmed: bool
    confidence: float  # 0-1
    notes: str
    created_at: float


class MarketEvidenceRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._evidence: dict[str, MarketEvidence] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"MEV-{self._counter:03d}"

    def record(self, subject_id: str, subject_type: str, market_condition: str,
               confidence: float, notes: str = "") -> str:
        with self._lock:
            ev_id = self._next_id()
            self._evidence[ev_id] = MarketEvidence(
                evidence_id=ev_id,
                subject_id=subject_id,
                subject_type=subject_type,
                market_condition=market_condition,
                observation_date=time.time(),
                confirmed=False,
                confidence=confidence,
                notes=notes,
                created_at=time.time(),
            )
            return ev_id

    def confirm(self, evidence_id: str) -> bool:
        with self._lock:
            if evidence_id in self._evidence:
                self._evidence[evidence_id].confirmed = True
                return True
            return False

    def all_evidence(self, subject_type: str = None, confirmed_only: bool = False) -> list:
        with self._lock:
            items = list(self._evidence.values())
            if subject_type:
                items = [e for e in items if e.subject_type == subject_type]
            if confirmed_only:
                items = [e for e in items if e.confirmed]
            return [vars(e) for e in items]

    def evidence_stats(self) -> dict:
        with self._lock:
            items = list(self._evidence.values())
            total = len(items)
            confirmed = sum(1 for e in items if e.confirmed)
            by_type: dict = {}
            for e in items:
                by_type[e.subject_type] = by_type.get(e.subject_type, 0) + 1
            return {
                "total": total,
                "confirmed": confirmed,
                "unconfirmed": total - confirmed,
                "by_subject_type": by_type,
                "confirmation_rate": confirmed / total if total else 0.0,
            }


market_evidence_registry = MarketEvidenceRegistry()

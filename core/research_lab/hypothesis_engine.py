"""Hypothesis engine for institutional research lab."""
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class Hypothesis:
    hyp_id: str
    statement: str
    domain: str
    testability: str
    supporting_evidence: list
    refuting_evidence: list
    status: str
    confidence: float
    created_at: str


class HypothesisEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._hypotheses: list = []
        self._counter = 0

    def propose(self, statement: str, domain: str, testability: str = "TESTABLE") -> str:
        with self._lock:
            self._counter += 1
            hyp_id = f"HYP-{self._counter:03d}"
            h = Hypothesis(
                hyp_id=hyp_id, statement=statement, domain=domain,
                testability=testability, supporting_evidence=[], refuting_evidence=[],
                status="PROPOSED", confidence=0.5, created_at=datetime.utcnow().isoformat(),
            )
            self._hypotheses.append(h)
            return hyp_id

    def add_evidence(self, hyp_id: str, evidence: str, supports: bool = True) -> bool:
        with self._lock:
            for h in self._hypotheses:
                if h.hyp_id == hyp_id:
                    if supports:
                        h.supporting_evidence.append(evidence)
                    else:
                        h.refuting_evidence.append(evidence)
                    total = len(h.supporting_evidence) + len(h.refuting_evidence)
                    h.confidence = len(h.supporting_evidence) / (total + 0.01)
                    return True
            return False

    def evaluate(self, hyp_id: str) -> dict:
        with self._lock:
            for h in self._hypotheses:
                if h.hyp_id == hyp_id:
                    h.status = "TESTING"
                    if h.confidence >= 0.75:
                        h.status = "CONFIRMED"
                    elif h.confidence <= 0.25:
                        h.status = "REFUTED"
                    else:
                        h.status = "INCONCLUSIVE"
                    return asdict(h)
            return {}

    def all_hypotheses(self, status_filter: Optional[str] = None) -> list:
        with self._lock:
            if status_filter:
                return [asdict(h) for h in self._hypotheses if h.status == status_filter]
            return [asdict(h) for h in self._hypotheses]

    def hypothesis_stats(self) -> dict:
        with self._lock:
            total = len(self._hypotheses)
            confirmed = sum(1 for h in self._hypotheses if h.status == "CONFIRMED")
            refuted = sum(1 for h in self._hypotheses if h.status == "REFUTED")
            inconclusive = sum(1 for h in self._hypotheses if h.status == "INCONCLUSIVE")
            testing = sum(1 for h in self._hypotheses if h.status == "TESTING")
            by_domain: dict = {}
            for h in self._hypotheses:
                by_domain[h.domain] = by_domain.get(h.domain, 0) + 1
            return {"total": total, "confirmed": confirmed, "refuted": refuted,
                    "inconclusive": inconclusive, "testing": testing, "by_domain": by_domain}


hypothesis_engine = HypothesisEngine()

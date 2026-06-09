"""Decision Quality Engine — scores decision quality."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class QualityRecord:
    quality_id: str
    decision_id: str
    quality_score: float
    quality_factors: dict
    scored_at: datetime = field(default_factory=datetime.utcnow)


class DecisionQualityEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[QualityRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DQE-{self._counter:03d}"

    def score_decision(self, decision_id: str) -> dict:
        from core.decision_intelligence.decision_registry import decision_registry
        with self._lock:
            dec = decision_registry.get(decision_id)
            if dec is None:
                return {"decision_id": decision_id, "quality_score": 0, "reason": "not found"}
            # Score = confidence if no outcome, else confidence * (1.0 if outcome matches expected else 0.5)
            score = dec.confidence_pct
            factors = {"confidence": dec.confidence_pct}
            if dec.actual_outcome is not None:
                match = dec.actual_outcome == dec.expected_outcome
                score = dec.confidence_pct * (1.0 if match else 0.5)
                factors["outcome_match"] = match
            score = min(100.0, max(0.0, score))
            rec = QualityRecord(self._next_id(), decision_id, score, factors)
            self._records.append(rec)
            return vars(rec)

    def top_quality_decisions(self, n: int = 10) -> List[dict]:
        with self._lock:
            sorted_recs = sorted(self._records, key=lambda r: r.quality_score, reverse=True)
            return [vars(r) for r in sorted_recs[:n]]


decision_quality_engine = DecisionQualityEngine()

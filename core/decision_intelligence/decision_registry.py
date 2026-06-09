"""Decision Registry — tracks decisions made by the system."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class DecisionRecord:
    decision_id: str
    domain: str
    decision_text: str
    expected_outcome: str
    actual_outcome: Optional[str]
    confidence_pct: float
    made_at: datetime = field(default_factory=datetime.utcnow)


class DecisionRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._decisions: List[DecisionRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DEC-{self._counter:03d}"

    def record(self, domain: str, decision_text: str, expected_outcome: str, confidence_pct: float) -> DecisionRecord:
        with self._lock:
            rec = DecisionRecord(
                decision_id=self._next_id(),
                domain=domain,
                decision_text=decision_text,
                expected_outcome=expected_outcome,
                actual_outcome=None,
                confidence_pct=confidence_pct,
            )
            self._decisions.append(rec)
            return rec

    def update_outcome(self, decision_id: str, actual_outcome: str) -> bool:
        with self._lock:
            for d in self._decisions:
                if d.decision_id == decision_id:
                    d.actual_outcome = actual_outcome
                    return True
            return False

    def all_decisions(self) -> List[dict]:
        with self._lock:
            return [vars(d) for d in self._decisions]

    def get(self, decision_id: str) -> Optional[DecisionRecord]:
        with self._lock:
            return next((d for d in self._decisions if d.decision_id == decision_id), None)


decision_registry = DecisionRegistry()

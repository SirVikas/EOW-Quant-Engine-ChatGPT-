"""Decision Regret Tracker — tracks decisions with bad outcomes."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


RegretMagnitude = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass
class RegretRecord:
    regret_id: str
    decision_id: str
    regret_magnitude: RegretMagnitude
    lesson: str
    recorded_at: datetime = field(default_factory=datetime.utcnow)


class DecisionRegretTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[RegretRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RGT-{self._counter:03d}"

    def record_regret(self, decision_id: str, regret_magnitude: RegretMagnitude, lesson: str) -> RegretRecord:
        with self._lock:
            rec = RegretRecord(self._next_id(), decision_id, regret_magnitude, lesson)
            self._records.append(rec)
            return rec

    def regret_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for r in self._records:
                summary[r.regret_magnitude] = summary.get(r.regret_magnitude, 0) + 1
            return {"total_regrets": len(self._records), "by_magnitude": summary}

    def high_regret_decisions(self) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._records if r.regret_magnitude == "HIGH"]


decision_regret_tracker = DecisionRegretTracker()

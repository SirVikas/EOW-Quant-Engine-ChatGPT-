"""PCCP — Decision Ledger: immutable record of every PHOENIX system decision."""
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Decision:
    decision_id: str
    title: str
    reason: str
    source_layers: List[str]
    confidence: float
    outcome: str
    outcome_recorded_at: float
    timestamp: float


class DecisionLedger:
    def __init__(self):
        self._lock = threading.RLock()
        self._decisions: List[Decision] = []

    def record(self, title: str, reason: str, source_layers: List[str], confidence: float) -> str:
        with self._lock:
            decision_id = str(uuid.uuid4())
            d = Decision(
                decision_id=decision_id,
                title=title,
                reason=reason,
                source_layers=source_layers,
                confidence=confidence,
                outcome="PENDING",
                outcome_recorded_at=0.0,
                timestamp=time.time(),
            )
            self._decisions.append(d)
            return decision_id

    def record_outcome(self, decision_id: str, outcome: str) -> dict:
        with self._lock:
            for d in self._decisions:
                if d.decision_id == decision_id:
                    d.outcome = outcome
                    d.outcome_recorded_at = time.time()
                    return {"updated": decision_id, "outcome": outcome}
            return {"error": f"Decision {decision_id} not found"}

    def all_decisions(self, limit: int = 100) -> List[dict]:
        with self._lock:
            return [asdict(d) for d in self._decisions[-limit:]]

    def pending_decisions(self) -> List[dict]:
        with self._lock:
            return [asdict(d) for d in self._decisions if d.outcome == "PENDING"]

    def ledger_stats(self) -> dict:
        with self._lock:
            total = len(self._decisions)
            pending = sum(1 for d in self._decisions if d.outcome == "PENDING")
            with_outcomes = total - pending
            avg_conf = (sum(d.confidence for d in self._decisions) / total) if total > 0 else 0.0
            return {
                "total": total,
                "pending": pending,
                "with_outcomes": with_outcomes,
                "avg_confidence": round(avg_conf, 4),
            }


decision_ledger = DecisionLedger()

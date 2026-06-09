"""Council Engine — manages ecosystem governance council decisions."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CouncilDecision:
    decision_id: str
    topic: str
    decision_text: str
    voting_nodes: list
    votes_for: int
    votes_against: int
    outcome: str
    decided_at: Optional[datetime]
    _votes_cast: dict = field(default_factory=dict, repr=False)


class CouncilEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._decisions: dict[str, CouncilDecision] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CGD-{self._counter:03d}"

    def propose(self, topic: str, decision_text: str,
                voting_nodes: list) -> CouncilDecision:
        with self._lock:
            d = CouncilDecision(
                decision_id=self._next_id(),
                topic=topic,
                decision_text=decision_text,
                voting_nodes=list(voting_nodes),
                votes_for=0,
                votes_against=0,
                outcome="PENDING",
                decided_at=None,
            )
            self._decisions[d.decision_id] = d
            return d

    def cast_vote(self, decision_id: str, node: str, vote_for: bool) -> bool:
        with self._lock:
            d = self._decisions.get(decision_id)
            if not d or d.outcome != "PENDING":
                return False
            if node in d._votes_cast:
                return False  # already voted
            d._votes_cast[node] = vote_for
            if vote_for:
                d.votes_for += 1
            else:
                d.votes_against += 1
            # Resolve if all nodes voted
            if len(d._votes_cast) >= len(d.voting_nodes):
                d.outcome = "PASSED" if d.votes_for > d.votes_against else "FAILED"
                d.decided_at = datetime.utcnow()
            return True

    def pending_decisions(self) -> list[dict]:
        with self._lock:
            return [
                {"decision_id": d.decision_id, "topic": d.topic,
                 "decision_text": d.decision_text, "votes_for": d.votes_for,
                 "votes_against": d.votes_against}
                for d in self._decisions.values() if d.outcome == "PENDING"
            ]

    def council_summary(self) -> dict:
        with self._lock:
            by_outcome: dict[str, int] = {}
            for d in self._decisions.values():
                by_outcome[d.outcome] = by_outcome.get(d.outcome, 0) + 1
            return {"total_decisions": len(self._decisions), "by_outcome": by_outcome}


council_engine = CouncilEngine()

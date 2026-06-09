"""Board Decision Registry — tracks decisions submitted to the executive board."""
import threading
import time
from dataclasses import dataclass


@dataclass
class BoardDecision:
    decision_id: str
    title: str
    decision_type: str  # STRATEGIC/EVOLUTION/RISK/CAPITAL/GOVERNANCE
    submitted_by: str
    status: str  # SUBMITTED/UNDER_REVIEW/APPROVED/REJECTED/DEFERRED
    decision_rationale: str
    board_notes: str
    submitted_at: float
    decided_at: float


class BoardDecisionRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._decisions: dict[str, BoardDecision] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"BRD-{self._counter:03d}"

    def submit(self, title: str, decision_type: str, submitted_by: str,
               rationale: str) -> str:
        with self._lock:
            did = self._next_id()
            self._decisions[did] = BoardDecision(
                decision_id=did,
                title=title,
                decision_type=decision_type,
                submitted_by=submitted_by,
                status="SUBMITTED",
                decision_rationale=rationale,
                board_notes="",
                submitted_at=time.time(),
                decided_at=0.0,
            )
            return did

    def decide(self, decision_id: str, status: str, board_notes: str = "") -> bool:
        with self._lock:
            d = self._decisions.get(decision_id)
            if not d:
                return False
            d.status = status
            d.board_notes = board_notes
            d.decided_at = time.time()
            return True

    def all_decisions(self, status_filter: str = None) -> list:
        with self._lock:
            items = list(self._decisions.values())
            if status_filter:
                items = [d for d in items if d.status == status_filter]
            return [vars(d) for d in items]

    def pending_review(self) -> list:
        with self._lock:
            return [vars(d) for d in self._decisions.values()
                    if d.status in ("SUBMITTED", "UNDER_REVIEW")]

    def decision_stats(self) -> dict:
        with self._lock:
            items = list(self._decisions.values())
            total = len(items)
            by_status: dict = {}
            by_type: dict = {}
            approved = 0
            decided = 0
            for d in items:
                by_status[d.status] = by_status.get(d.status, 0) + 1
                by_type[d.decision_type] = by_type.get(d.decision_type, 0) + 1
                if d.decided_at > 0:
                    decided += 1
                if d.status == "APPROVED":
                    approved += 1
            return {
                "total": total,
                "by_status": by_status,
                "by_type": by_type,
                "approval_rate": approved / decided if decided else 0.0,
            }


board_decision_registry = BoardDecisionRegistry()

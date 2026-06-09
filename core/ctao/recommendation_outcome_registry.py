"""Recommendation Outcome Registry — lifecycle tracking for CTAO recommendations."""
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class OutcomeRecord:
    rec_id: str
    status: str  # PROPOSED/APPROVED/IMPLEMENTED/ACTIVE/REJECTED/RETIRED
    proposed_at: float
    approved_at: Optional[float]
    implemented_at: Optional[float]
    retired_at: Optional[float]
    review_30_trades: dict
    review_100_trades: dict
    long_term_review: dict
    lifecycle_notes: list


class RecommendationOutcomeRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, OutcomeRecord] = {}

    def propose(self, rec_id: str) -> bool:
        with self._lock:
            self._records[rec_id] = OutcomeRecord(
                rec_id=rec_id,
                status="PROPOSED",
                proposed_at=time.time(),
                approved_at=None,
                implemented_at=None,
                retired_at=None,
                review_30_trades={},
                review_100_trades={},
                long_term_review={},
                lifecycle_notes=[],
            )
            return True

    def approve(self, rec_id: str) -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            rec.status = "APPROVED"
            rec.approved_at = time.time()
            return True

    def implement(self, rec_id: str) -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            rec.status = "IMPLEMENTED"
            rec.implemented_at = time.time()
            return True

    def retire(self, rec_id: str, reason: str = "") -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            rec.status = "RETIRED"
            rec.retired_at = time.time()
            if reason:
                rec.lifecycle_notes.append(f"Retired: {reason}")
            return True

    def reject(self, rec_id: str, reason: str = "") -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            rec.status = "REJECTED"
            if reason:
                rec.lifecycle_notes.append(f"Rejected: {reason}")
            return True

    def record_review(self, rec_id: str, window: str, result_dict: dict) -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            if window == "30_trades":
                rec.review_30_trades = result_dict
            elif window == "100_trades":
                rec.review_100_trades = result_dict
            elif window == "long_term":
                rec.long_term_review = result_dict
            return True

    def add_note(self, rec_id: str, note: str) -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            rec.lifecycle_notes.append(note)
            return True

    def get_lifecycle(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            rec = self._records.get(rec_id)
            return asdict(rec) if rec else None

    def all_outcomes(self, status_filter: Optional[str] = None) -> list:
        with self._lock:
            if status_filter:
                return [asdict(r) for r in self._records.values() if r.status == status_filter]
            return [asdict(r) for r in self._records.values()]

    def outcome_stats(self) -> dict:
        with self._lock:
            recs = list(self._records.values())
            by_status: dict[str, int] = {}
            for r in recs:
                by_status[r.status] = by_status.get(r.status, 0) + 1
            return {
                "total": len(recs),
                "by_status": by_status,
                "with_30_trade_review": sum(1 for r in recs if r.review_30_trades),
                "with_100_trade_review": sum(1 for r in recs if r.review_100_trades),
                "with_long_term_review": sum(1 for r in recs if r.long_term_review),
            }


recommendation_outcome_registry = RecommendationOutcomeRegistry()

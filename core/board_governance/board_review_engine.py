"""Board Review Engine — individual board member reviews for decisions."""
import threading
import time
from dataclasses import dataclass, field


@dataclass
class BoardReview:
    review_id: str
    decision_id: str
    reviewer: str
    review_score: float  # 0-1
    recommendation: str  # APPROVE/REJECT/DEFER
    concerns: list
    reviewed_at: float


class BoardReviewEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._reviews: list[BoardReview] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"BRV-{self._counter:03d}"

    def submit_review(self, decision_id: str, reviewer: str, score: float,
                       recommendation: str, concerns: list = None) -> str:
        with self._lock:
            rid = self._next_id()
            self._reviews.append(BoardReview(
                review_id=rid,
                decision_id=decision_id,
                reviewer=reviewer,
                review_score=score,
                recommendation=recommendation,
                concerns=concerns or [],
                reviewed_at=time.time(),
            ))
            return rid

    def get_reviews(self, decision_id: str) -> list:
        with self._lock:
            return [vars(r) for r in self._reviews if r.decision_id == decision_id]

    def board_consensus(self, decision_id: str) -> dict:
        with self._lock:
            reviews = [r for r in self._reviews if r.decision_id == decision_id]
            if not reviews:
                return {"consensus": "NO_REVIEWS", "avg_score": 0.0, "vote_breakdown": {}}
            votes: dict = {}
            scores = []
            for r in reviews:
                votes[r.recommendation] = votes.get(r.recommendation, 0) + 1
                scores.append(r.review_score)
            consensus = max(votes, key=votes.get)
            return {
                "consensus": consensus,
                "avg_score": sum(scores) / len(scores),
                "vote_breakdown": votes,
            }


board_review_engine = BoardReviewEngine()

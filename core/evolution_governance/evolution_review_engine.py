"""
PHOENIX Evolution Governance — Evolution Review Engine
Manages reviews for evolution proposals.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
import uuid


@dataclass
class Review:
    review_id: str
    evo_id: str
    reviewer: str
    review_type: str  # SIMULATION/IMPACT/RISK/COMPLIANCE
    findings: List[str]
    score: float
    recommendation: str  # APPROVE/REJECT/DEFER
    reviewed_at: str


class EvolutionReviewEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._reviews: Dict[str, Review] = {}

    def submit_review(
        self,
        evo_id: str,
        reviewer: str,
        review_type: str,
        findings: list,
        score: float,
        recommendation: str,
    ) -> dict:
        review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
        review = Review(
            review_id=review_id,
            evo_id=evo_id,
            reviewer=reviewer,
            review_type=review_type,
            findings=findings,
            score=score,
            recommendation=recommendation,
            reviewed_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._reviews[review_id] = review
        return asdict(review)

    def get_reviews(self, evo_id: str) -> list:
        with self._lock:
            return [asdict(r) for r in self._reviews.values() if r.evo_id == evo_id]

    def review_summary(self, evo_id: str) -> dict:
        reviews = self.get_reviews(evo_id)
        if not reviews:
            return {"evo_id": evo_id, "review_count": 0, "overall_recommendation": "NO_REVIEWS"}

        avg_score = sum(r["score"] for r in reviews) / len(reviews)
        rec_counts: Dict[str, int] = {}
        for r in reviews:
            rec_counts[r["recommendation"]] = rec_counts.get(r["recommendation"], 0) + 1

        overall = max(rec_counts, key=lambda k: rec_counts[k])
        return {
            "evo_id": evo_id,
            "review_count": len(reviews),
            "avg_score": round(avg_score, 4),
            "recommendations_breakdown": rec_counts,
            "overall_recommendation": overall,
        }


evolution_review_engine = EvolutionReviewEngine()

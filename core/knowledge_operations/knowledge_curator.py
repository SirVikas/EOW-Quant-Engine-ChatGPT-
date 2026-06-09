"""Knowledge Curator — curates knowledge quality."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CurationReview:
    review_id: str
    item_id: str
    curator_notes: str
    quality_score: int
    reviewed_at: datetime


class KnowledgeCurator:
    def __init__(self):
        self._lock = threading.RLock()
        self._reviews: dict[str, CurationReview] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"KCR-{self._counter:03d}"

    def curate(self, item_id: str, curator_notes: str, quality_score: int) -> CurationReview:
        with self._lock:
            review = CurationReview(
                review_id=self._next_id(),
                item_id=item_id,
                curator_notes=curator_notes,
                quality_score=max(0, min(100, quality_score)),
                reviewed_at=datetime.utcnow(),
            )
            self._reviews[review.review_id] = review
            return review

    def top_quality_items(self, n: int = 10) -> list[dict]:
        with self._lock:
            # best score per item_id
            best: dict[str, int] = {}
            for r in self._reviews.values():
                best[r.item_id] = max(best.get(r.item_id, 0), r.quality_score)
            sorted_items = sorted(best.items(), key=lambda x: x[1], reverse=True)[:n]
            return [{"item_id": item_id, "quality_score": score} for item_id, score in sorted_items]

    def curation_stats(self) -> dict:
        with self._lock:
            if not self._reviews:
                return {"total_reviews": 0, "avg_quality_score": 0, "items_reviewed": 0}
            scores = [r.quality_score for r in self._reviews.values()]
            items = len({r.item_id for r in self._reviews.values()})
            return {
                "total_reviews": len(self._reviews),
                "avg_quality_score": round(sum(scores) / len(scores), 1),
                "items_reviewed": items,
            }

    def reviews_for(self, item_id: str) -> list[CurationReview]:
        with self._lock:
            return [r for r in self._reviews.values() if r.item_id == item_id]


knowledge_curator = KnowledgeCurator()

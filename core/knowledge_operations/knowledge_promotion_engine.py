"""Knowledge Promotion Engine — handles promotion decisions."""
import threading
from datetime import datetime


class KnowledgePromotionEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._history: list[dict] = []

    def evaluate_for_promotion(self, item_id: str) -> dict:
        # Lazy imports to avoid circular deps
        from core.knowledge_operations.knowledge_curator import knowledge_curator
        from core.knowledge_operations.knowledge_lifecycle_engine import knowledge_lifecycle_engine

        reviews = knowledge_curator.reviews_for(item_id)
        if not reviews:
            return {"item_id": item_id, "eligible": False, "reason": "No curation reviews found"}

        best_score = max(r.quality_score for r in reviews)
        if best_score < 80:
            return {"item_id": item_id, "eligible": False,
                    "reason": f"Quality score {best_score} below threshold 80"}

        item = knowledge_lifecycle_engine._items.get(item_id)
        if not item:
            return {"item_id": item_id, "eligible": False, "reason": "Item not found"}
        if item.stage == "INSTITUTIONAL":
            return {"item_id": item_id, "eligible": False, "reason": "Already at INSTITUTIONAL stage"}
        if item.stage == "RETIRED":
            return {"item_id": item_id, "eligible": False, "reason": "Item is RETIRED"}

        return {"item_id": item_id, "eligible": True,
                "reason": f"Quality score {best_score} >= 80 with {len(reviews)} review(s)"}

    def batch_promote(self) -> list[str]:
        from core.knowledge_operations.knowledge_lifecycle_engine import knowledge_lifecycle_engine

        promoted = []
        with self._lock:
            for item_id in list(knowledge_lifecycle_engine._items.keys()):
                ev = self.evaluate_for_promotion(item_id)
                if ev["eligible"]:
                    knowledge_lifecycle_engine.promote(item_id)
                    self._history.append({
                        "item_id": item_id, "promoted_at": datetime.utcnow().isoformat()
                    })
                    promoted.append(item_id)
        return promoted

    def promotion_history(self) -> list[dict]:
        with self._lock:
            return list(self._history)


knowledge_promotion_engine = KnowledgePromotionEngine()

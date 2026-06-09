"""Knowledge Value Ranker — cross-references importance and decay to compute true value."""
import threading
from typing import List


class KnowledgeValueRanker:
    def __init__(self):
        self._lock = threading.RLock()

    def rank_all(self) -> List[dict]:
        with self._lock:
            from core.meta_knowledge.knowledge_importance_tracker import knowledge_importance_tracker
            from core.meta_knowledge.knowledge_decay_engine import knowledge_decay_engine

            records = knowledge_importance_tracker.all_records()
            ranked = []
            for rec in records:
                decay_rec = knowledge_decay_engine.get_record(rec["subject_id"])
                decay_val = decay_rec["current_value"] if decay_rec else 1.0
                value_score = rec["importance_score"] * decay_val
                ranked.append({**rec, "current_decay_value": decay_val, "value_score": value_score})
            ranked.sort(key=lambda x: x["value_score"], reverse=True)
            return ranked

    def most_valuable(self, limit: int = 10) -> List[dict]:
        with self._lock:
            return self.rank_all()[:limit]

    def least_valuable(self, limit: int = 10) -> List[dict]:
        with self._lock:
            ranked = self.rank_all()
            return ranked[-limit:] if len(ranked) >= limit else ranked

    def value_distribution(self) -> dict:
        with self._lock:
            ranked = self.rank_all()
            if not ranked:
                return {"high_value_count": 0, "medium_value_count": 0,
                        "low_value_count": 0, "avg_value_score": 0}
            total_score = sum(r["value_score"] for r in ranked)
            high = sum(1 for r in ranked if r["value_score"] >= 70)
            medium = sum(1 for r in ranked if 30 <= r["value_score"] < 70)
            low = sum(1 for r in ranked if r["value_score"] < 30)
            return {
                "high_value_count": high,
                "medium_value_count": medium,
                "low_value_count": low,
                "avg_value_score": total_score / len(ranked),
            }


knowledge_value_ranker = KnowledgeValueRanker()

"""Meta-Knowledge Engine — unified interface for knowledge health and prioritization."""
import threading
from datetime import datetime, timezone
from typing import List


class MetaKnowledgeEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def meta_report(self) -> dict:
        with self._lock:
            from core.meta_knowledge.knowledge_value_ranker import knowledge_value_ranker
            from core.meta_knowledge.knowledge_decay_engine import knowledge_decay_engine
            from core.meta_knowledge.knowledge_importance_tracker import knowledge_importance_tracker

            most_valuable = knowledge_value_ranker.most_valuable(5)
            decay_stats = knowledge_decay_engine.decay_stats()
            importance_stats = knowledge_importance_tracker.importance_stats()
            value_dist = knowledge_value_ranker.value_distribution()

            return {
                "most_valuable_knowledge": most_valuable,
                "stale_knowledge_count": decay_stats["stale"] + decay_stats["expired"],
                "importance_distribution": value_dist,
                "knowledge_hierarchy_depth": importance_stats["total"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def what_matters_most(self) -> List[dict]:
        with self._lock:
            from core.meta_knowledge.knowledge_value_ranker import knowledge_value_ranker
            from core.meta_knowledge.knowledge_decay_engine import knowledge_decay_engine

            top5 = knowledge_value_ranker.most_valuable(5)
            result = []
            for item in top5:
                decay_rec = knowledge_decay_engine.get_record(item["subject_id"])
                if decay_rec and decay_rec["status"] in ("STALE", "EXPIRED"):
                    continue
                result.append({
                    "subject_id": item["subject_id"],
                    "knowledge_type": item["knowledge_type"],
                    "value_score": item["value_score"],
                    "explanation": f"High importance ({item['importance_score']:.1f}) with {item['current_decay_value']:.2f} freshness",
                })
            return result

    def prune_candidates(self) -> List[dict]:
        with self._lock:
            from core.meta_knowledge.knowledge_decay_engine import knowledge_decay_engine
            from core.meta_knowledge.knowledge_value_ranker import knowledge_value_ranker

            expired = [r for r in knowledge_decay_engine.stale_knowledge()
                       if r["status"] == "EXPIRED"]
            least = knowledge_value_ranker.least_valuable(10)
            seen = {r["subject_id"] for r in expired}
            combined = list(expired)
            for item in least:
                if item["subject_id"] not in seen:
                    combined.append(item)
            return combined


meta_knowledge_engine = MetaKnowledgeEngine()

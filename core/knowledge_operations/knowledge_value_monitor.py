"""Knowledge Value Monitor — master KOS engine."""
import threading


class KnowledgeValueMonitor:
    def __init__(self):
        self._lock = threading.RLock()

    def kos_report(self) -> dict:
        from core.knowledge_operations.knowledge_lifecycle_engine import knowledge_lifecycle_engine
        from core.knowledge_operations.knowledge_curator import knowledge_curator

        summary = knowledge_lifecycle_engine.lifecycle_summary()
        curator_stats = knowledge_curator.curation_stats()
        institutional_items = knowledge_lifecycle_engine.by_stage("INSTITUTIONAL")

        # recently promoted = items that have promoted_at set
        recently_promoted = [
            {"item_id": i.item_id, "title": i.title, "promoted_at": i.promoted_at.isoformat()}
            for i in knowledge_lifecycle_engine._items.values()
            if i.promoted_at is not None
        ][-10:]

        return {
            "total_items": summary["total_items"],
            "by_stage": summary["by_stage"],
            "avg_quality_score": curator_stats.get("avg_quality_score", 0),
            "institutional_items_count": len(institutional_items),
            "recently_promoted": recently_promoted,
        }

    def one_liner(self) -> str:
        report = self.kos_report()
        return (f"KOS: {report['total_items']} items | "
                f"{report['institutional_items_count']} institutional | "
                f"avg quality {report['avg_quality_score']}")


knowledge_value_monitor = KnowledgeValueMonitor()

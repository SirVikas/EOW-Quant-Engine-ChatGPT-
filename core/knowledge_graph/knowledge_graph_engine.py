"""Knowledge Graph Engine — Orchestrates entity/relationship creation and querying."""
import threading
from typing import Optional


class KnowledgeGraphEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def add_finding_chain(
        self,
        finding_id: str,
        finding_label: str,
        root_cause_label: str,
        recommendation_label: str,
        outcome_label: Optional[str] = None,
        trust_delta: Optional[float] = None,
    ) -> dict:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        f_id = entity_registry.register("FINDING", finding_label, {"finding_id": finding_id})
        rc_id = entity_registry.register("ROOT_CAUSE", root_cause_label)
        rec_id = entity_registry.register("RECOMMENDATION", recommendation_label)

        relationship_registry.create(f_id, rc_id, "CAUSED_BY", "Finding caused by root cause")
        relationship_registry.create(rc_id, rec_id, "LED_TO", "Root cause led to recommendation")

        chain = {"finding_entity_id": f_id, "root_cause_entity_id": rc_id, "recommendation_entity_id": rec_id}

        if outcome_label:
            out_id = entity_registry.register("OUTCOME", outcome_label)
            relationship_registry.create(rec_id, out_id, "LED_TO", "Recommendation led to outcome")
            chain["outcome_entity_id"] = out_id

        if trust_delta is not None:
            ts_id = entity_registry.register("TRUST_SCORE", f"TrustDelta:{trust_delta}", {"delta": trust_delta})
            relationship_registry.create(chain.get("outcome_entity_id", rec_id), ts_id, "IMPROVES", "Improves trust score")
            chain["trust_score_entity_id"] = ts_id

        return chain

    def query_chain(self, start_id: str) -> list:
        from core.knowledge_graph.graph_query_engine import graph_query_engine
        return graph_query_engine.causal_chain(start_id)

    def full_graph_export(self) -> dict:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry
        from core.knowledge_graph.graph_metrics import graph_metrics

        return {
            "entities": entity_registry.all_entities(),
            "relationships": relationship_registry.all_relationships(),
            "metrics": graph_metrics.coverage_report(),
        }

    def kg_status(self) -> dict:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry
        from core.knowledge_graph.graph_metrics import graph_metrics

        return {
            "entity_count": entity_registry.entity_count(),
            "relationship_count": len(relationship_registry.all_relationships()),
            "coverage": graph_metrics.coverage_report(),
        }


knowledge_graph_engine = KnowledgeGraphEngine()

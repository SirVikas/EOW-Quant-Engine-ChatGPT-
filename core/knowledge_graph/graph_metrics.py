"""Graph Metrics — Coverage and centrality analytics for the Knowledge Graph."""
import threading


class GraphMetrics:
    def __init__(self):
        self._lock = threading.RLock()

    def centrality(self) -> dict:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        degree: dict[str, int] = {}
        for rel in relationship_registry.all_relationships():
            degree[rel["source_id"]] = degree.get(rel["source_id"], 0) + 1
            degree[rel["target_id"]] = degree.get(rel["target_id"], 0) + 1
        sorted_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_nodes[:10])

    def orphan_entities(self) -> list:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        connected = set()
        for rel in relationship_registry.all_relationships():
            connected.add(rel["source_id"])
            connected.add(rel["target_id"])
        return [e for e in entity_registry.all_entities() if e["entity_id"] not in connected]

    def coverage_report(self) -> dict:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        entities = entity_registry.all_entities()
        relationships = relationship_registry.all_relationships()
        total_e = len(entities)
        total_r = len(relationships)

        degree: dict[str, int] = {}
        for rel in relationships:
            degree[rel["source_id"]] = degree.get(rel["source_id"], 0) + 1
            degree[rel["target_id"]] = degree.get(rel["target_id"], 0) + 1

        avg_conn = sum(degree.values()) / total_e if total_e else 0
        most_connected = max(degree, key=lambda k: degree[k]) if degree else None
        types_covered = list({e["entity_type"] for e in entities})

        return {
            "total_entities": total_e,
            "total_relationships": total_r,
            "entity_types_covered": types_covered,
            "avg_connections": round(avg_conn, 2),
            "most_connected": most_connected,
        }

    def causal_completeness(self) -> float:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.graph_query_engine import graph_query_engine

        findings = entity_registry.all_entities(entity_type="FINDING")
        if not findings:
            return 0.0
        complete = 0
        for f in findings:
            chain = graph_query_engine.causal_chain(f["entity_id"])
            types_in_chain = {n["entity_type"] for n in chain}
            if "OUTCOME" in types_in_chain:
                complete += 1
        return round(complete / len(findings), 4)


graph_metrics = GraphMetrics()

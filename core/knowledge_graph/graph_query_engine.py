"""Graph Query Engine — BFS traversal and path-finding on Knowledge Graph."""
import threading
from collections import deque
from typing import Optional


class GraphQueryEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def causal_chain(self, start_entity_id: str, max_depth: int = 6) -> list:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        visited = set()
        queue = deque([(start_entity_id, 0, None)])
        result = []
        while queue:
            eid, depth, rel_label = queue.popleft()
            if eid in visited or depth > max_depth:
                continue
            visited.add(eid)
            entity = entity_registry.get(eid)
            if entity:
                entry = dict(entity)
                entry["relationship_label"] = rel_label
                entry["depth"] = depth
                result.append(entry)
            for rel in relationship_registry.get_outgoing(eid):
                if rel["target_id"] not in visited:
                    queue.append((rel["target_id"], depth + 1, rel["label"]))
        return result

    def find_path(self, source_id: str, target_id: str) -> list:
        from core.knowledge_graph.relationship_registry import relationship_registry

        visited = set()
        queue = deque([(source_id, [source_id])])
        while queue:
            current, path = queue.popleft()
            if current == target_id:
                return path
            if current in visited:
                continue
            visited.add(current)
            for rel in relationship_registry.get_outgoing(current):
                nxt = rel["target_id"]
                if nxt not in visited:
                    queue.append((nxt, path + [nxt]))
        return []

    def root_causes_of(self, entity_id: str) -> list:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        visited = set()
        queue = deque([entity_id])
        roots = []
        while queue:
            eid = queue.popleft()
            if eid in visited:
                continue
            visited.add(eid)
            incoming = relationship_registry.get_incoming(eid)
            caused_by = [r for r in incoming if r["rel_type"] == "CAUSED_BY"]
            if not caused_by:
                e = entity_registry.get(eid)
                if e:
                    roots.append(e)
            else:
                for rel in caused_by:
                    queue.append(rel["source_id"])
        return roots

    def downstream_impact(self, entity_id: str) -> list:
        from core.knowledge_graph.entity_registry import entity_registry
        from core.knowledge_graph.relationship_registry import relationship_registry

        visited = set()
        queue = deque([entity_id])
        downstream = []
        while queue:
            eid = queue.popleft()
            if eid in visited:
                continue
            visited.add(eid)
            for rel in relationship_registry.get_outgoing(eid):
                if rel["rel_type"] in ("LED_TO", "IMPACTS"):
                    nxt = rel["target_id"]
                    e = entity_registry.get(nxt)
                    if e:
                        downstream.append(e)
                    queue.append(nxt)
        return downstream


graph_query_engine = GraphQueryEngine()

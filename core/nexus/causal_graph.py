"""
PHOENIX NEXUS — Unified Causal Graph  [CLI-01]

Single PHOENIX-wide graph connecting all institutional events, decisions,
recommendations, risks, amendments, and governance rulings.

Node types:
  DISEASE, RECOMMENDATION, DECISION, RISK, AMENDMENT, GOVERNANCE_RULING,
  TRUST_EVENT, AEG_PROMOTION, CASCADE_EVENT, BOARD_DIRECTIVE

Edge types:
  CAUSED_BY, LED_TO, BLOCKED_BY, INFLUENCED, RESOLVED_BY, TRIGGERED

The graph is a lightweight directed adjacency structure (no heavy deps).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


NODE_TYPES = {
    "DISEASE", "RECOMMENDATION", "DECISION", "RISK", "AMENDMENT",
    "GOVERNANCE_RULING", "TRUST_EVENT", "AEG_PROMOTION", "CASCADE_EVENT",
    "BOARD_DIRECTIVE", "SYSTEM_EVENT",
}

EDGE_TYPES = {
    "CAUSED_BY", "LED_TO", "BLOCKED_BY", "INFLUENCED", "RESOLVED_BY", "TRIGGERED",
}


@dataclass
class GraphNode:
    node_id: str
    node_type: str
    label: str
    layer: str          # NEXUS / OBSX / CORTEX / PTP / AEG / PCAO
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    label: str = ""


class UnifiedCausalGraph:
    """
    PHOENIX-wide directed causal graph for cross-layer relationship intelligence.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._adj: Dict[str, Set[str]] = {}   # source → set of target node_ids
        self._seed_founding_nodes()

    def _seed_founding_nodes(self) -> None:
        seeds = [
            ("NODE-NEXUS-CORE",   "SYSTEM_EVENT",    "PHOENIX NEXUS Core",           "NEXUS"),
            ("NODE-OBSX-CORE",    "SYSTEM_EVENT",    "OBSERVATORY-X Core",           "OBSX"),
            ("NODE-CORTEX-CORE",  "SYSTEM_EVENT",    "CORTEX Core",                  "CORTEX"),
            ("NODE-PTP-CORE",     "SYSTEM_EVENT",    "PHOENIX Trust Program Core",   "PTP"),
            ("NODE-AEG-CORE",     "SYSTEM_EVENT",    "AEG Pipeline Core",            "AEG"),
            ("NODE-PCAO-CORE",    "SYSTEM_EVENT",    "PCAO Foundation",              "PCAO"),
        ]
        for nid, ntype, label, layer in seeds:
            self._nodes[nid] = GraphNode(node_id=nid, node_type=ntype, label=label, layer=layer)

    # ── Graph Mutation ────────────────────────────────────────────────────────

    def add_node(self, node_id: str, node_type: str, label: str, layer: str,
                 metadata: Optional[dict] = None) -> GraphNode:
        node = GraphNode(node_id=node_id, node_type=node_type, label=label,
                         layer=layer, metadata=metadata or {})
        with self._lock:
            self._nodes[node_id] = node
        return node

    def add_edge(self, source_id: str, target_id: str, edge_type: str,
                 weight: float = 1.0, label: str = "") -> Optional[GraphEdge]:
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                return None
            edge_id = f"EDGE-{source_id[:8]}-{target_id[:8]}-{int(time.time()*1000)}"
            edge = GraphEdge(edge_id=edge_id, source_id=source_id, target_id=target_id,
                             edge_type=edge_type, weight=weight, label=label)
            self._edges.append(edge)
            self._adj.setdefault(source_id, set()).add(target_id)
        return edge

    # ── Graph Query ───────────────────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[dict]:
        with self._lock:
            n = self._nodes.get(node_id)
        return self._ser_node(n) if n else None

    def neighbors(self, node_id: str) -> List[dict]:
        with self._lock:
            targets = list(self._adj.get(node_id, set()))
            return [self._ser_node(self._nodes[t]) for t in targets if t in self._nodes]

    def edges_from(self, node_id: str) -> List[dict]:
        with self._lock:
            return [self._ser_edge(e) for e in self._edges if e.source_id == node_id]

    def causal_path(self, source_id: str, target_id: str, max_depth: int = 6) -> List[str]:
        """BFS shortest path from source to target."""
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                return []
            visited = {source_id}
            queue = [[source_id]]
            while queue:
                path = queue.pop(0)
                node = path[-1]
                if node == target_id:
                    return path
                if len(path) >= max_depth:
                    continue
                for neighbor in self._adj.get(node, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(path + [neighbor])
        return []

    def impact_analysis(self, node_id: str, max_depth: int = 3) -> dict:
        """What nodes are reachable from this node (downstream impact)."""
        with self._lock:
            reachable = set()
            frontier = {node_id}
            for _ in range(max_depth):
                next_frontier = set()
                for n in frontier:
                    for target in self._adj.get(n, set()):
                        if target not in reachable:
                            reachable.add(target)
                            next_frontier.add(target)
                frontier = next_frontier
            nodes = [self._ser_node(self._nodes[r]) for r in reachable if r in self._nodes]
        return {
            "source_node":     node_id,
            "reachable_count": len(nodes),
            "impacted_nodes":  nodes,
        }

    def global_causal_map(self) -> dict:
        with self._lock:
            nodes = [self._ser_node(n) for n in self._nodes.values()]
            edges = [self._ser_edge(e) for e in self._edges]
        by_layer: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for n in nodes:
            by_layer[n["layer"]] = by_layer.get(n["layer"], 0) + 1
            by_type[n["node_type"]] = by_type.get(n["node_type"], 0) + 1
        return {
            "node_count":  len(nodes),
            "edge_count":  len(edges),
            "nodes_by_layer": by_layer,
            "nodes_by_type":  by_type,
            "nodes":       nodes,
            "edges":       edges,
        }

    def ingest_cross_layer_event(self, cascade: dict) -> None:
        """Auto-populate graph from a CrossLayerIntelligence cascade result."""
        try:
            ctype = cascade.get("cascade_type", "")
            cid   = cascade.get("cascade_id", f"CASCADE-{int(time.time()*1000)}")
            self.add_node(cid, "CASCADE_EVENT", f"Cascade: {ctype}", "NEXUS",
                          metadata={"cascade_type": ctype})
            results = cascade.get("layer_results", {})
            for layer, result in results.items():
                if result.get("status") == "OK":
                    layer_node_id = f"NODE-{layer}-CORE"
                    if layer_node_id in self._nodes:
                        self.add_edge(cid, layer_node_id, "TRIGGERED", label=ctype)
        except Exception:
            pass

    @staticmethod
    def _ser_node(n: GraphNode) -> dict:
        return {"node_id": n.node_id, "node_type": n.node_type, "label": n.label,
                "layer": n.layer, "created_at": n.created_at, "metadata": n.metadata}

    @staticmethod
    def _ser_edge(e: GraphEdge) -> dict:
        return {"edge_id": e.edge_id, "source_id": e.source_id, "target_id": e.target_id,
                "edge_type": e.edge_type, "weight": e.weight, "label": e.label,
                "created_at": e.created_at}


# Singleton
causal_graph = UnifiedCausalGraph()

"""Federation Registry — registry of PHOENIX federation nodes."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


NodeStatus = Literal["ACTIVE", "INACTIVE", "SYNCING"]


@dataclass
class FederationNode:
    node_id: str
    node_name: str
    endpoint: str
    status: NodeStatus
    last_seen: datetime
    capabilities: List[str]


class FederationRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._nodes: List[FederationNode] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"PHX-{self._counter:03d}"

    def register_node(self, node_name: str, endpoint: str, capabilities: List[str]) -> FederationNode:
        with self._lock:
            node = FederationNode(
                node_id=self._next_id(),
                node_name=node_name,
                endpoint=endpoint,
                status="ACTIVE",
                last_seen=datetime.utcnow(),
                capabilities=capabilities,
            )
            self._nodes.append(node)
            return node

    def active_nodes(self) -> List[dict]:
        with self._lock:
            return [vars(n) for n in self._nodes if n.status == "ACTIVE"]

    def federation_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for n in self._nodes:
                summary[n.status] = summary.get(n.status, 0) + 1
            return {"total_nodes": len(self._nodes), "by_status": summary}


federation_registry = FederationRegistry()

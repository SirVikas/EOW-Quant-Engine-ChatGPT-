"""Evidence Lineage — tracks parent/child relationships between evidence items."""
import threading
import time
from dataclasses import dataclass
from collections import deque


@dataclass
class LineageLink:
    link_id: str
    parent_evidence_id: str
    child_evidence_id: str
    relationship: str  # DERIVED_FROM/SUPPORTS/CONTRADICTS/UPDATES/SUPERSEDES
    created_at: float


class EvidenceLineage:
    def __init__(self):
        self._lock = threading.RLock()
        self._links: list[LineageLink] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"LNK-{self._counter:03d}"

    def link(self, parent_id: str, child_id: str, relationship: str) -> str:
        with self._lock:
            link_id = self._next_id()
            self._links.append(LineageLink(
                link_id=link_id,
                parent_evidence_id=parent_id,
                child_evidence_id=child_id,
                relationship=relationship,
                created_at=time.time(),
            ))
            return link_id

    def ancestors(self, evidence_id: str, depth: int = 5) -> list:
        with self._lock:
            result = []
            visited = set()
            queue = deque([(evidence_id, 0)])
            backward_rels = {"DERIVED_FROM", "UPDATES"}
            while queue:
                eid, d = queue.popleft()
                if d >= depth or eid in visited:
                    continue
                visited.add(eid)
                for lnk in self._links:
                    if lnk.child_evidence_id == eid and lnk.relationship in backward_rels:
                        result.append(lnk.parent_evidence_id)
                        queue.append((lnk.parent_evidence_id, d + 1))
            return result

    def descendants(self, evidence_id: str, depth: int = 5) -> list:
        with self._lock:
            result = []
            visited = set()
            queue = deque([(evidence_id, 0)])
            while queue:
                eid, d = queue.popleft()
                if d >= depth or eid in visited:
                    continue
                visited.add(eid)
                for lnk in self._links:
                    if lnk.parent_evidence_id == eid:
                        result.append(lnk.child_evidence_id)
                        queue.append((lnk.child_evidence_id, d + 1))
            return result

    def lineage_chain(self, evidence_id: str) -> dict:
        ancs = self.ancestors(evidence_id)
        descs = self.descendants(evidence_id)
        return {
            "evidence_id": evidence_id,
            "ancestors": ancs,
            "descendants": descs,
            "total_lineage_depth": len(ancs) + len(descs),
        }


evidence_lineage = EvidenceLineage()

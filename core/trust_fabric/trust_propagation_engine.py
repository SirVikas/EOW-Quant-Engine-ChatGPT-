"""
PHOENIX Unified Trust Fabric — Trust Propagation Engine
Propagates trust changes to downstream nodes in the knowledge graph.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone
from typing import List


class TrustPropagationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._propagation_history: List[dict] = []

    def propagate_trust_update(
        self, subject_id: str, new_score: float, reason: str
    ) -> dict:
        from core.trust_fabric.trust_registry import trust_registry

        updates = []
        downstream_ids = []

        try:
            from core.knowledge_graph.knowledge_graph_engine import knowledge_graph_engine
            impact = knowledge_graph_engine.downstream_impact(subject_id)
            downstream_ids = impact.get("downstream_nodes", [])
        except Exception:
            pass

        current = trust_registry.get_trust(subject_id)
        if current:
            old_score = current["trust_score"]
            delta = new_score - old_score
            for ds_id in downstream_ids:
                ds = trust_registry.get_trust(ds_id)
                if ds:
                    dampened_delta = delta * 0.3
                    updated_score = max(0.0, min(1.0, ds["trust_score"] + dampened_delta))
                    trust_registry.set_trust(
                        ds_id, ds["subject_type"], updated_score, ds["evidence_count"]
                    )
                    updates.append({"subject_id": ds_id, "old_score": ds["trust_score"], "new_score": updated_score})

        event = {
            "source": subject_id,
            "new_score": new_score,
            "reason": reason,
            "propagated_to_count": len(updates),
            "updates": updates,
            "propagated_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._propagation_history.append(event)
        return event

    def propagation_history(self, limit: int = 20) -> list:
        with self._lock:
            return list(self._propagation_history[-limit:])


trust_propagation_engine = TrustPropagationEngine()

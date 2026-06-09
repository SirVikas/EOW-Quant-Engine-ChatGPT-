"""
PHOENIX Unified Trust Fabric Engine
Single source of truth for system-wide trust across all dimensions.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone


class TrustFabricEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def unified_trust_report(self) -> dict:
        from core.trust_fabric.trust_registry import trust_registry

        summary = trust_registry.trust_summary()

        pillar_trust = {}
        try:
            from core.trust.trust_validation_registry import trust_validation_registry
            pillar_trust = trust_validation_registry.pillar_statuses()
        except Exception:
            pass

        confidence_summary = {}
        try:
            from core.epistemic.confidence_boundary_engine import confidence_boundary_engine
            confidence_summary = confidence_boundary_engine.confidence_map()
        except Exception:
            pass

        # Fabric health: average trust score
        avg_score = summary.get("avg_score", 0.5)
        fabric_health = round(avg_score * 100, 2)

        return {
            "fabric_health_score": fabric_health,
            "trust_summary": summary,
            "pillar_trust": pillar_trust,
            "confidence_summary": confidence_summary,
            "single_source_truth": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def update_trust(
        self, subject_id: str, subject_type: str, trust_score: float, evidence_count: int
    ) -> dict:
        from core.trust_fabric.trust_registry import trust_registry
        from core.trust_fabric.trust_propagation_engine import trust_propagation_engine

        entry = trust_registry.set_trust(subject_id, subject_type, trust_score, evidence_count)
        propagation = trust_propagation_engine.propagate_trust_update(
            subject_id, trust_score, reason="Trust update via TrustFabricEngine"
        )
        return {"entry": entry, "propagation": propagation}

    def trust_leaderboard(self, limit: int = 10) -> list:
        from core.trust_fabric.trust_registry import trust_registry
        entries = trust_registry.all_trust_entries()
        entries.sort(key=lambda x: x["trust_score"], reverse=True)
        return entries[:limit]


trust_fabric_engine = TrustFabricEngine()

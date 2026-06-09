"""
PHOENIX Evolution Governance — Evolution Approval Engine
Manages approval, rejection, and deployment of evolutions.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional


class EvolutionApprovalEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self.approval_log: List[dict] = []

    def _log(self, evo_id: str, action: str, actor: str, conditions=None):
        with self._lock:
            self.approval_log.append({
                "evo_id": evo_id,
                "action": action,
                "actor": actor,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "conditions": conditions or [],
            })

    def approve(self, evo_id: str, approver: str, conditions: list = None) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry
        evolution_registry.update_status(evo_id, "APPROVED")
        self._log(evo_id, "APPROVED", approver, conditions)
        return {"evo_id": evo_id, "status": "APPROVED", "approver": approver}

    def reject(self, evo_id: str, rejector: str, reason: str) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry
        evolution_registry.update_status(evo_id, "REJECTED")
        self._log(evo_id, "REJECTED", rejector, [reason])
        return {"evo_id": evo_id, "status": "REJECTED", "rejector": rejector}

    def deploy(self, evo_id: str) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry
        evolution_registry.update_status(
            evo_id, "DEPLOYED",
            deployed_at=datetime.now(timezone.utc).isoformat()
        )
        self._log(evo_id, "DEPLOYED", "SYSTEM")
        return {"evo_id": evo_id, "status": "DEPLOYED"}

    def approval_stats(self) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry
        approved = len(evolution_registry.all_evolutions(status_filter="APPROVED"))
        rejected = len(evolution_registry.all_evolutions(status_filter="REJECTED"))
        pending = len(evolution_registry.all_evolutions(status_filter="APPROVED"))  # approved but not yet deployed
        deployed = len(evolution_registry.all_evolutions(status_filter="DEPLOYED"))
        return {
            "total_approved": approved + deployed,
            "total_rejected": rejected,
            "pending_deployment": approved,
        }


evolution_approval_engine = EvolutionApprovalEngine()

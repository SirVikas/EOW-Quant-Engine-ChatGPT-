"""
PHOENIX Evolution Governance — Evolution Proposal Engine
Creates and tracks evolution proposals with duplicate detection.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone
from typing import Dict, List


class EvolutionProposalEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def create_proposal(
        self,
        title: str,
        description: str,
        proposed_by: str,
        evo_type: str,
        rationale: str,
        risk_level: str = "MEDIUM",
    ) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry

        warnings = []
        existing = evolution_registry.all_evolutions(status_filter="PROPOSED")
        title_lower = title.lower()
        for e in existing:
            if e["title"].lower() == title_lower:
                warnings.append(
                    f"Similar proposal already exists: {e['evo_id']} — {e['title']}"
                )
                break

        evo_id = evolution_registry.propose(
            title=title,
            description=description,
            proposed_by=proposed_by,
            evo_type=evo_type,
            rationale=rationale,
            risk_level=risk_level,
        )
        return {"evo_id": evo_id, "warnings": warnings}

    def pending_proposals(self) -> list:
        from core.evolution_governance.evolution_registry import evolution_registry
        return evolution_registry.all_evolutions(status_filter="PROPOSED")

    def proposal_stats(self) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry

        proposed = evolution_registry.all_evolutions(status_filter="PROPOSED")
        all_evos = evolution_registry.all_evolutions()
        risk_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        if proposed:
            avg_risk = sum(risk_map.get(e["risk_level"], 2) for e in proposed) / len(proposed)
        else:
            avg_risk = 0.0
        return {
            "total_proposed": len(all_evos),
            "pending_review": len(proposed),
            "avg_risk_level": round(avg_risk, 2),
        }


evolution_proposal_engine = EvolutionProposalEngine()

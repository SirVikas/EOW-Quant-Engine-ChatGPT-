"""Organizational Evolution Engine — master org design."""
import threading
from datetime import datetime


class OrganizationalEvolutionEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._evolution_log: list[dict] = []

    def evolve(self, proposed_change: str) -> dict:
        from core.organization_design.structure_optimizer import structure_optimizer

        findings = structure_optimizer.analyze()
        record = {
            "proposed_change": proposed_change,
            "analysis": findings,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._evolution_log.append(record)
        return record

    def evolution_history(self) -> list[dict]:
        with self._lock:
            return list(self._evolution_log)

    def org_health_report(self) -> dict:
        from core.organization_design.organization_registry import organization_registry
        from core.organization_design.role_definition_engine import role_definition_engine
        from core.organization_design.structure_optimizer import structure_optimizer

        unit_summary = organization_registry.unit_summary()
        role_catalog = role_definition_engine.role_catalog()
        findings = structure_optimizer.analyze()
        opportunities = [f for f in findings if f["area"] != "Overall"]

        # Simple health score: deduct 10 per opportunity
        health_score = max(0, 100 - len(opportunities) * 10)

        return {
            "total_units": unit_summary["total_units"],
            "total_roles": len(role_catalog),
            "optimization_opportunities": len(opportunities),
            "health_score": health_score,
        }


organizational_evolution_engine = OrganizationalEvolutionEngine()

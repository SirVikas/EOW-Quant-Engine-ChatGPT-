"""Change Impact Assessor — master change management engine."""
import threading

LAYER_MAP = {
    "ARCHITECTURAL": ["Trading Engine", "Risk Engine", "Data Layer", "API Layer"],
    "POLICY": ["Governance Layer", "Reporting Layer"],
    "GOVERNANCE": ["Governance Layer", "Compliance Layer"],
    "STRATEGIC": ["Strategic Layer", "Roadmap"],
}

DOWNTIME_MAP = {"LOW": 0, "MEDIUM": 5, "HIGH": 30, "CRITICAL": 120}


class ChangeImpactAssessor:
    def __init__(self):
        self._lock = threading.RLock()

    def impact_report(self, change_id: str) -> dict:
        from core.change_management.change_registry import change_registry
        with self._lock:
            change = change_registry.get(change_id)
            if change is None:
                return {"change_id": change_id, "error": "not found"}
            affected_layers = LAYER_MAP.get(change.change_type, ["Unknown"])
            downtime = DOWNTIME_MAP.get(change.risk_level, 0)
            rollback_feasibility = "HIGH" if change.risk_level in ("LOW", "MEDIUM") else "MEDIUM"
            return {
                "change_id": change_id,
                "affected_layers": affected_layers,
                "estimated_downtime_mins": downtime,
                "rollback_feasibility": rollback_feasibility,
            }

    def change_management_summary(self) -> dict:
        from core.change_management.change_registry import change_registry
        from core.change_management.change_risk_engine import change_risk_engine
        with self._lock:
            summary = change_registry.change_summary()
            high_risk = change_risk_engine.high_risk_changes()
            return {
                "total_changes": summary["total_changes"],
                "pending_changes": len(change_registry.pending_changes()),
                "high_risk_count": len(high_risk),
                "by_status": summary["by_status"],
            }


change_impact_assessor = ChangeImpactAssessor()

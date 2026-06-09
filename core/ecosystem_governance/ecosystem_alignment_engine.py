"""Ecosystem Alignment Engine — master ecosystem governance."""
import threading


class EcosystemAlignmentEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def ecosystem_governance_report(self) -> dict:
        from core.ecosystem_governance.federation_policy_manager import federation_policy_manager
        from core.ecosystem_governance.cross_instance_audit import cross_instance_audit
        from core.ecosystem_governance.council_engine import council_engine

        active_policies = federation_policy_manager.active_policies()
        audit_summary = cross_instance_audit.audit_summary()
        pending_decisions = council_engine.pending_decisions()

        total = audit_summary.get("total_audits", 0)
        by_result = audit_summary.get("by_result", {})
        compliant = by_result.get("COMPLIANT", 0)
        compliant_pct = round(compliant / total * 100, 1) if total > 0 else 100.0

        if compliant_pct >= 80 and len(pending_decisions) <= 2:
            health = "STRONG"
        elif compliant_pct >= 60:
            health = "MODERATE"
        else:
            health = "WEAK"

        return {
            "active_policies": len(active_policies),
            "compliant_nodes_pct": compliant_pct,
            "pending_council_decisions": len(pending_decisions),
            "governance_health": health,
        }

    def one_liner(self) -> str:
        report = self.ecosystem_governance_report()
        return (f"EcoGov: health={report['governance_health']} | "
                f"policies={report['active_policies']} | "
                f"compliance={report['compliant_nodes_pct']}%")


ecosystem_alignment_engine = EcosystemAlignmentEngine()

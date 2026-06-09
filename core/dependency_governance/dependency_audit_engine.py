"""Dependency Audit Engine — master dependency governance engine."""
import threading


class DependencyAuditEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def audit_report(self) -> dict:
        from core.dependency_governance.vendor_registry import vendor_registry
        from core.dependency_governance.dependency_risk_engine import dependency_risk_engine
        from core.dependency_governance.external_service_monitor import external_service_monitor
        with self._lock:
            vendor_summary = vendor_registry.vendor_summary()
            critical_vendors = vendor_registry.critical_vendors()
            high_risks = dependency_risk_engine.high_severity_risks()
            degraded = external_service_monitor.degraded_vendors()
            # Concentration risk: multiple CRITICAL vendors
            concentration_risk = len(critical_vendors)
            critical_at_risk = len([v for v in critical_vendors if v["vendor_id"] in degraded])
            resilience = (
                "WEAK" if critical_at_risk > 0 or len(high_risks) > 3
                else "MODERATE" if high_risks
                else "STRONG"
            )
            return {
                "total_vendors": vendor_summary["total_vendors"],
                "critical_at_risk": critical_at_risk,
                "concentration_risk_count": concentration_risk,
                "overall_resilience": resilience,
            }

    def one_liner(self) -> str:
        report = self.audit_report()
        return f"Dependency Governance: {report['overall_resilience']}, {report['total_vendors']} vendors, {report['critical_at_risk']} critical at risk"


dependency_audit_engine = DependencyAuditEngine()

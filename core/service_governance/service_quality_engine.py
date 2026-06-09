"""Service Quality Engine — master service governance engine."""
import threading


class ServiceQualityEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def quality_report(self) -> dict:
        from core.service_governance.sla_registry import sla_registry
        from core.service_governance.slo_tracker import slo_tracker
        from core.service_governance.availability_monitor import availability_monitor
        with self._lock:
            active_slas = sla_registry.active_slas()
            breached_slas = sla_registry.breached_slas()
            sla_total = len(active_slas) + len(breached_slas)
            sla_compliance_pct = (len(active_slas) / sla_total * 100) if sla_total else 100.0
            slo_compliance_pct = slo_tracker.compliance_rate_pct()
            degraded = availability_monitor.degraded_services()
            if sla_compliance_pct < 90 or slo_compliance_pct < 90 or len(degraded) > 2:
                health = "CRITICAL"
            elif sla_compliance_pct < 99 or slo_compliance_pct < 99 or degraded:
                health = "DEGRADED"
            else:
                health = "HEALTHY"
            return {
                "sla_compliance_pct": round(sla_compliance_pct, 2),
                "slo_compliance_pct": slo_compliance_pct,
                "degraded_services": degraded,
                "overall_health": health,
            }

    def one_liner(self) -> str:
        report = self.quality_report()
        return f"Service Governance: {report['overall_health']}, SLA {report['sla_compliance_pct']}%, SLO {report['slo_compliance_pct']}%"


service_quality_engine = ServiceQualityEngine()

"""
PHOENIX Meta Governance — Control Plane Monitor
Liveness and health monitoring for all PCCP control plane components.
"""
from __future__ import annotations
import threading
import time
from datetime import datetime, timezone


class ControlPlaneMonitor:
    def __init__(self):
        self._lock = threading.RLock()

    def monitor_pulse(self) -> dict:
        t0 = time.time()
        checked = 0
        failed = []

        components = {
            "pccp_orchestrator": lambda: __import__("core.pccp.pccp_orchestrator", fromlist=["pccp_orchestrator"]).pccp_orchestrator.system_status(),
            "conflict_resolver": lambda: __import__("core.pccp.conflict_resolver", fromlist=["conflict_resolver"]).conflict_resolver.conflict_stats(),
            "global_priority_manager": lambda: __import__("core.pccp.global_priority_manager", fromlist=["global_priority_manager"]).global_priority_manager.priority_summary(),
        }

        for name, fn in components.items():
            checked += 1
            try:
                fn()
            except Exception as e:
                failed.append({"component": name, "error": str(e)})

        elapsed_ms = round((time.time() - t0) * 1000, 2)
        return {
            "components_checked": checked,
            "all_responsive": len(failed) == 0,
            "failed_components": failed,
            "pulse_time_ms": elapsed_ms,
            "monitored_at": datetime.now(timezone.utc).isoformat(),
        }

    def continuous_health_report(self) -> dict:
        pulse = self.monitor_pulse()

        compliance_summary = {}
        try:
            from core.meta_governance.compliance_engine import compliance_engine
            report = compliance_engine.full_compliance_check()
            compliance_summary = {
                "score": report["compliance_score"],
                "non_compliant": report["non_compliant"],
            }
        except Exception:
            pass

        audit_summary = {}
        try:
            from core.meta_governance.pccp_audit_engine import pccp_audit_engine
            audit = pccp_audit_engine.full_pccp_audit()
            audit_summary = {
                "overall_compliance_score": audit["overall_compliance_score"],
                "findings_count": len(audit["findings_summary"]),
            }
        except Exception:
            pass

        return {
            "pulse": pulse,
            "compliance": compliance_summary,
            "audit_summary": audit_summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


control_plane_monitor = ControlPlaneMonitor()

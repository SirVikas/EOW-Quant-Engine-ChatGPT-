"""Governance Report Builder — assembles governance-focused reports."""
import threading
import time


class GovernanceReportBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build(self) -> dict:
        with self._lock:
            sections: dict = {}

            try:
                from core.constitution.constitution_engine import constitution_engine
                sections["constitution"] = constitution_engine.constitution_report()
            except Exception as e:
                sections["constitution"] = {"error": str(e)}

            try:
                from core.governance.compliance_engine import compliance_engine
                sections["compliance"] = compliance_engine.full_compliance_check()
            except Exception as e:
                sections["compliance"] = {"error": str(e)}

            try:
                from core.meta_governance.governance_validator import governance_validator
                sections["governance_health"] = governance_validator.governance_health()
            except Exception as e:
                sections["governance_health"] = {"error": str(e)}

            try:
                from core.evolution_governance.evolution_registry import evolution_registry
                sections["evolution_stats"] = evolution_registry.evolution_stats()
            except Exception as e:
                sections["evolution_stats"] = {"error": str(e)}

            return {
                "report_type": "GOVERNANCE",
                "generated_at": time.time(),
                "sections": sections,
            }


governance_report_builder = GovernanceReportBuilder()

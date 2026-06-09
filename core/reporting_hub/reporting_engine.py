"""Reporting Engine — unified routing and generation of all institutional reports."""
import threading
import time


class ReportingEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def generate_report(self, report_type: str) -> dict:
        with self._lock:
            report_type = report_type.upper()
            if report_type == "EXECUTIVE":
                from core.reporting_hub.executive_report_builder import executive_report_builder
                return executive_report_builder.build()
            elif report_type == "GOVERNANCE":
                from core.reporting_hub.governance_report_builder import governance_report_builder
                return governance_report_builder.build()
            elif report_type == "TRUST":
                from core.reporting_hub.trust_report_builder import trust_report_builder
                return trust_report_builder.build()
            elif report_type == "EVOLUTION":
                from core.reporting_hub.evolution_report_builder import evolution_report_builder
                return evolution_report_builder.build()
            elif report_type == "CAPITAL":
                from core.reporting_hub.capital_report_builder import capital_report_builder
                return capital_report_builder.build()
            else:
                return {"error": f"Unknown report type: {report_type}"}

    def generate_all_reports(self) -> dict:
        from core.reporting_hub.executive_report_builder import executive_report_builder
        from core.reporting_hub.governance_report_builder import governance_report_builder
        from core.reporting_hub.trust_report_builder import trust_report_builder
        from core.reporting_hub.evolution_report_builder import evolution_report_builder
        from core.reporting_hub.capital_report_builder import capital_report_builder

        reports = {
            "EXECUTIVE": executive_report_builder.build(),
            "GOVERNANCE": governance_report_builder.build(),
            "TRUST": trust_report_builder.build(),
            "EVOLUTION": evolution_report_builder.build(),
            "CAPITAL": capital_report_builder.build(),
        }
        total_sections = sum(len(r.get("sections", {})) for r in reports.values())
        return {
            "reports": reports,
            "generated_at": time.time(),
            "total_sections": total_sections,
        }

    def board_pack(self) -> dict:
        from core.reporting_hub.executive_report_builder import executive_report_builder
        from core.reporting_hub.governance_report_builder import governance_report_builder
        from core.reporting_hub.capital_report_builder import capital_report_builder

        return {
            "pack_type": "BOARD_PACK",
            "executive": executive_report_builder.build(),
            "governance": governance_report_builder.build(),
            "capital": capital_report_builder.build(),
            "generated_at": time.time(),
        }


reporting_engine = ReportingEngine()

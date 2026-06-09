"""Institutional Maturity Scorecard — Institutional Dashboard."""
import threading, time


class InstitutionalDashboard:
    def __init__(self):
        self._lock = threading.RLock()

    def full_dashboard(self) -> dict:
        with self._lock:
            from core.maturity_scorecard.maturity_engine import maturity_engine
            maturity = maturity_engine.assess()

            pcao_briefing = {}
            try:
                from core.pcao.pcao_engine import pcao_engine
                pcao_briefing = pcao_engine.executive_briefing()
            except Exception as e:
                pcao_briefing = {"error": str(e)[:60]}

            report_keys = []
            try:
                from core.reporting_hub.reporting_engine import reporting_engine
                all_reports = reporting_engine.generate_all_reports()
                report_keys = list(all_reports.get("reports", {}).keys())
            except Exception:
                pass

            governance_status = {}
            try:
                from core.human_governance.human_governance_engine import human_governance_engine
                governance_status = human_governance_engine.human_governance_status()
            except Exception as e:
                governance_status = {"error": str(e)[:60]}

            constitution_stats = {}
            try:
                from core.constitution.constitution_engine import constitution_engine
                report = constitution_engine.constitution_report()
                constitution_stats = {
                    "constitutional_health_score": report.get("constitutional_health_score"),
                    "articles_active": report.get("articles_active"),
                }
            except Exception as e:
                constitution_stats = {"error": str(e)[:60]}

        return {
            "maturity": maturity,
            "pcao_briefing": pcao_briefing,
            "available_reports": report_keys,
            "governance_status": governance_status,
            "constitution_stats": constitution_stats,
            "generated_at": time.time(),
        }

    def readiness_summary(self) -> dict:
        from core.maturity_scorecard.maturity_engine import maturity_engine
        assessment = maturity_engine.assess()
        score = assessment["total_score"]
        level = assessment["maturity_level"]
        return {
            "score": score,
            "level": level,
            "production_ready": score >= 88,
            "generated_at": time.time(),
        }


institutional_dashboard = InstitutionalDashboard()

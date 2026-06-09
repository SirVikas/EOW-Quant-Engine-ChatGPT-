"""Executive Performance Dashboard — master executive management engine."""
import threading


class ExecutivePerformanceDashboard:
    def __init__(self):
        self._lock = threading.RLock()

    def executive_report(self) -> dict:
        from core.executive_management.okr_registry import okr_registry
        from core.executive_management.goal_tracker import goal_tracker
        from core.executive_management.strategic_kpi_engine import strategic_kpi_engine
        with self._lock:
            active_okrs = okr_registry.active_okrs()
            # OKR completion: avg progress across all KRs
            total_pct = 0.0
            kr_count = 0
            for o in active_okrs:
                for kr in o["key_results"]:
                    if kr["target"] > 0:
                        total_pct += min(100.0, kr["current"] / kr["target"] * 100)
                        kr_count += 1
            okr_completion_pct = round(total_pct / kr_count, 2) if kr_count else 0.0
            goal_summary = goal_tracker.goal_summary()
            all_kpis = strategic_kpi_engine.kpi_dashboard()
            on_target_kpis = sum(1 for k in all_kpis if k["current_value"] >= k["target_value"])
            return {
                "okr_completion_pct": okr_completion_pct,
                "goals_on_track": goal_summary["on_track"],
                "kpis_on_target": on_target_kpis,
                "period_summary": "Q1-2026 / Q2-2026 / Annual-2026",
            }

    def one_liner(self) -> str:
        report = self.executive_report()
        return f"Executive Dashboard: OKR {report['okr_completion_pct']}%, {report['goals_on_track']} goals on track, {report['kpis_on_target']} KPIs on target"


executive_performance_dashboard = ExecutivePerformanceDashboard()

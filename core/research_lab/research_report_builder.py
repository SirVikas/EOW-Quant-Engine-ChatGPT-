"""Research report builder for institutional research lab."""
import threading
from datetime import datetime


class ResearchReportBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build_report(self) -> dict:
        from core.research_lab.experiment_registry import experiment_registry
        from core.research_lab.hypothesis_engine import hypothesis_engine
        from core.research_lab.research_tracker import research_tracker

        exp_stats = experiment_registry.experiment_stats()
        recent_completed = experiment_registry.all_experiments(status_filter="COMPLETED")[-5:]
        hyp_stats = hypothesis_engine.hypothesis_stats()
        confirmed_hyps = hypothesis_engine.all_hypotheses(status_filter="CONFIRMED")
        top_research = research_tracker.top_relevant(5)

        return {
            "report_type": "RESEARCH",
            "sections": {
                "experiments": {
                    "stats": exp_stats,
                    "recent_completed": recent_completed,
                },
                "hypotheses": {
                    "stats": hyp_stats,
                    "confirmed": confirmed_hyps,
                },
                "top_research": top_research,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    def research_summary(self) -> dict:
        from core.research_lab.experiment_registry import experiment_registry
        from core.research_lab.hypothesis_engine import hypothesis_engine
        from core.research_lab.research_tracker import research_tracker

        exp_stats = experiment_registry.experiment_stats()
        hyp_stats = hypothesis_engine.hypothesis_stats()
        r_stats = research_tracker.research_stats()
        return {
            "active_experiments": exp_stats.get("by_status", {}).get("ACTIVE", 0),
            "confirmed_hypotheses": hyp_stats.get("confirmed", 0),
            "research_items": r_stats.get("total", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }


research_report_builder = ResearchReportBuilder()

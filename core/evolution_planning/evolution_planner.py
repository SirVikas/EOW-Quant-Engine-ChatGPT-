"""Evolution Planner — analyses current state and recommends next evolution steps."""
import threading
from datetime import datetime, timezone


class EvolutionPlanner:
    def __init__(self):
        self._lock = threading.RLock()

    def plan_next_evolution(self) -> dict:
        with self._lock:
            from core.evolution_planning.capability_progress_tracker import capability_progress_tracker
            from core.evolution_planning.roadmap_registry import roadmap_registry

            lagging = capability_progress_tracker.lagging_capabilities()
            active_roadmaps = roadmap_registry.active_roadmaps()

            maturity_score = 50
            try:
                from core.maturity_scorecard.maturity_engine import maturity_engine
                maturity_score = maturity_engine.assess().get("overall_score", 50)
            except Exception:
                pass

            focus_areas = [cap["capability_name"] for cap in lagging[:5]]
            candidates = [r["title"] for r in active_roadmaps]

            return {
                "recommended_focus_areas": focus_areas,
                "next_evolution_candidates": candidates,
                "estimated_impact": "HIGH" if len(lagging) > 3 else "MEDIUM",
                "planning_horizon": "3Y",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def evolution_plan_report(self) -> dict:
        with self._lock:
            from core.evolution_planning.roadmap_registry import roadmap_registry
            from core.evolution_planning.capability_progress_tracker import capability_progress_tracker
            from core.evolution_planning.future_architecture_engine import future_architecture_engine

            return {
                "roadmaps": roadmap_registry.roadmap_stats(),
                "capability_progress": capability_progress_tracker.progress_summary(),
                "visions": future_architecture_engine.architecture_outlook(),
                "planning_summary": self.plan_next_evolution(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }


evolution_planner = EvolutionPlanner()

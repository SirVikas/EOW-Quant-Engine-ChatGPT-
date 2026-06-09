"""
PHOENIX PCAO — Executive Dashboard
Aggregates all PCAO/PCCP/NEXUS sources into a unified executive view.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone


class ExecutiveDashboard:
    def __init__(self):
        self._lock = threading.RLock()

    def full_dashboard(self) -> dict:
        from core.pcao.pcao_executive_engine import pcao_executive_engine
        from core.pcao.priority_director import priority_director
        from core.pcao.resource_allocator import resource_allocator

        briefing = pcao_executive_engine.executive_briefing()
        active_priorities = priority_director.active_priorities()
        current_allocations = resource_allocator.current_allocations()

        health_forecast = {}
        try:
            from core.pccp.health_intelligence_engine import health_intelligence_engine
            health_forecast = health_intelligence_engine.at_risk_layers()
        except Exception:
            pass

        goal_hierarchy = {}
        try:
            from core.pccp.strategic_goal_engine import strategic_goal_engine
            goal_hierarchy = strategic_goal_engine.goal_hierarchy_report()
        except Exception:
            pass

        learning_summary = {}
        try:
            from core.pccp.institutional_learning_engine import institutional_learning_engine
            learning_summary = institutional_learning_engine.learning_summary()
        except Exception:
            pass

        return {
            "executive_briefing": briefing,
            "active_priorities": active_priorities,
            "current_allocations": current_allocations,
            "health_forecast": health_forecast,
            "strategic_goal_hierarchy": goal_hierarchy,
            "learning_summary": learning_summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def quick_status(self) -> dict:
        from core.pcao.pcao_executive_engine import pcao_executive_engine
        from core.pcao.priority_director import priority_director

        briefing = pcao_executive_engine.executive_briefing()
        top_3 = priority_director.active_priorities()[:3]
        return {
            "health": briefing.get("health"),
            "posture": pcao_executive_engine.strategic_posture(),
            "top_3_priorities": top_3,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


executive_dashboard = ExecutiveDashboard()

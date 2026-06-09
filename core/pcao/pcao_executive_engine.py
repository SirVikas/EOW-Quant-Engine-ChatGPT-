"""
PHOENIX PCAO — Executive Engine  (FTD PHX-AEI-PROGRAM-001)
Provides executive briefing, strategic posture, and status aggregation.
Complements the existing PCAOEngine (foundation layer) with institutional-level views.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone


class PCAOExecutiveEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def executive_briefing(self) -> dict:
        health = {}
        try:
            from core.nexus.institutional_health_index import institutional_health_index
            health = institutional_health_index.health_report()
        except Exception:
            health = {"status": "UNAVAILABLE"}

        top_priority = {}
        priority_summary_data = {}
        try:
            from core.pccp.global_priority_manager import global_priority_manager
            top_priority = global_priority_manager.top_priority()
            priority_summary_data = global_priority_manager.priority_summary()
        except Exception:
            pass

        critical_layer = {}
        try:
            from core.pccp.layer_dependency_engine import layer_dependency_engine
            critical_layer = layer_dependency_engine.most_critical_layer()
        except Exception:
            pass

        memory_status = {}
        try:
            from core.strategic_memory.strategic_memory_engine import strategic_memory_engine
            memory_status = strategic_memory_engine.memory_status()
        except Exception:
            pass

        health_score = health.get("health_score", 100) if isinstance(health, dict) else 100
        open_risks = health.get("open_risks", 0) if isinstance(health, dict) else 0

        if health_score >= 80 and open_risks == 0:
            verdict = "SYSTEMS_NOMINAL"
        elif health_score >= 60 or open_risks <= 2:
            verdict = "ATTENTION_REQUIRED"
        else:
            verdict = "EXECUTIVE_ACTION_REQUIRED"

        return {
            "health": health,
            "top_priority": top_priority,
            "priority_summary": priority_summary_data,
            "critical_layer": critical_layer,
            "memory_status": memory_status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
        }

    def strategic_posture(self) -> str:
        try:
            from core.nexus.institutional_health_index import institutional_health_index
            report = institutional_health_index.health_report()
            score = report.get("health_score", 75) if isinstance(report, dict) else 75
            open_risks = report.get("open_risks", 0) if isinstance(report, dict) else 0
        except Exception:
            score = 75
            open_risks = 0

        if score >= 80 and open_risks == 0:
            return "OFFENSIVE"
        elif score < 50 or open_risks > 3:
            return "DEFENSIVE"
        return "NEUTRAL"

    def pcao_status(self) -> dict:
        return {
            "version": "1.0.0",
            "posture": self.strategic_posture(),
            "briefing_summary": self.executive_briefing(),
        }


pcao_executive_engine = PCAOExecutiveEngine()

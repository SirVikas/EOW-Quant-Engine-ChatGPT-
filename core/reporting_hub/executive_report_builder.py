"""Executive Report Builder — assembles executive-level reports."""
import threading
import time


class ExecutiveReportBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build(self) -> dict:
        with self._lock:
            sections: dict = {}

            try:
                from core.pcao.pcao_engine import pcao_engine
                sections["pcao_briefing"] = pcao_engine.executive_briefing()
            except Exception as e:
                sections["pcao_briefing"] = {"error": str(e)}

            try:
                from core.strategic_memory.strategic_goal_engine import strategic_goal_engine
                sections["strategic_goals"] = strategic_goal_engine.goal_hierarchy_report()
            except Exception as e:
                sections["strategic_goals"] = {"error": str(e)}

            try:
                from core.autonomous_improvement.improvement_engine import improvement_engine
                sections["improvement_status"] = improvement_engine.improvement_status()
            except Exception as e:
                sections["improvement_status"] = {"error": str(e)}

            return {
                "report_type": "EXECUTIVE",
                "generated_at": time.time(),
                "sections": sections,
            }


executive_report_builder = ExecutiveReportBuilder()

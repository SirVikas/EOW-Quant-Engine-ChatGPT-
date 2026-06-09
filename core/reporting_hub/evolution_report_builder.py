"""Evolution Report Builder — assembles evolution lifecycle reports."""
import threading
import time


class EvolutionReportBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build(self) -> dict:
        with self._lock:
            sections: dict = {}

            try:
                from core.evolution_governance.evolution_registry import evolution_registry
                sections["evolution_stats"] = evolution_registry.evolution_stats()
            except Exception as e:
                sections["evolution_stats"] = {"error": str(e)}

            try:
                from core.evolution_governance.evolution_rollback_engine import evolution_rollback_engine
                sections["rollback_stats"] = evolution_rollback_engine.rollback_stats()
            except Exception as e:
                sections["rollback_stats"] = {"error": str(e)}

            try:
                from core.evolution_governance.evolution_approval_engine import evolution_approval_engine
                sections["approval_stats"] = evolution_approval_engine.approval_stats()
            except Exception as e:
                sections["approval_stats"] = {"error": str(e)}

            return {
                "report_type": "EVOLUTION",
                "generated_at": time.time(),
                "sections": sections,
            }


evolution_report_builder = EvolutionReportBuilder()

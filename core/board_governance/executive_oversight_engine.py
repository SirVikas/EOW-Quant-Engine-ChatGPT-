"""Executive Oversight Engine — aggregates oversight data for executive review."""
import threading
import time


class ExecutiveOversightEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def oversight_report(self) -> dict:
        from core.board_governance.board_decision_registry import board_decision_registry

        report: dict = {
            "generated_at": time.time(),
            "board_pending": board_decision_registry.pending_review(),
            "board_stats": board_decision_registry.decision_stats(),
        }

        try:
            from core.pcao.pcao_engine import pcao_engine
            report["pcao_briefing"] = pcao_engine.executive_briefing()
        except Exception:
            report["pcao_briefing"] = {}

        try:
            from core.evolution_governance.evolution_governance import evolution_governance
            report["pending_evolution_proposals"] = evolution_governance.pending_proposals() \
                if hasattr(evolution_governance, "pending_proposals") else []
        except Exception:
            report["pending_evolution_proposals"] = []

        return report

    def escalation_required(self) -> bool:
        from core.board_governance.board_decision_registry import board_decision_registry
        now = time.time()
        pending = board_decision_registry.pending_review()
        for d in pending:
            if now - d.get("submitted_at", now) > 7 * 86400:
                return True

        try:
            from core.pcao.pcao_engine import pcao_engine
            briefing = pcao_engine.executive_briefing()
            posture = briefing.get("posture", "")
            if "CRITICAL" in str(posture).upper():
                return True
        except Exception:
            pass

        return False

    def oversight_health(self) -> dict:
        from core.board_governance.board_decision_registry import board_decision_registry
        pending = board_decision_registry.pending_review()
        escalation = self.escalation_required()
        pcao_posture = "UNKNOWN"
        try:
            from core.pcao.pcao_engine import pcao_engine
            briefing = pcao_engine.executive_briefing()
            pcao_posture = briefing.get("posture", "UNKNOWN")
        except Exception:
            pass
        health_score = 100 - (len(pending) * 5) - (20 if escalation else 0)
        return {
            "pcao_posture": pcao_posture,
            "pending_board_items": len(pending),
            "escalation_required": escalation,
            "health_score": max(0, health_score),
        }


executive_oversight_engine = ExecutiveOversightEngine()

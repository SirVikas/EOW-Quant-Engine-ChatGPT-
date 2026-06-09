"""Board Engine — unified facade for board governance."""
import threading
import time


class BoardEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def full_board_dashboard(self) -> dict:
        from core.board_governance.board_decision_registry import board_decision_registry
        from core.board_governance.board_review_engine import board_review_engine
        from core.board_governance.executive_oversight_engine import executive_oversight_engine

        decisions = board_decision_registry.all_decisions()
        consensus_summaries = []
        for d in decisions:
            did = d["decision_id"]
            consensus = board_review_engine.board_consensus(did)
            if consensus.get("consensus") != "NO_REVIEWS":
                consensus_summaries.append({"decision_id": did, **consensus})

        return {
            "decision_stats": board_decision_registry.decision_stats(),
            "consensus_summaries": consensus_summaries,
            "oversight_report": executive_oversight_engine.oversight_report(),
            "generated_at": time.time(),
        }

    def submit_for_board_review(self, title: str, decision_type: str,
                                 submitted_by: str, rationale: str) -> str:
        from core.board_governance.board_decision_registry import board_decision_registry
        return board_decision_registry.submit(title, decision_type, submitted_by, rationale)

    def board_status(self) -> dict:
        from core.board_governance.board_decision_registry import board_decision_registry
        stats = board_decision_registry.decision_stats()
        pending = board_decision_registry.pending_review()
        all_dec = board_decision_registry.all_decisions()
        last_at = max((d.get("decided_at", 0) for d in all_dec), default=0.0)
        return {
            "pending_count": len(pending),
            "approval_rate": stats.get("approval_rate", 0.0),
            "last_decision_at": last_at,
        }


board_engine = BoardEngine()

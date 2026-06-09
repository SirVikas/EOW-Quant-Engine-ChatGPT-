"""Human Governance Engine — unified facade for all human governance operations."""
import threading
import time


class HumanGovernanceEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def governance_dashboard(self) -> dict:
        from core.human_governance.approval_registry import approval_registry
        from core.human_governance.emergency_override_engine import emergency_override_engine
        from core.human_governance.rollback_authority import rollback_authority

        pending = approval_registry.pending_approvals()
        active_overrides = emergency_override_engine.active_overrides()
        rollback_orders = rollback_authority.all_orders()

        now = time.time()
        has_old_pending = any(
            now - p.get("requested_at", now) > 86400 for p in pending
        )
        health_score = 100
        if active_overrides:
            health_score -= len(active_overrides) * 15
        if has_old_pending:
            health_score -= 20
        health_score = max(0, health_score)

        return {
            "pending_approvals": pending,
            "active_overrides": active_overrides,
            "rollback_orders": rollback_orders,
            "governance_health_score": health_score,
            "generated_at": time.time(),
        }

    def pause(self, target: str, issued_by: str, reason: str) -> str:
        from core.human_governance.emergency_override_engine import emergency_override_engine
        return emergency_override_engine.issue_override("PAUSE", issued_by, target, reason)

    def emergency_stop(self, target: str, issued_by: str, reason: str) -> dict:
        from core.human_governance.emergency_override_engine import emergency_override_engine
        from core.human_governance.rollback_authority import rollback_authority

        override_id = emergency_override_engine.issue_override("STOP", issued_by, target, reason)
        order_id = rollback_authority.issue_rollback(issued_by, target, "SYSTEM",
                                                      reason, urgency="EMERGENCY")
        return {"override_id": override_id, "rollback_order_id": order_id}

    def approve_action(self, subject_id: str, subject_type: str,
                        action: str, requested_by: str) -> str:
        from core.human_governance.approval_registry import approval_registry
        return approval_registry.request_approval(subject_id, subject_type, action, requested_by)

    def human_governance_status(self) -> dict:
        from core.human_governance.approval_registry import approval_registry
        from core.human_governance.emergency_override_engine import emergency_override_engine
        from core.human_governance.rollback_authority import rollback_authority

        return {
            "approval_stats": approval_registry.approval_stats(),
            "override_stats": emergency_override_engine.override_stats(),
            "rollback_stats": rollback_authority.rollback_stats(),
            "generated_at": time.time(),
        }


human_governance_engine = HumanGovernanceEngine()

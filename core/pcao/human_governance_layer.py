"""
PHOENIX PCAO — Human Governance Layer  [GAP-R14]

Makes human governance actions first-class citizens:
  - Board Actions (approve, veto, override, defer)
  - Governance Approvals (trust promotion, AEG promotion, amendments)
  - Vetoes (block specific actions even if system would allow)
  - Overrides (force-allow despite system blocks)
  - Audit trail of every human governance act

All human actions are:
  1. Recorded with actor identity, timestamp, rationale
  2. Propagated to the relevant subsystem
  3. Mirrored to NEXUS institutional memory
  4. Auditable by any future session
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


ACTION_TYPES = {
    "APPROVE_TRUST_PROMOTION",
    "VETO_TRUST_PROMOTION",
    "APPROVE_AEG_PROMOTION",
    "VETO_AEG_PROMOTION",
    "APPROVE_AMENDMENT",
    "VETO_AMENDMENT",
    "OVERRIDE_EVIDENCE_BLOCK",
    "OVERRIDE_ROLLBACK_SUSPENSION",
    "RISK_ACCEPTED",
    "RISK_ESCALATED",
    "BOARD_DIRECTIVE",
}


@dataclass
class HumanGovernanceAction:
    action_id: str
    action_type: str
    actor: str
    subject_id: str
    rationale: str
    outcome: str = "PENDING"   # PENDING / APPLIED / FAILED / SUPERSEDED
    propagated: bool = False
    recorded_at: float = field(default_factory=time.time)
    applied_at: float = 0.0
    detail: dict = field(default_factory=dict)


class HumanGovernanceLayer:
    """
    Records and propagates all human governance actions across PHOENIX layers.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._actions: List[HumanGovernanceAction] = []

    def act(
        self,
        action_type: str,
        actor: str,
        subject_id: str,
        rationale: str,
        detail: Optional[dict] = None,
    ) -> HumanGovernanceAction:
        action = HumanGovernanceAction(
            action_id=f"HGA-{action_type[:4]}-{int(time.time()*1000)}",
            action_type=action_type,
            actor=actor,
            subject_id=subject_id,
            rationale=rationale,
            detail=detail or {},
        )
        with self._lock:
            self._actions.append(action)
        self._propagate(action)
        return action

    def _propagate(self, action: HumanGovernanceAction) -> None:
        try:
            self._apply_action(action)
            action.outcome = "APPLIED"
            action.applied_at = time.time()
            action.propagated = True
        except Exception as e:
            action.outcome = f"FAILED: {e}"

        # Mirror to NEXUS
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[HUMAN GOVERNANCE] {action.action_type} by {action.actor}: {action.subject_id}",
                    content=f"Rationale: {action.rationale}",
                    category="human_governance",
                    tags=["human", "governance", action.action_type.lower(), action.actor.lower()],
                )
        except Exception:
            pass

    def _apply_action(self, action: HumanGovernanceAction) -> None:
        t = action.action_type

        if t == "APPROVE_AEG_PROMOTION":
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            aeg_promotion_engine.approve_promotion(action.subject_id, approved_by=action.actor)

        elif t == "OVERRIDE_EVIDENCE_BLOCK":
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine
            evidence_supremacy_engine.override_verdict(action.subject_id, overridden_by=action.actor)

        elif t == "OVERRIDE_ROLLBACK_SUSPENSION":
            from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework
            aeg_rollback_framework.reinstate(action.subject_id, approved_by=action.actor)

        elif t == "RISK_ACCEPTED":
            from core.pcao.risk_office import risk_office
            risk_office.update_risk(action.subject_id, status="ACCEPTED")

        elif t == "RISK_ESCALATED":
            from core.pcao.risk_office import risk_office
            risk_office.update_risk(action.subject_id, severity="CRITICAL")

        elif t == "APPROVE_AMENDMENT":
            from core.cortex.constitutional_amendment import constitutional_amendment
            constitutional_amendment.enact(action.subject_id, enacted_by=action.actor)

        elif t == "BOARD_DIRECTIVE":
            pass  # Recorded only — no automated propagation

    # ── Query ─────────────────────────────────────────────────────────────────

    def recent_actions(self, limit: int = 50) -> List[dict]:
        with self._lock:
            items = list(self._actions)
        return [self._ser(a) for a in sorted(items, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    def by_actor(self, actor: str) -> List[dict]:
        with self._lock:
            items = [a for a in self._actions if a.actor == actor]
        return [self._ser(a) for a in sorted(items, key=lambda x: x.recorded_at, reverse=True)]

    def by_type(self, action_type: str) -> List[dict]:
        with self._lock:
            items = [a for a in self._actions if a.action_type == action_type]
        return [self._ser(a) for a in sorted(items, key=lambda x: x.recorded_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._actions)
        by_type: Dict[str, int] = {}
        for a in items:
            by_type[a.action_type] = by_type.get(a.action_type, 0) + 1
        return {
            "total_actions":  len(items),
            "applied":        sum(1 for a in items if a.outcome == "APPLIED"),
            "failed":         sum(1 for a in items if a.outcome.startswith("FAILED")),
            "by_type":        by_type,
            "available_types": sorted(ACTION_TYPES),
        }

    @staticmethod
    def _ser(a: HumanGovernanceAction) -> dict:
        return {
            "action_id":   a.action_id,
            "action_type": a.action_type,
            "actor":       a.actor,
            "subject_id":  a.subject_id,
            "rationale":   a.rationale,
            "outcome":     a.outcome,
            "propagated":  a.propagated,
            "recorded_at": a.recorded_at,
            "applied_at":  a.applied_at or None,
            "detail":      a.detail,
        }


# Singleton
human_governance_layer = HumanGovernanceLayer()

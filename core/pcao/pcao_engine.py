"""
PHOENIX PCAO — Planning, Control, Autonomy, and Oversight Foundation  [FTD-PCAO-001]

PCAO is the strategic governance layer above AEG.
It answers: "What should the system work on next? Who decides? Who audits?"

PCAO Components (Foundation — v0.1.0):
  1. Strategic Planning   — Objective registry, priority queue
  2. Task Routing         — Directs work to the appropriate subsystem
  3. Resource Allocation  — Tracks which subsystems are active
  4. Board Communications — Human-readable governance summaries
  5. Executive Oversight  — Unified audit and decision log

Current status: FOUNDATION LAYER (0% autonomous capability).
  AEG must complete and stabilize before PCAO autonomy is activated.
  All PCAO actions are advisory / human-reviewed at this stage.

Prerequisite chain: KGE → HKE → AEG → PCAO
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


PCAO_VERSION = "0.1.0"
PCAO_STATUS  = "FOUNDATION"   # FOUNDATION / ACTIVE / AUTONOMOUS


PRIORITY_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "DEFERRED"]


@dataclass
class StrategicObjective:
    obj_id: str
    title: str
    description: str
    priority: str
    owner: str           # "SYSTEM", "AEG", "HUMAN:<name>"
    status: str          # PROPOSED / ACTIVE / COMPLETED / DEFERRED / CANCELLED
    target_subsystem: str
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    outcome_summary: str = ""


@dataclass
class PCAODecision:
    decision_id: str
    obj_id: str
    decision_type: str   # ROUTE / PRIORITISE / ALLOCATE / DEFER / ESCALATE
    rationale: str
    decided_by: str      # "SYSTEM", "HUMAN:<name>", "AEG"
    requires_human_approval: bool
    approved: bool = False
    approved_by: str = ""
    recorded_at: float = field(default_factory=time.time)


class PCAOEngine:
    """
    PCAO Foundation: Strategic Planning and Oversight.
    All actions advisory at v0.1.0 — human approval required for all routing decisions.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._objectives: Dict[str, StrategicObjective] = {}
        self._decisions: List[PCAODecision] = []
        self._seed_founding_objectives()

    def _seed_founding_objectives(self) -> None:
        founding = [
            ("PCAO-OBJ-001", "Complete FTD-KGE-001 Knowledge Graph Expansion", "Expand entity coverage to 10+ node types", "HIGH", "KGE"),
            ("PCAO-OBJ-002", "Complete FTD-HKE-001 Historical Knowledge Extraction", "Extract 500+ institutional facts from archives", "HIGH", "HKE"),
            ("PCAO-OBJ-003", "Activate FTD-AEG-001 Autonomous Engineering Governance", "AEG operational after KGE+HKE complete", "MEDIUM", "AEG"),
            ("PCAO-OBJ-004", "Complete ETE Phase-2 Truth Calibration", "Collect 500+ trades for ETE score calibration", "HIGH", "TRUTH_ENGINE"),
            ("PCAO-OBJ-005", "PCAO Autonomy Activation", "Enable PCAO autonomous task routing after AEG stabilizes", "LOW", "PCAO"),
        ]
        for obj_id, title, desc, priority, subsystem in founding:
            obj = StrategicObjective(
                obj_id=obj_id,
                title=title,
                description=desc,
                priority=priority,
                owner="SYSTEM",
                status="ACTIVE" if priority in ("HIGH", "CRITICAL") else "PROPOSED",
                target_subsystem=subsystem,
                created_at=time.time(),
            )
            self._objectives[obj_id] = obj

    # ── Strategic Planning ────────────────────────────────────────────────────

    def add_objective(
        self,
        title: str,
        description: str,
        priority: str,
        owner: str = "SYSTEM",
        target_subsystem: str = "",
    ) -> StrategicObjective:
        obj_id = f"PCAO-OBJ-{int(time.time()*1000)}"
        obj = StrategicObjective(
            obj_id=obj_id,
            title=title,
            description=description,
            priority=priority,
            owner=owner,
            status="PROPOSED",
            target_subsystem=target_subsystem,
        )
        with self._lock:
            self._objectives[obj_id] = obj
        return obj

    def update_objective_status(self, obj_id: str, status: str, outcome: str = "") -> dict:
        with self._lock:
            obj = self._objectives.get(obj_id)
        if not obj:
            return {"error": f"Objective '{obj_id}' not found"}
        obj.status = status
        if status == "COMPLETED":
            obj.completed_at = time.time()
            obj.outcome_summary = outcome
        return {"updated": True, "obj_id": obj_id, "status": status}

    def priority_queue(self) -> List[dict]:
        with self._lock:
            items = [o for o in self._objectives.values() if o.status not in ("COMPLETED", "CANCELLED")]
        items.sort(key=lambda x: (PRIORITY_LEVELS.index(x.priority) if x.priority in PRIORITY_LEVELS else 99, x.created_at))
        return [self._ser_obj(o) for o in items]

    # ── Task Routing ──────────────────────────────────────────────────────────

    def route_task(self, obj_id: str, rationale: str, decided_by: str = "SYSTEM") -> PCAODecision:
        d = PCAODecision(
            decision_id=f"PCAO-DEC-{int(time.time()*1000)}",
            obj_id=obj_id,
            decision_type="ROUTE",
            rationale=rationale,
            decided_by=decided_by,
            requires_human_approval=True,  # all routing requires human approval at v0.1.0
        )
        with self._lock:
            self._decisions.append(d)
        return d

    def approve_decision(self, decision_id: str, approved_by: str) -> dict:
        with self._lock:
            d = next((x for x in self._decisions if x.decision_id == decision_id), None)
        if not d:
            return {"error": f"Decision '{decision_id}' not found"}
        d.approved = True
        d.approved_by = approved_by
        return {"approved": True, "decision_id": decision_id}

    # ── Board Communications ──────────────────────────────────────────────────

    def board_summary(self) -> dict:
        with self._lock:
            all_obj = list(self._objectives.values())
            all_dec = list(self._decisions)

        by_status: Dict[str, int] = {}
        for o in all_obj:
            by_status[o.status] = by_status.get(o.status, 0) + 1

        pending_approvals = [d for d in all_dec if d.requires_human_approval and not d.approved]

        return {
            "pcao_version":        PCAO_VERSION,
            "pcao_status":         PCAO_STATUS,
            "total_objectives":    len(all_obj),
            "by_status":           by_status,
            "priority_queue_top5": self.priority_queue()[:5],
            "pending_approvals":   len(pending_approvals),
            "total_decisions":     len(all_dec),
            "note":                "PCAO is in FOUNDATION mode — all actions advisory and human-reviewed",
        }

    # ── Resource Allocation ───────────────────────────────────────────────────

    def resource_allocation_status(self) -> dict:
        subsystems = ["KGE", "HKE", "AEG", "TRUTH_ENGINE", "PCAO", "OBSERVATORY_X", "CORTEX", "PTP"]
        allocation = {}
        for sub in subsystems:
            active_objs = [o for o in self._objectives.values() if o.target_subsystem == sub and o.status == "ACTIVE"]
            allocation[sub] = {"active_objectives": len(active_objs), "status": "ACTIVE" if active_objs else "IDLE"}
        return allocation

    # ── Executive Oversight ───────────────────────────────────────────────────

    def executive_audit(self, limit: int = 20) -> List[dict]:
        with self._lock:
            decisions = list(self._decisions)
        return [
            {
                "decision_id":             d.decision_id,
                "obj_id":                  d.obj_id,
                "decision_type":           d.decision_type,
                "rationale":               d.rationale,
                "decided_by":              d.decided_by,
                "requires_human_approval": d.requires_human_approval,
                "approved":                d.approved,
                "approved_by":             d.approved_by,
                "recorded_at":             d.recorded_at,
            }
            for d in sorted(decisions, key=lambda x: x.recorded_at, reverse=True)[:limit]
        ]

    @staticmethod
    def _ser_obj(o: StrategicObjective) -> dict:
        return {
            "obj_id":           o.obj_id,
            "title":            o.title,
            "description":      o.description,
            "priority":         o.priority,
            "owner":            o.owner,
            "status":           o.status,
            "target_subsystem": o.target_subsystem,
            "created_at":       o.created_at,
            "completed_at":     o.completed_at or None,
            "outcome_summary":  o.outcome_summary,
        }


# Singleton
pcao_engine = PCAOEngine()

"""Workflow Registry — registry of business workflows."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


WorkflowType = Literal["RESEARCH", "GOVERNANCE", "EVOLUTION", "VALIDATION"]
WorkflowStatus = Literal["DRAFT", "ACTIVE", "PAUSED", "COMPLETED", "FAILED"]


@dataclass
class WorkflowRecord:
    workflow_id: str
    name: str
    workflow_type: WorkflowType
    steps: List[str]
    status: WorkflowStatus
    created_at: datetime = field(default_factory=datetime.utcnow)


class WorkflowRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._workflows: List[WorkflowRecord] = []
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"WF-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("Research Hypothesis Workflow", "RESEARCH", ["Hypothesis", "Data Collection", "Analysis", "Report"]),
            ("Governance Policy Review", "GOVERNANCE", ["Draft Policy", "Review", "Approve", "Publish"]),
            ("Evolution Proposal Workflow", "EVOLUTION", ["Propose", "Assess", "Approve", "Implement"]),
            ("Model Validation Workflow", "VALIDATION", ["Backtest", "Shadow", "Stress", "Promote"]),
        ]
        for name, wtype, steps in seeds:
            self._workflows.append(WorkflowRecord(
                workflow_id=self._next_id(),
                name=name,
                workflow_type=wtype,
                steps=steps,
                status="ACTIVE",
            ))

    def register(self, name: str, workflow_type: WorkflowType, steps: List[str]) -> WorkflowRecord:
        with self._lock:
            rec = WorkflowRecord(self._next_id(), name, workflow_type, steps, "DRAFT")
            self._workflows.append(rec)
            return rec

    def active_workflows(self) -> List[dict]:
        with self._lock:
            return [vars(w) for w in self._workflows if w.status == "ACTIVE"]

    def workflow_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for w in self._workflows:
                summary[w.status] = summary.get(w.status, 0) + 1
            return {"total_workflows": len(self._workflows), "by_status": summary}

    def get(self, workflow_id: str):
        with self._lock:
            return next((w for w in self._workflows if w.workflow_id == workflow_id), None)


workflow_registry = WorkflowRegistry()

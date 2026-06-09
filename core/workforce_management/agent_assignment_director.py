"""Agent Assignment Director — assigns agents to tasks/workflows."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Assignment:
    assignment_id: str
    agent_id: str
    task_name: str
    workflow_id: Optional[str]
    assigned_at: datetime
    completed_at: Optional[datetime]
    outcome: str


class AgentAssignmentDirector:
    def __init__(self):
        self._lock = threading.RLock()
        self._assignments: dict[str, Assignment] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ASN-{self._counter:03d}"

    def assign(self, agent_id: str, task_name: str,
               workflow_id: Optional[str] = None) -> Assignment:
        with self._lock:
            a = Assignment(
                assignment_id=self._next_id(),
                agent_id=agent_id,
                task_name=task_name,
                workflow_id=workflow_id,
                assigned_at=datetime.utcnow(),
                completed_at=None,
                outcome="PENDING",
            )
            self._assignments[a.assignment_id] = a
            return a

    def complete(self, assignment_id: str, outcome: str) -> Optional[Assignment]:
        with self._lock:
            a = self._assignments.get(assignment_id)
            if a:
                a.completed_at = datetime.utcnow()
                a.outcome = outcome
            return a

    def active_assignments(self) -> list[dict]:
        with self._lock:
            return [
                {"assignment_id": a.assignment_id, "agent_id": a.agent_id,
                 "task_name": a.task_name, "workflow_id": a.workflow_id,
                 "assigned_at": a.assigned_at.isoformat()}
                for a in self._assignments.values() if a.outcome == "PENDING"
            ]

    def assignment_report(self) -> dict:
        with self._lock:
            outcomes: dict[str, int] = {}
            for a in self._assignments.values():
                outcomes[a.outcome] = outcomes.get(a.outcome, 0) + 1
            return {"total_assignments": len(self._assignments), "by_outcome": outcomes}


agent_assignment_director = AgentAssignmentDirector()

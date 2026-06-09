"""Workflow Monitor — monitors workflow execution runs."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional


RunStatus = Literal["RUNNING", "COMPLETED", "FAILED"]


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: RunStatus
    current_step: str


class WorkflowMonitor:
    def __init__(self):
        self._lock = threading.RLock()
        self._runs: List[WorkflowRun] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RUN-{self._counter:03d}"

    def start_run(self, workflow_id: str) -> WorkflowRun:
        with self._lock:
            run = WorkflowRun(
                run_id=self._next_id(),
                workflow_id=workflow_id,
                started_at=datetime.utcnow(),
                completed_at=None,
                status="RUNNING",
                current_step="INIT",
            )
            self._runs.append(run)
            return run

    def complete_run(self, run_id: str, status: RunStatus) -> bool:
        with self._lock:
            for r in self._runs:
                if r.run_id == run_id:
                    r.status = status
                    r.completed_at = datetime.utcnow()
                    return True
            return False

    def active_runs(self) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._runs if r.status == "RUNNING"]

    def run_history(self, workflow_id: str) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._runs if r.workflow_id == workflow_id]


workflow_monitor = WorkflowMonitor()

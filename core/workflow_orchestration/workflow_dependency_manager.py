"""Workflow Dependency Manager — tracks workflow dependencies."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class DependencyRecord:
    dep_id: str
    upstream_workflow_id: str
    downstream_workflow_id: str
    registered_at: datetime = field(default_factory=datetime.utcnow)


class WorkflowDependencyManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._deps: List[DependencyRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DEP-{self._counter:03d}"

    def add_dependency(self, upstream_id: str, downstream_id: str) -> DependencyRecord:
        with self._lock:
            rec = DependencyRecord(self._next_id(), upstream_id, downstream_id)
            self._deps.append(rec)
            return rec

    def dependencies_for(self, workflow_id: str) -> List[dict]:
        with self._lock:
            return [vars(d) for d in self._deps if d.downstream_workflow_id == workflow_id]

    def can_start(self, workflow_id: str) -> bool:
        """Returns True if all upstream workflows are COMPLETED."""
        from core.workflow_orchestration.workflow_registry import workflow_registry
        with self._lock:
            upstream_ids = [d.upstream_workflow_id for d in self._deps if d.downstream_workflow_id == workflow_id]
            for uid in upstream_ids:
                wf = workflow_registry.get(uid)
                if wf is None or wf.status != "COMPLETED":
                    return False
            return True


workflow_dependency_manager = WorkflowDependencyManager()

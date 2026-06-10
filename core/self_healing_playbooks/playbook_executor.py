"""
Playbook executor — records structured executions of recovery playbooks.
Advisory execution: steps are issued as operator/healing guidance, never as
direct interventions in the live trading loop.
"""
import threading
import time
from typing import Dict


class PlaybookExecutor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._executions: Dict[str, dict] = {}
        self._counter = 0

    def execute(self, failure_type: str, context: str = "") -> dict:
        from core.self_healing_playbooks.playbook_registry import playbook_registry
        playbook = playbook_registry.find_for(failure_type)
        with self._lock:
            self._counter += 1
            execution_id = f"SHX-{self._counter:03d}"
            if playbook is None:
                execution = {
                    "execution_id": execution_id,
                    "failure_type": str(failure_type).upper(),
                    "playbook_id": None,
                    "status": "NO_PLAYBOOK",
                    "steps": [],
                    "context": context,
                    "executed_at": time.time(),
                }
            else:
                execution = {
                    "execution_id": execution_id,
                    "failure_type": playbook.failure_type,
                    "playbook_id": playbook.playbook_id,
                    "status": "EXECUTED",
                    "steps": [
                        {"step": step, "state": "ADVISED"}
                        for step in playbook.steps
                    ],
                    "context": context,
                    "executed_at": time.time(),
                }
            self._executions[execution_id] = execution
            return execution

    def get(self, execution_id: str) -> dict:
        with self._lock:
            return dict(self._executions.get(execution_id, {}))

    def execution_summary(self) -> dict:
        with self._lock:
            executions = list(self._executions.values())
            return {
                "total": len(executions),
                "executed": sum(1 for e in executions if e["status"] == "EXECUTED"),
                "no_playbook": sum(1 for e in executions if e["status"] == "NO_PLAYBOOK"),
                "recent": executions[-10:],
            }


playbook_executor = PlaybookExecutor()

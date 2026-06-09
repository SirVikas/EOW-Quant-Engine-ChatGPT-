"""Agent coordinator for multi-agent task assignment."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    task_id: str
    description: str
    assigned_to: str
    priority: int
    status: str
    created_at: str
    completed_at: Optional[str]


class AgentCoordinator:
    def __init__(self):
        self._lock = threading.RLock()
        self._tasks: list = []
        self._counter = 0

    def assign_task(self, description: str, agent_type_preferred: Optional[str] = None,
                    priority: int = 5) -> dict:
        from core.agent_fabric.agent_registry import agent_registry
        with self._lock:
            agents = agent_registry.active_agents(agent_type=agent_type_preferred)
            if not agents:
                agents = agent_registry.active_agents()
            assigned_to = agents[0]["agent_id"] if agents else "UNASSIGNED"
            self._counter += 1
            t = Task(
                task_id=f"TSK-{self._counter:03d}",
                description=description,
                assigned_to=assigned_to,
                priority=priority,
                status="ASSIGNED" if assigned_to != "UNASSIGNED" else "QUEUED",
                created_at=datetime.utcnow().isoformat(),
                completed_at=None,
            )
            self._tasks.append(t)
            return asdict(t)

    def complete_task(self, task_id: str, result: Optional[str] = None) -> bool:
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    t.status = "COMPLETED"
                    t.completed_at = datetime.utcnow().isoformat()
                    return True
            return False

    def fail_task(self, task_id: str, reason: str) -> bool:
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    t.status = "FAILED"
                    t.completed_at = datetime.utcnow().isoformat()
                    return True
            return False

    def active_tasks(self) -> list:
        with self._lock:
            return [asdict(t) for t in self._tasks if t.status in ("QUEUED", "ASSIGNED")]

    def coordinator_status(self) -> dict:
        from core.agent_fabric.agent_registry import agent_registry
        with self._lock:
            total = len(self._tasks)
            active = sum(1 for t in self._tasks if t.status in ("QUEUED", "ASSIGNED"))
            completed = sum(1 for t in self._tasks if t.status == "COMPLETED")
            failed = sum(1 for t in self._tasks if t.status == "FAILED")
            stats = agent_registry.agent_stats()
            return {"total_tasks": total, "active": active, "completed": completed,
                    "failed": failed, "agent_count": stats.get("active", 0)}


agent_coordinator = AgentCoordinator()

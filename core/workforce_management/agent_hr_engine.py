"""Agent HR Engine — manages agent lifecycle (hire/promote/retire)."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

TIERS = ["TRAINEE", "JUNIOR", "SENIOR", "PRINCIPAL", "DISTINGUISHED"]
STATUSES = ["ACTIVE", "PROBATION", "SUSPENDED", "RETIRED"]


@dataclass
class Agent:
    agent_id: str
    name: str
    role: str
    department: str
    status: str
    hired_at: datetime
    performance_tier: str


class AgentHREngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._agents: dict[str, Agent] = {}
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"AGT-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("Alpha Sentinel", "Risk Monitor", "Risk"),
            ("Beta Analyst", "Data Analyst", "Analytics"),
            ("Gamma Executor", "Trade Executor", "Execution"),
            ("Delta Curator", "Knowledge Curator", "Intelligence"),
            ("Epsilon Governor", "Governance Lead", "Governance"),
        ]
        for name, role, dept in seeds:
            self._create_internal(name, role, dept)

    def _create_internal(self, name: str, role: str, department: str) -> Agent:
        agent = Agent(
            agent_id=self._next_id(),
            name=name,
            role=role,
            department=department,
            status="ACTIVE",
            hired_at=datetime.utcnow(),
            performance_tier="TRAINEE",
        )
        self._agents[agent.agent_id] = agent
        return agent

    def hire(self, name: str, role: str, department: str) -> Agent:
        with self._lock:
            return self._create_internal(name, role, department)

    def promote(self, agent_id: str) -> Optional[Agent]:
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return None
            idx = TIERS.index(agent.performance_tier)
            if idx < len(TIERS) - 1:
                agent.performance_tier = TIERS[idx + 1]
            return agent

    def suspend(self, agent_id: str) -> Optional[Agent]:
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.status = "SUSPENDED"
            return agent

    def retire(self, agent_id: str) -> Optional[Agent]:
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.status = "RETIRED"
            return agent

    def active_agents(self) -> list[dict]:
        with self._lock:
            return [
                {"agent_id": a.agent_id, "name": a.name, "role": a.role,
                 "department": a.department, "performance_tier": a.performance_tier}
                for a in self._agents.values() if a.status == "ACTIVE"
            ]

    def workforce_summary(self) -> dict:
        with self._lock:
            by_status: dict[str, int] = {}
            by_tier: dict[str, int] = {}
            for a in self._agents.values():
                by_status[a.status] = by_status.get(a.status, 0) + 1
                by_tier[a.performance_tier] = by_tier.get(a.performance_tier, 0) + 1
            return {"total_agents": len(self._agents), "by_status": by_status, "by_tier": by_tier}


agent_hr_engine = AgentHREngine()

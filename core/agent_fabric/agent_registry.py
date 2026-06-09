"""Agent registry for multi-agent coordination fabric."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Agent:
    agent_id: str
    name: str
    agent_type: str
    capabilities: list
    status: str
    created_at: str
    last_active: str


class AgentRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._agents: list = []
        self._counter = 0
        # Auto-register 5 default agents
        defaults = [
            ("ANALYST_ALPHA", "ANALYST", ["market_analysis", "signal_evaluation", "trend_detection"]),
            ("RISK_SENTINEL", "RISK", ["risk_assessment", "drawdown_monitoring", "position_limits"]),
            ("AUDIT_INSPECTOR", "AUDIT", ["compliance_audit", "trade_review", "governance_check"]),
            ("RESEARCH_ASSISTANT", "RESEARCH", ["hypothesis_testing", "data_analysis", "insight_generation"]),
            ("GOVERNANCE_GUARDIAN", "GOVERNANCE", ["policy_enforcement", "escalation_handling", "oversight"]),
        ]
        for name, atype, caps in defaults:
            self._register(name, atype, caps)

    def _register(self, name: str, agent_type: str, capabilities: list) -> str:
        self._counter += 1
        agent_id = f"AGT-{self._counter:03d}"
        now = datetime.utcnow().isoformat()
        a = Agent(agent_id=agent_id, name=name, agent_type=agent_type,
                  capabilities=capabilities, status="ACTIVE",
                  created_at=now, last_active=now)
        self._agents.append(a)
        return agent_id

    def register(self, name: str, agent_type: str, capabilities: list) -> str:
        with self._lock:
            return self._register(name, agent_type, capabilities)

    def _set_status(self, agent_id: str, status: str) -> bool:
        for a in self._agents:
            if a.agent_id == agent_id:
                a.status = status
                return True
        return False

    def activate(self, agent_id: str) -> bool:
        with self._lock:
            return self._set_status(agent_id, "ACTIVE")

    def suspend(self, agent_id: str) -> bool:
        with self._lock:
            return self._set_status(agent_id, "SUSPENDED")

    def decommission(self, agent_id: str) -> bool:
        with self._lock:
            return self._set_status(agent_id, "DECOMMISSIONED")

    def active_agents(self, agent_type: Optional[str] = None) -> list:
        with self._lock:
            result = [a for a in self._agents if a.status == "ACTIVE"]
            if agent_type:
                result = [a for a in result if a.agent_type == agent_type]
            return [asdict(a) for a in result]

    def all_agents(self) -> list:
        with self._lock:
            return [asdict(a) for a in self._agents]

    def agent_stats(self) -> dict:
        with self._lock:
            total = len(self._agents)
            active = sum(1 for a in self._agents if a.status == "ACTIVE")
            by_type: dict = {}
            for a in self._agents:
                by_type[a.agent_type] = by_type.get(a.agent_type, 0) + 1
            return {"total": total, "active": active, "by_type": by_type}


agent_registry = AgentRegistry()

"""Agent Retirement Manager — handles agent retirement."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RetirementRecord:
    ret_id: str
    agent_id: str
    reason: str
    contributions_summary: str
    retired_at: datetime


class AgentRetirementManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, RetirementRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RET-{self._counter:03d}"

    def retire(self, agent_id: str, reason: str, contributions_summary: str) -> RetirementRecord:
        from core.workforce_management.agent_hr_engine import agent_hr_engine
        agent_hr_engine.retire(agent_id)
        with self._lock:
            rec = RetirementRecord(
                ret_id=self._next_id(),
                agent_id=agent_id,
                reason=reason,
                contributions_summary=contributions_summary,
                retired_at=datetime.utcnow(),
            )
            self._records[rec.ret_id] = rec
            return rec

    def retired_agents(self) -> list[dict]:
        with self._lock:
            return [
                {"ret_id": r.ret_id, "agent_id": r.agent_id, "reason": r.reason,
                 "contributions_summary": r.contributions_summary,
                 "retired_at": r.retired_at.isoformat()}
                for r in self._records.values()
            ]

    def retirement_stats(self) -> dict:
        with self._lock:
            return {
                "total_retirements": len(self._records),
                "reasons": list({r.reason for r in self._records.values()}),
            }


agent_retirement_manager = AgentRetirementManager()

"""Agent conflict resolver for multi-agent coordination."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class AgentConflict:
    conflict_id: str
    agent_a: str
    position_a: str
    agent_b: str
    position_b: str
    topic: str
    resolution: str
    resolved_by: str
    resolved_at: str


class AgentConflictResolver:
    def __init__(self):
        self._lock = threading.RLock()
        self._conflicts: list = []
        self._counter = 0

    def resolve(self, agent_a: str, position_a: str, agent_b: str, position_b: str, topic: str) -> dict:
        # Try strategic goal evaluation; fall back to simple heuristic
        winner_position = position_a
        resolved_by = agent_a
        try:
            from core.strategic_memory.strategic_goal_engine import strategic_goal_engine
            score_a = strategic_goal_engine.evaluate_alignment(position_a) if hasattr(strategic_goal_engine, "evaluate_alignment") else 0.5
            score_b = strategic_goal_engine.evaluate_alignment(position_b) if hasattr(strategic_goal_engine, "evaluate_alignment") else 0.5
            if score_b > score_a:
                winner_position = position_b
                resolved_by = agent_b
        except Exception:
            # Default: alphabetical winner (deterministic)
            if position_b < position_a:
                winner_position = position_b
                resolved_by = agent_b

        with self._lock:
            self._counter += 1
            c = AgentConflict(
                conflict_id=f"ACF-{self._counter:03d}",
                agent_a=agent_a, position_a=position_a,
                agent_b=agent_b, position_b=position_b,
                topic=topic, resolution=winner_position,
                resolved_by=resolved_by,
                resolved_at=datetime.utcnow().isoformat(),
            )
            self._conflicts.append(c)
            return asdict(c)

    def all_conflicts(self, limit: int = 20) -> list:
        with self._lock:
            return [asdict(c) for c in self._conflicts[-limit:]]

    def conflict_stats(self) -> dict:
        with self._lock:
            total = len(self._conflicts)
            escalated = sum(1 for c in self._conflicts if c.resolved_by == "ESCALATED")
            return {"total": total, "by_resolution_method": {}, "escalated_count": escalated}


agent_conflict_resolver = AgentConflictResolver()

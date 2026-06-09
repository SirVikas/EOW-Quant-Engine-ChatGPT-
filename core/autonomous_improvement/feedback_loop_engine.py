"""
PHOENIX Autonomous Improvement — Feedback Loop Engine
Manages full feedback cycles from trigger to lesson to proposals.
"""
from __future__ import annotations
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class FeedbackCycle:
    cycle_id: str
    trigger_event: str
    outcome_observed: str
    lesson_extracted: Optional[str]
    policy_proposed: Optional[str]
    behavior_proposed: Optional[str]
    cycle_complete: bool
    started_at: str
    completed_at: Optional[str]


class FeedbackLoopEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._cycles: Dict[str, FeedbackCycle] = {}

    def start_cycle(self, trigger_event: str, outcome_observed: str) -> dict:
        cycle_id = f"FC-{uuid.uuid4().hex[:8].upper()}"
        cycle = FeedbackCycle(
            cycle_id=cycle_id,
            trigger_event=trigger_event,
            outcome_observed=outcome_observed,
            lesson_extracted=None,
            policy_proposed=None,
            behavior_proposed=None,
            cycle_complete=False,
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=None,
        )
        with self._lock:
            self._cycles[cycle_id] = cycle
        return asdict(cycle)

    def add_lesson(self, cycle_id: str, lesson: str) -> dict:
        with self._lock:
            c = self._cycles.get(cycle_id)
            if c:
                c.lesson_extracted = lesson
                return asdict(c)
        return {"error": f"{cycle_id} not found"}

    def add_proposals(
        self, cycle_id: str, policy_proposal: str = None, behavior_proposal: str = None
    ) -> dict:
        with self._lock:
            c = self._cycles.get(cycle_id)
            if c:
                if policy_proposal:
                    c.policy_proposed = policy_proposal
                if behavior_proposal:
                    c.behavior_proposed = behavior_proposal
                return asdict(c)
        return {"error": f"{cycle_id} not found"}

    def complete_cycle(self, cycle_id: str) -> dict:
        with self._lock:
            c = self._cycles.get(cycle_id)
            if not c:
                return {"error": f"{cycle_id} not found"}
            c.cycle_complete = True
            c.completed_at = datetime.now(timezone.utc).isoformat()
            result = asdict(c)

        if c.lesson_extracted:
            try:
                from core.strategic_memory.lesson_registry import lesson_registry
                lesson_registry.record(c.lesson_extracted, source="FEEDBACK_LOOP")
            except Exception:
                pass
        return result

    def all_cycles(self, limit: int = 20) -> list:
        with self._lock:
            items = list(self._cycles.values())
        items.sort(key=lambda x: x.started_at, reverse=True)
        return [asdict(c) for c in items[:limit]]

    def loop_health(self) -> dict:
        with self._lock:
            items = list(self._cycles.values())
        total = len(items)
        complete = sum(1 for c in items if c.cycle_complete)
        lessons = sum(1 for c in items if c.lesson_extracted is not None)

        durations = []
        for c in items:
            if c.cycle_complete and c.completed_at:
                try:
                    from datetime import datetime as dt_cls
                    start = dt_cls.fromisoformat(c.started_at)
                    end = dt_cls.fromisoformat(c.completed_at)
                    durations.append((end - start).total_seconds())
                except Exception:
                    pass
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_cycles": total,
            "complete_cycles": complete,
            "avg_cycle_duration_s": round(avg_duration, 2),
            "lessons_generated": lessons,
        }


feedback_loop_engine = FeedbackLoopEngine()

"""Goal Tracker — tracks goal achievement linked to OKRs."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class GoalRecord:
    goal_id: str
    okr_id: str
    goal_text: str
    completion_pct: float
    on_track: bool
    updated_at: datetime = field(default_factory=datetime.utcnow)


class GoalTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._goals: List[GoalRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"GL-{self._counter:03d}"

    def update_goal(self, okr_id: str, goal_text: str, completion_pct: float) -> GoalRecord:
        with self._lock:
            # Upsert: update if exists, else create
            for g in self._goals:
                if g.okr_id == okr_id and g.goal_text == goal_text:
                    g.completion_pct = completion_pct
                    g.on_track = completion_pct >= 50
                    g.updated_at = datetime.utcnow()
                    return g
            rec = GoalRecord(self._next_id(), okr_id, goal_text, completion_pct, completion_pct >= 50)
            self._goals.append(rec)
            return rec

    def at_risk_goals(self) -> List[dict]:
        with self._lock:
            return [vars(g) for g in self._goals if not g.on_track]

    def goal_summary(self) -> dict:
        with self._lock:
            total = len(self._goals)
            on_track = sum(1 for g in self._goals if g.on_track)
            return {"total_goals": total, "on_track": on_track, "at_risk": total - on_track}


goal_tracker = GoalTracker()

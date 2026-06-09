"""Strategy Execution Monitor — monitors execution of strategy."""
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Milestone:
    exec_id: str
    initiative_id: str
    milestone: str
    achieved: bool
    target_date: datetime
    actual_date: Optional[datetime]
    notes: str


class StrategyExecutionMonitor:
    def __init__(self):
        self._lock = threading.RLock()
        self._milestones: dict[str, Milestone] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SEX-{self._counter:03d}"

    def record_milestone(self, initiative_id: str, milestone: str,
                         target_date_days: int) -> Milestone:
        with self._lock:
            m = Milestone(
                exec_id=self._next_id(),
                initiative_id=initiative_id,
                milestone=milestone,
                achieved=False,
                target_date=datetime.utcnow() + timedelta(days=target_date_days),
                actual_date=None,
                notes="",
            )
            self._milestones[m.exec_id] = m
            return m

    def mark_achieved(self, exec_id: str, notes: str = "") -> Optional[Milestone]:
        with self._lock:
            m = self._milestones.get(exec_id)
            if m:
                m.achieved = True
                m.actual_date = datetime.utcnow()
                m.notes = notes
            return m

    def at_risk_milestones(self) -> list[dict]:
        now = datetime.utcnow()
        with self._lock:
            return [
                {"exec_id": m.exec_id, "initiative_id": m.initiative_id,
                 "milestone": m.milestone,
                 "target_date": m.target_date.isoformat(),
                 "days_overdue": (now - m.target_date).days}
                for m in self._milestones.values()
                if not m.achieved and m.target_date < now
            ]


strategy_execution_monitor = StrategyExecutionMonitor()

"""Experiment registry for the institutional research lab."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Experiment:
    exp_id: str
    title: str
    hypothesis: str
    methodology: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    researcher: str
    expected_outcome: str
    actual_outcome: str
    conclusion: str


class ExperimentRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._experiments: list = []
        self._counter = 0

    def register(self, title: str, hypothesis: str, methodology: str, researcher: str,
                 expected_outcome: str) -> str:
        with self._lock:
            self._counter += 1
            exp_id = f"EXP-{self._counter:03d}"
            e = Experiment(
                exp_id=exp_id, title=title, hypothesis=hypothesis, methodology=methodology,
                status="PROPOSED", started_at=None, completed_at=None,
                researcher=researcher, expected_outcome=expected_outcome,
                actual_outcome="", conclusion="",
            )
            self._experiments.append(e)
            return exp_id

    def start(self, exp_id: str) -> bool:
        with self._lock:
            for e in self._experiments:
                if e.exp_id == exp_id:
                    e.status = "ACTIVE"
                    e.started_at = datetime.utcnow().isoformat()
                    return True
            return False

    def complete(self, exp_id: str, actual_outcome: str, conclusion: str) -> bool:
        with self._lock:
            for e in self._experiments:
                if e.exp_id == exp_id:
                    e.status = "COMPLETED"
                    e.completed_at = datetime.utcnow().isoformat()
                    e.actual_outcome = actual_outcome
                    e.conclusion = conclusion
                    return True
            return False

    def abandon(self, exp_id: str, reason: str) -> bool:
        with self._lock:
            for e in self._experiments:
                if e.exp_id == exp_id:
                    e.status = "ABANDONED"
                    e.conclusion = reason
                    return True
            return False

    def all_experiments(self, status_filter: Optional[str] = None) -> list:
        with self._lock:
            if status_filter:
                return [asdict(e) for e in self._experiments if e.status == status_filter]
            return [asdict(e) for e in self._experiments]

    def experiment_stats(self) -> dict:
        with self._lock:
            total = len(self._experiments)
            by_status: dict = {}
            for e in self._experiments:
                by_status[e.status] = by_status.get(e.status, 0) + 1
            completed = by_status.get("COMPLETED", 0)
            rate = completed / max(1, total)
            durations = []
            for e in self._experiments:
                if e.started_at and e.completed_at:
                    from datetime import datetime as dt
                    try:
                        s = dt.fromisoformat(e.started_at)
                        c = dt.fromisoformat(e.completed_at)
                        durations.append((c - s).total_seconds() / 3600)
                    except Exception:
                        pass
            avg_dur = sum(durations) / len(durations) if durations else 0
            return {"total": total, "by_status": by_status, "completion_rate": rate,
                    "avg_duration_days": avg_dur / 24}


experiment_registry = ExperimentRegistry()

"""Agent Performance Tracker — tracks agent performance metrics."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceRecord:
    perf_id: str
    agent_id: str
    period: str
    tasks_completed: int
    accuracy_pct: float
    reliability_score: int
    recorded_at: datetime


class AgentPerformanceTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, PerformanceRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"PFM-{self._counter:03d}"

    def record(self, agent_id: str, period: str, tasks_completed: int,
               accuracy_pct: float, reliability_score: int) -> PerformanceRecord:
        with self._lock:
            rec = PerformanceRecord(
                perf_id=self._next_id(),
                agent_id=agent_id,
                period=period,
                tasks_completed=tasks_completed,
                accuracy_pct=accuracy_pct,
                reliability_score=max(0, min(100, reliability_score)),
                recorded_at=datetime.utcnow(),
            )
            self._records[rec.perf_id] = rec
            return rec

    def performance_for(self, agent_id: str) -> list[dict]:
        with self._lock:
            return [
                {"perf_id": r.perf_id, "period": r.period,
                 "tasks_completed": r.tasks_completed,
                 "accuracy_pct": r.accuracy_pct,
                 "reliability_score": r.reliability_score,
                 "recorded_at": r.recorded_at.isoformat()}
                for r in self._records.values() if r.agent_id == agent_id
            ]

    def top_performers(self, n: int = 5) -> list[dict]:
        with self._lock:
            # average reliability per agent
            scores: dict[str, list[int]] = {}
            for r in self._records.values():
                scores.setdefault(r.agent_id, []).append(r.reliability_score)
            avg = {aid: sum(s) / len(s) for aid, s in scores.items()}
            top = sorted(avg.items(), key=lambda x: x[1], reverse=True)[:n]
            return [{"agent_id": aid, "avg_reliability": round(score, 1)} for aid, score in top]


agent_performance_tracker = AgentPerformanceTracker()

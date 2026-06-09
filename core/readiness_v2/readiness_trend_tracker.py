"""
Readiness trend tracker — records readiness scores per dimension over time.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class ReadinessTrend:
    trend_id: str
    dimension: str   # ARCHITECTURE / GOVERNANCE / VALIDATION / OPERATIONS / ECONOMIC
    score: float     # 0–100
    period: str
    recorded_at: str


class ReadinessTrendTracker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[ReadinessTrend] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RDT-{self._counter:03d}"

    def record(self, dimension: str, score: float, period: str) -> ReadinessTrend:
        with self._lock:
            rec = ReadinessTrend(
                trend_id=self._next_id(),
                dimension=dimension,
                score=max(0.0, min(100.0, score)),
                period=period,
                recorded_at=datetime.utcnow().isoformat(),
            )
            self._records.append(rec)
            return rec

    def trend_for(self, dimension: str) -> List[ReadinessTrend]:
        with self._lock:
            return [r for r in self._records if r.dimension == dimension]

    def latest_scores(self) -> Dict[str, float]:
        with self._lock:
            latest: Dict[str, ReadinessTrend] = {}
            for r in self._records:
                if r.dimension not in latest or r.recorded_at > latest[r.dimension].recorded_at:
                    latest[r.dimension] = r
            return {dim: rec.score for dim, rec in latest.items()}


readiness_trend_tracker = ReadinessTrendTracker()

"""Competitive Intelligence Engine — tracks competitive landscape observations."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List


@dataclass
class CompetitiveObservation:
    obs_id: str
    competitor_name: str
    observation: str
    strategic_implication: str
    timestamp: str


class CompetitiveIntelligenceEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._observations: List[CompetitiveObservation] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"OBS-{self._counter:03d}"

    def record_observation(self, competitor_name: str, observation: str,
                           strategic_implication: str) -> dict:
        with self._lock:
            obs = CompetitiveObservation(
                obs_id=self._next_id(),
                competitor_name=competitor_name,
                observation=observation,
                strategic_implication=strategic_implication,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._observations.append(obs)
            return asdict(obs)

    def all_observations(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(o) for o in self._observations[-limit:]]

    def by_competitor(self, name: str) -> List[dict]:
        with self._lock:
            return [asdict(o) for o in self._observations if o.competitor_name == name]

    def observation_stats(self) -> dict:
        with self._lock:
            total = len(self._observations)
            competitors = set(o.competitor_name for o in self._observations)
            return {"total_observations": total, "unique_competitors": len(competitors)}


competitive_intelligence_engine = CompetitiveIntelligenceEngine()

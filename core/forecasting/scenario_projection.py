"""Scenario projection engine for strategic forecasting."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Projection:
    proj_id: str
    scenario_name: str
    horizon_days: int
    base_case: dict
    bull_case: dict
    bear_case: dict
    probability_weights: dict
    expected_value: dict
    created_at: str


def _weighted_avg(base: dict, bull: dict, bear: dict, weights: dict) -> dict:
    result = {}
    all_keys = set(base.keys()) | set(bull.keys()) | set(bear.keys())
    for k in all_keys:
        bv = base.get(k, 0)
        uv = bull.get(k, bv)
        dv = bear.get(k, bv)
        if all(isinstance(x, (int, float)) for x in [bv, uv, dv]):
            result[k] = (bv * weights.get("base", 0.6) +
                         uv * weights.get("bull", 0.2) +
                         dv * weights.get("bear", 0.2))
    return result


class ScenarioProjection:
    def __init__(self):
        self._lock = threading.RLock()
        self._projections: list = []
        self._counter = 0

    def project(self, scenario_name: str, horizon_days: int, base_case: dict,
                bull_case: Optional[dict] = None, bear_case: Optional[dict] = None,
                prob_weights: Optional[dict] = None) -> dict:
        with self._lock:
            self._counter += 1
            weights = prob_weights or {"base": 0.6, "bull": 0.2, "bear": 0.2}
            bull = bull_case or base_case
            bear = bear_case or base_case
            ev = _weighted_avg(base_case, bull, bear, weights)
            p = Projection(
                proj_id=f"PRJ-{self._counter:03d}",
                scenario_name=scenario_name, horizon_days=horizon_days,
                base_case=base_case, bull_case=bull, bear_case=bear,
                probability_weights=weights, expected_value=ev,
                created_at=datetime.utcnow().isoformat(),
            )
            self._projections.append(p)
            return asdict(p)

    def all_projections(self, limit: int = 20) -> list:
        with self._lock:
            return [asdict(p) for p in self._projections[-limit:]]

    def scenario_comparison(self) -> list:
        with self._lock:
            return sorted([asdict(p) for p in self._projections], key=lambda x: x["horizon_days"])[-10:]


scenario_projection = ScenarioProjection()

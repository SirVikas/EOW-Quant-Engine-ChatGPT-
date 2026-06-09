"""
PHOENIX Digital Twin — Scenario Simulator
Deterministic scenario simulation for pre-deployment risk assessment.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class Scenario:
    scenario_id: str
    name: str
    parameters: Dict
    sim_result: Dict
    risk_score: float
    drawdown_projection: float
    capital_impact_pct: float
    stability_score: float
    created_at: str


class ScenarioSimulator:
    def __init__(self):
        self._lock = threading.RLock()
        self._scenarios: Dict[str, Scenario] = {}

    def simulate(self, name: str, parameters: dict) -> dict:
        risk_score = min(
            1.0,
            parameters.get("position_size_mult", 1.0) * 0.3
            + parameters.get("leverage", 1.0) * 0.1,
        )
        drawdown_projection = parameters.get("base_drawdown", 0.05) * (
            1 + parameters.get("volatility_factor", 0.0)
        )
        capital_impact_pct = (
            -drawdown_projection * 100 * parameters.get("position_size_mult", 1.0)
        )
        stability_score = max(0.0, 1.0 - risk_score)

        scenario_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        sim_result = {
            "risk_score": risk_score,
            "drawdown_projection": drawdown_projection,
            "capital_impact_pct": capital_impact_pct,
            "stability_score": stability_score,
        }
        scenario = Scenario(
            scenario_id=scenario_id,
            name=name,
            parameters=parameters,
            sim_result=sim_result,
            risk_score=risk_score,
            drawdown_projection=drawdown_projection,
            capital_impact_pct=capital_impact_pct,
            stability_score=stability_score,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._scenarios[scenario_id] = scenario
        return asdict(scenario)

    def compare_scenarios(self, scenario_ids: List[str]) -> dict:
        with self._lock:
            comparison = {}
            for sid in scenario_ids:
                s = self._scenarios.get(sid)
                comparison[sid] = asdict(s) if s else None
        return {"comparison": comparison, "scenario_count": len(scenario_ids)}

    def all_scenarios(self, limit: int = 50) -> list:
        with self._lock:
            items = list(self._scenarios.values())
        items.sort(key=lambda x: x.created_at, reverse=True)
        return [asdict(s) for s in items[:limit]]


scenario_simulator = ScenarioSimulator()

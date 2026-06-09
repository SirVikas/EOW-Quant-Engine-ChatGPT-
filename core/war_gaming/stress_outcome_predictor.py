"""Stress Outcome Predictor — predicts system outcomes under stress scenarios."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class StressScenario:
    scenario_id: str
    name: str
    severity: float  # 0-1
    predicted_impact: Dict
    recommended_response: str
    created_at: str


_SEED_SCENARIOS = [
    {
        "name": "BLACK_SWAN_CRASH",
        "severity": 0.9,
        "predicted_impact": {
            "portfolio_drawdown_pct": 45,
            "liquidity_impact": "SEVERE",
            "recovery_horizon_days": 180,
        },
        "recommended_response": "Halt all live trading; activate capital preservation mode; escalate to governance layer.",
    },
    {
        "name": "GOVERNANCE_FAILURE",
        "severity": 0.7,
        "predicted_impact": {
            "compliance_risk": "HIGH",
            "operational_continuity": "DEGRADED",
            "audit_exposure": "ELEVATED",
        },
        "recommended_response": "Engage EGI override protocols; freeze discretionary actions; trigger IMRAF incident log.",
    },
    {
        "name": "TRUST_COLLAPSE",
        "severity": 0.8,
        "predicted_impact": {
            "signal_reliability_pct": 20,
            "false_positive_rate": "HIGH",
            "decision_confidence_drop_pct": 60,
        },
        "recommended_response": "Switch to conservative rule-based execution; disable RL inference; initiate truth engine recalibration.",
    },
]


class StressOutcomePredictor:
    def __init__(self):
        self._lock = threading.RLock()
        self._scenarios: Dict[str, StressScenario] = {}
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"SCN-{self._counter:03d}"

    def _seed(self):
        for s in _SEED_SCENARIOS:
            scenario = StressScenario(
                scenario_id=self._next_id(),
                name=s["name"],
                severity=s["severity"],
                predicted_impact=s["predicted_impact"],
                recommended_response=s["recommended_response"],
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._scenarios[scenario.name] = scenario

    def predict(self, scenario_name: str) -> Optional[dict]:
        with self._lock:
            s = self._scenarios.get(scenario_name)
            return asdict(s) if s else None

    def all_scenarios(self) -> List[dict]:
        with self._lock:
            return [asdict(s) for s in self._scenarios.values()]

    def worst_case_scenarios(self, threshold: float = 0.7) -> List[dict]:
        with self._lock:
            return [asdict(s) for s in self._scenarios.values() if s.severity >= threshold]


stress_outcome_predictor = StressOutcomePredictor()

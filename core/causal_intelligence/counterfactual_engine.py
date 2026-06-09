"""Counterfactual engine for causal inference."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Union


@dataclass
class Counterfactual:
    cf_id: str
    question: str
    actual_outcome: object
    counterfactual_outcome: object
    difference: object
    confidence: float
    method: str
    created_at: str


class CounterfactualEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._counterfactuals: list = []
        self._counter = 0

    def ask(self, question: str, actual_outcome, counterfactual_scenario, confidence: float = 0.5) -> dict:
        with self._lock:
            self._counter += 1
            if isinstance(actual_outcome, (int, float)) and isinstance(counterfactual_scenario, (int, float)):
                difference = counterfactual_scenario - actual_outcome
                method = "HISTORICAL_COMPARISON"
            elif isinstance(actual_outcome, str) and isinstance(counterfactual_scenario, str):
                difference = "changed" if actual_outcome != counterfactual_scenario else "unchanged"
                method = "EXPERT_RULE"
            else:
                difference = str(counterfactual_scenario)
                method = "SIMULATION"
            cf = Counterfactual(
                cf_id=f"CF-{self._counter:04d}",
                question=question,
                actual_outcome=actual_outcome,
                counterfactual_outcome=counterfactual_scenario,
                difference=difference,
                confidence=confidence,
                method=method,
                created_at=datetime.utcnow().isoformat(),
            )
            self._counterfactuals.append(cf)
            return asdict(cf)

    def all_counterfactuals(self, limit: int = 50) -> list:
        with self._lock:
            return [asdict(c) for c in self._counterfactuals[-limit:]]

    def counterfactual_insights(self) -> dict:
        with self._lock:
            groups: dict = {}
            for c in self._counterfactuals:
                key = c.question[:40]
                groups.setdefault(key, []).append(c.difference)
            return {"question_groups": {k: v for k, v in list(groups.items())[:10]},
                    "total": len(self._counterfactuals)}


counterfactual_engine = CounterfactualEngine()

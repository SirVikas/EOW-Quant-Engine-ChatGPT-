"""Capital Strategy Director — sets capital allocation strategy."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CapitalStrategy:
    strategy_id: str
    name: str
    allocation_rules: dict
    risk_budget_pct: float
    approved_by: str
    effective_from: datetime


class CapitalStrategyDirector:
    def __init__(self):
        self._lock = threading.RLock()
        self._strategies: list[CapitalStrategy] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CST-{self._counter:03d}"

    def set_strategy(self, name: str, allocation_rules: dict,
                     risk_budget_pct: float, approved_by: str) -> CapitalStrategy:
        with self._lock:
            s = CapitalStrategy(
                strategy_id=self._next_id(),
                name=name,
                allocation_rules=allocation_rules,
                risk_budget_pct=risk_budget_pct,
                approved_by=approved_by,
                effective_from=datetime.utcnow(),
            )
            self._strategies.append(s)
            return s

    def current_strategy(self) -> Optional[dict]:
        with self._lock:
            if not self._strategies:
                return None
            s = self._strategies[-1]
            return {"strategy_id": s.strategy_id, "name": s.name,
                    "allocation_rules": s.allocation_rules,
                    "risk_budget_pct": s.risk_budget_pct,
                    "approved_by": s.approved_by,
                    "effective_from": s.effective_from.isoformat()}

    def strategy_history(self) -> list[dict]:
        with self._lock:
            return [
                {"strategy_id": s.strategy_id, "name": s.name,
                 "effective_from": s.effective_from.isoformat()}
                for s in self._strategies
            ]


capital_strategy_director = CapitalStrategyDirector()

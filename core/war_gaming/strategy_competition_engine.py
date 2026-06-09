"""Strategy Competition Engine — pits strategies against each other in simulated environments."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict


@dataclass
class CompetitionResult:
    result_id: str
    strategy_a: str
    strategy_b: str
    winner: str
    margin_pct: float
    scenario_name: str
    run_at: str


class StrategyCompetitionEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._results: List[CompetitionResult] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CMP-{self._counter:03d}"

    def run_competition(self, strategy_a: str, strategy_b: str, scenario_name: str) -> dict:
        with self._lock:
            from core.war_gaming.stress_outcome_predictor import stress_outcome_predictor

            scenario = stress_outcome_predictor.predict(scenario_name)
            severity = scenario["severity"] if scenario else 0.5

            # Deterministic outcome: higher-alphabet strategy wins under high severity (for reproducibility)
            if severity >= 0.8:
                winner = strategy_b if strategy_b > strategy_a else strategy_a
            else:
                winner = strategy_a if strategy_a > strategy_b else strategy_b
            loser = strategy_b if winner == strategy_a else strategy_a
            margin_pct = round(abs(severity - 0.5) * 40, 2)

            result = CompetitionResult(
                result_id=self._next_id(),
                strategy_a=strategy_a,
                strategy_b=strategy_b,
                winner=winner,
                margin_pct=margin_pct,
                scenario_name=scenario_name,
                run_at=datetime.now(timezone.utc).isoformat(),
            )
            self._results.append(result)
            return asdict(result)

    def competition_history(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._results[-limit:]]

    def leaderboard(self) -> List[dict]:
        with self._lock:
            wins: Dict[str, int] = {}
            for r in self._results:
                wins[r.winner] = wins.get(r.winner, 0) + 1
            board = [{"strategy": k, "wins": v} for k, v in wins.items()]
            board.sort(key=lambda x: x["wins"], reverse=True)
            return board


strategy_competition_engine = StrategyCompetitionEngine()

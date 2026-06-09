"""War Game Engine — master orchestrator for all war gaming subsystems."""
import threading
from datetime import datetime, timezone
from typing import List


class WarGameEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._games_run: int = 0
        self._scenarios_tested: List[str] = []

    def run_full_war_game(self, scenario_name: str) -> dict:
        with self._lock:
            from core.war_gaming.stress_outcome_predictor import stress_outcome_predictor
            from core.war_gaming.scenario_battlefield import scenario_battlefield
            from core.war_gaming.strategy_competition_engine import strategy_competition_engine

            self._games_run += 1
            if scenario_name not in self._scenarios_tested:
                self._scenarios_tested.append(scenario_name)

            prediction = stress_outcome_predictor.predict(scenario_name)
            if not prediction:
                return {"error": f"Unknown scenario: {scenario_name}"}

            scenario_battlefield.start_scenario(scenario_name)
            scenario_battlefield.advance_round()
            scenario_battlefield.advance_round()
            battlefield_state = scenario_battlefield.get_state()
            scenario_battlefield.end_scenario()

            competition = strategy_competition_engine.run_competition(
                "MOMENTUM_STRATEGY", "MEAN_REVERSION_STRATEGY", scenario_name
            )

            return {
                "scenario": scenario_name,
                "severity": prediction["severity"],
                "predicted_impact": prediction["predicted_impact"],
                "recommended_response": prediction["recommended_response"],
                "competition_result": competition,
                "battlefield_rounds": battlefield_state["rounds_elapsed"],
                "run_at": datetime.now(timezone.utc).isoformat(),
            }

    def war_game_summary(self) -> dict:
        with self._lock:
            from core.war_gaming.stress_outcome_predictor import stress_outcome_predictor

            worst = stress_outcome_predictor.worst_case_scenarios(threshold=0.75)
            return {
                "total_games_run": self._games_run,
                "scenarios_tested": list(self._scenarios_tested),
                "critical_vulnerabilities_found": len(worst),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def one_liner(self) -> str:
        with self._lock:
            return (
                f"PHOENIX War Gaming: {self._games_run} games run, "
                f"{len(self._scenarios_tested)} scenarios tested"
            )


war_game_engine = WarGameEngine()

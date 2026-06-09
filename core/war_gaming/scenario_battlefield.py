"""Scenario Battlefield — manages active war game simulations."""
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ScenarioBattlefield:
    def __init__(self):
        self._lock = threading.RLock()
        self._active_scenario: Optional[str] = None
        self._rounds_elapsed: int = 0
        self._agent_positions: Dict[str, str] = {}
        self._event_log: List[dict] = []

    def start_scenario(self, scenario_name: str) -> dict:
        with self._lock:
            self._active_scenario = scenario_name
            self._rounds_elapsed = 0
            self._agent_positions = {}
            self._event_log = []
            event = {
                "event": "scenario_started",
                "scenario": scenario_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._event_log.append(event)
            return {"status": "STARTED", "scenario": scenario_name}

    def advance_round(self) -> dict:
        with self._lock:
            if not self._active_scenario:
                return {"status": "NO_ACTIVE_SCENARIO"}
            self._rounds_elapsed += 1
            event = {
                "event": "round_advanced",
                "round": self._rounds_elapsed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._event_log.append(event)
            return {"round": self._rounds_elapsed, "scenario": self._active_scenario}

    def get_state(self) -> dict:
        with self._lock:
            return {
                "active_scenario": self._active_scenario,
                "rounds_elapsed": self._rounds_elapsed,
                "agent_positions": dict(self._agent_positions),
                "event_log": list(self._event_log[-20:]),
            }

    def end_scenario(self) -> dict:
        with self._lock:
            ended = self._active_scenario
            event = {
                "event": "scenario_ended",
                "scenario": ended,
                "total_rounds": self._rounds_elapsed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._event_log.append(event)
            self._active_scenario = None
            return {"status": "ENDED", "scenario": ended, "rounds_completed": self._rounds_elapsed}


scenario_battlefield = ScenarioBattlefield()

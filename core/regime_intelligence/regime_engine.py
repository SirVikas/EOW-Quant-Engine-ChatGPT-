"""Regime Engine — orchestrates regime intelligence across all sub-components."""
import threading
import time


class RegimeEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def update_regime(self, regime: str, trigger: str = "", characteristics: dict = None) -> dict:
        from core.regime_intelligence.regime_history import regime_history
        from core.regime_intelligence.regime_transition_tracker import regime_transition_tracker

        with self._lock:
            current = regime_history.current_regime()
            from_regime = current.get("regime", "UNKNOWN") if current else "UNKNOWN"

            rid = regime_history.record_regime(regime, characteristics, trigger)
            if from_regime != "UNKNOWN":
                regime_transition_tracker.record_transition(from_regime, regime, trigger)

            return {"record_id": rid, "regime": regime, "from_regime": from_regime}

    def current_regime(self) -> dict:
        from core.regime_intelligence.regime_history import regime_history
        return regime_history.current_regime()

    def regime_context(self) -> dict:
        from core.regime_intelligence.regime_history import regime_history
        from core.regime_intelligence.regime_transition_tracker import regime_transition_tracker

        return {
            "current": regime_history.current_regime(),
            "recent_transitions": regime_transition_tracker.recent_transitions(limit=5),
            "regime_stats": regime_history.regime_stats(),
            "regime_awareness": True,
        }

    def enrich_with_regime(self, data_dict: dict) -> dict:
        data_dict["regime_context"] = self.regime_context()
        return data_dict


regime_engine = RegimeEngine()

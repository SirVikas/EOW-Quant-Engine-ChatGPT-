"""Regime Transition Tracker — records and analyzes regime-to-regime transitions."""
import threading
import time
from dataclasses import dataclass


@dataclass
class Transition:
    transition_id: str
    from_regime: str
    to_regime: str
    transition_at: float
    trigger: str
    impact_assessment: dict


class RegimeTransitionTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._transitions: list[Transition] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"TRN-{self._counter:03d}"

    def record_transition(self, from_regime: str, to_regime: str, trigger: str,
                           impact_assessment: dict = None) -> str:
        with self._lock:
            tid = self._next_id()
            self._transitions.append(Transition(
                transition_id=tid,
                from_regime=from_regime,
                to_regime=to_regime,
                transition_at=time.time(),
                trigger=trigger,
                impact_assessment=impact_assessment or {},
            ))
            return tid

    def recent_transitions(self, limit: int = 10) -> list:
        with self._lock:
            return [vars(t) for t in self._transitions[-limit:]]

    def transition_matrix(self) -> dict:
        with self._lock:
            matrix: dict = {}
            for t in self._transitions:
                if t.from_regime not in matrix:
                    matrix[t.from_regime] = {}
                matrix[t.from_regime][t.to_regime] = matrix[t.from_regime].get(t.to_regime, 0) + 1
            return matrix

    def high_risk_transitions(self) -> list:
        with self._lock:
            high_risk = {"CRISIS", "VOLATILE"}
            return [vars(t) for t in self._transitions if t.to_regime.upper() in high_risk]


regime_transition_tracker = RegimeTransitionTracker()

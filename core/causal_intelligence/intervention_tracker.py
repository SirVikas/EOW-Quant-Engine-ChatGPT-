"""Intervention tracker for causal inference."""
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class Intervention:
    intervention_id: str
    cause_candidate: str
    effect_candidate: str
    intervention_type: str
    before_state: dict
    after_state: dict
    effect_observed: dict
    recorded_at: str


class InterventionTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._interventions: list = []
        self._counter = 0

    def record_intervention(self, cause_candidate: str, effect_candidate: str, intervention_type: str,
                             before_state: dict, after_state: dict, effect_observed: dict) -> dict:
        with self._lock:
            self._counter += 1
            i = Intervention(
                intervention_id=f"INT-{self._counter:03d}",
                cause_candidate=cause_candidate,
                effect_candidate=effect_candidate,
                intervention_type=intervention_type,
                before_state=before_state,
                after_state=after_state,
                effect_observed=effect_observed,
                recorded_at=datetime.utcnow().isoformat(),
            )
            self._interventions.append(i)
            return asdict(i)

    def all_interventions(self, limit: int = 50) -> list:
        with self._lock:
            return [asdict(i) for i in self._interventions[-limit:]]

    def interventions_for(self, cause_candidate: str) -> list:
        with self._lock:
            return [asdict(i) for i in self._interventions if i.cause_candidate == cause_candidate]


intervention_tracker = InterventionTracker()

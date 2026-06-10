"""
Playbook registry — maps known failure types to recovery procedures.
Package is named self_healing_playbooks (not self_healing as proposed in the
gap review) because core/self_healing.py hosts the live SelfHealingProtocol
and a package of the same name would shadow it at import time.
"""
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_SEED_PLAYBOOKS = [
    ("WS_STALE", [
        "Confirm tick staleness via trade_flow_monitor",
        "Allow SelfHealingProtocol one stale cycle before reconnect",
        "Trigger WebSocket reconnect with backoff",
    ], ["Tick flow resumed within 2 heal cycles"]),
    ("API_TIMEOUT", [
        "Ping exchange REST endpoint",
        "Back off API calls with exponential delay",
        "Re-establish session once ping succeeds",
    ], ["API ping returns OK"]),
    ("REDIS_DOWN", [
        "Confirm Redis connectivity via redis_health",
        "Fall back to in-process buffers",
        "Restore Redis-backed persistence after reconnect",
    ], ["Redis health check passes"]),
    ("DATA_GAP", [
        "Identify gap window in DataLake candles",
        "Backfill missing candles from exchange history",
        "Re-validate indicators over backfilled window",
    ], ["No gaps detected in affected window"]),
    ("DRIFT_DETECTED", [
        "Review drift detection report for affected strategy",
        "Freeze allocation increases for drifting strategy",
        "Re-baseline expected behavior after review",
    ], ["Drift score back under alert threshold"]),
    ("SAFE_MODE_TRIGGERED", [
        "Identify gate failures that triggered safe mode",
        "Resolve underlying gate condition",
        "Exit safe mode only after gates re-validate",
    ], ["Engine state LIVE with gates passing"]),
]


@dataclass
class Playbook:
    playbook_id: str
    failure_type: str
    steps: List[str]
    verification_steps: List[str] = field(default_factory=list)


class PlaybookRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._playbooks: Dict[str, Playbook] = {}
        self._counter = 0
        for failure_type, steps, verification in _SEED_PLAYBOOKS:
            self.register(failure_type, steps, verification)

    def register(self, failure_type: str, steps: List[str],
                 verification_steps: List[str] = None) -> Playbook:
        failure_type = str(failure_type).upper()
        with self._lock:
            existing = self._playbooks.get(failure_type)
            if existing:
                existing.steps = list(steps)
                existing.verification_steps = list(verification_steps or [])
                return existing
            self._counter += 1
            playbook = Playbook(
                playbook_id=f"SHP-{self._counter:03d}",
                failure_type=failure_type,
                steps=list(steps),
                verification_steps=list(verification_steps or []),
            )
            self._playbooks[failure_type] = playbook
            return playbook

    def find_for(self, failure_type: str) -> Optional[Playbook]:
        with self._lock:
            return self._playbooks.get(str(failure_type).upper())

    def all_playbooks(self) -> dict:
        with self._lock:
            return {
                "total": len(self._playbooks),
                "playbooks": [vars(p) for p in self._playbooks.values()],
            }


playbook_registry = PlaybookRegistry()

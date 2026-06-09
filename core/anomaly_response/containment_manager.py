"""
Containment manager — maps anomaly types to containment actions.
Advisory only: actions are recorded recommendations, never direct
interventions in the live trading loop.
"""
import threading
import time
from typing import List

_CONTAINMENT_ACTIONS = {
    "WS_STALE": "Hold new signal intake until tick flow recovers; rely on self-healing WS reconnect",
    "API_TIMEOUT": "Back off API-dependent operations; verify connectivity before resuming",
    "DATA_GAP": "Quarantine affected candles; suspend indicator trust until backfill confirmed",
    "DATA_STALE": "Quarantine affected feed; flag dependent strategies for review",
    "DRIFT_DETECTED": "Flag drifting strategy for review; freeze allocation increases",
    "LOSS_CLUSTER": "Respect drawdown controller limits; review strategy loss cap",
    "SAFE_MODE_TRIGGERED": "Keep safe mode active; require gate re-validation before exit",
    "REDIS_DOWN": "Fall back to in-process buffers; avoid Redis-dependent persistence",
}
_DEFAULT_ACTION = "Isolate affected subsystem and observe before intervention"


class ContainmentManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._containments: List[dict] = []
        self._counter = 0

    def contain(self, response_id: str, anomaly_type: str) -> dict:
        action = _CONTAINMENT_ACTIONS.get(str(anomaly_type).upper(), _DEFAULT_ACTION)
        with self._lock:
            self._counter += 1
            containment = {
                "containment_id": f"ARC-{self._counter:03d}",
                "response_id": response_id,
                "anomaly_type": str(anomaly_type).upper(),
                "action": action,
                "mode": "ADVISORY",
                "contained_at": time.time(),
            }
            self._containments.append(containment)
            return containment

    def containment_summary(self) -> dict:
        with self._lock:
            containments = list(self._containments)
            by_type: dict = {}
            for c in containments:
                by_type[c["anomaly_type"]] = by_type.get(c["anomaly_type"], 0) + 1
            return {
                "total": len(containments),
                "by_anomaly_type": by_type,
                "known_anomaly_types": sorted(_CONTAINMENT_ACTIONS.keys()),
                "recent": containments[-10:],
            }


containment_manager = ContainmentManager()

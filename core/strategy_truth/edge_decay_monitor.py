"""GAP-01: Edge Decay Monitor — monitors alpha edge decay over time."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class DecayRecord:
    decay_id: str
    signal_name: str
    initial_edge_pct: float
    current_edge_pct: float
    decay_rate_pct_per_month: float
    status: str  # STABLE/DECAYING/DEPLETED
    measured_at: int


class EdgeDecayMonitor:
    """Monitors alpha edge decay over time. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, DecayRecord] = {}
        self._counter = 0
        logger.info("[GAP-01] EdgeDecayMonitor initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"EDM-{self._counter:03d}"

    def _compute_status(self, initial: float, current: float) -> str:
        if current <= 0:
            return "DEPLETED"
        decay_pct = (initial - current) / initial * 100 if initial > 0 else 0
        if decay_pct > 20:
            return "DECAYING"
        return "STABLE"

    def _compute_decay_rate(self, initial: float, current: float) -> float:
        # Simplified: assumes 1 month measurement period
        if initial <= 0:
            return 0.0
        return round((initial - current) / initial * 100, 4)

    def record_measurement(
        self,
        signal_name: str,
        initial_edge_pct: float,
        current_edge_pct: float,
    ) -> str:
        with self._lock:
            did = self._next_id()
            self._records[did] = DecayRecord(
                decay_id=did,
                signal_name=signal_name,
                initial_edge_pct=initial_edge_pct,
                current_edge_pct=current_edge_pct,
                decay_rate_pct_per_month=self._compute_decay_rate(initial_edge_pct, current_edge_pct),
                status=self._compute_status(initial_edge_pct, current_edge_pct),
                measured_at=int(time.time() * 1000),
            )
            return did

    def decaying_edges(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.status in {"DECAYING", "DEPLETED"}]

    def edge_health_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            stable = sum(1 for r in self._records.values() if r.status == "STABLE")
            decaying = sum(1 for r in self._records.values() if r.status == "DECAYING")
            depleted = sum(1 for r in self._records.values() if r.status == "DEPLETED")
            return {
                "total_edges_tracked": total,
                "stable": stable,
                "decaying": decaying,
                "depleted": depleted,
                "health_pct": round(stable / total * 100, 2) if total > 0 else 100.0,
                "ts": int(time.time() * 1000),
            }


edge_decay_monitor = EdgeDecayMonitor()

"""GAP-04: Survivability Tracker — tracks system survivability over time horizons."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List

from loguru import logger


@dataclass
class SurvivabilityRecord:
    track_id: str
    horizon_label: str  # 30D/90D/180D/365D
    start_date: str
    metrics_snapshot: Dict[str, Any]
    still_alive: bool
    recorded_at: int


class SurvivabilityTracker:
    """Tracks system survivability over time horizons. Thread-safe."""

    VALID_HORIZONS = {"30D", "90D", "180D", "365D"}

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[SurvivabilityRecord] = []
        self._counter = 0
        logger.info("[GAP-04] SurvivabilityTracker initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"SRV-{self._counter:03d}"

    def record(self, horizon_label: str, metrics_snapshot: Dict[str, Any], still_alive: bool) -> str:
        with self._lock:
            tid = self._next_id()
            self._records.append(SurvivabilityRecord(
                track_id=tid,
                horizon_label=horizon_label if horizon_label in self.VALID_HORIZONS else "30D",
                start_date=str(int(time.time())),
                metrics_snapshot=metrics_snapshot,
                still_alive=still_alive,
                recorded_at=int(time.time() * 1000),
            ))
            return tid

    def by_horizon(self, horizon_label: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.horizon_label == horizon_label]

    def survivability_rate(self, horizon_label: str) -> float:
        with self._lock:
            horizon_recs = [r for r in self._records if r.horizon_label == horizon_label]
            if not horizon_recs:
                return 0.0
            survived = sum(1 for r in horizon_recs if r.still_alive)
            return round(survived / len(horizon_recs) * 100, 2)


survivability_tracker = SurvivabilityTracker()

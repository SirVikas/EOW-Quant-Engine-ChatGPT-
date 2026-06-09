"""GAP-04: Stability Monitor — monitors system stability over long periods."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class StabilityRecord:
    mon_id: str
    metric_name: str
    period: str
    mean_value: float
    std_dev: float
    stability_score: float  # 0-100
    drift_detected: bool
    recorded_at: int


class StabilityMonitor:
    """Monitors system stability over long periods. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[StabilityRecord] = []
        self._counter = 0
        logger.info("[GAP-04] StabilityMonitor initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"STB-{self._counter:03d}"

    def _compute_stability_score(self, mean_value: float, std_dev: float) -> float:
        # CV-based stability: lower coefficient of variation = more stable
        if mean_value == 0:
            return 50.0
        cv = abs(std_dev / mean_value)
        score = max(0.0, min(100.0, 100.0 - cv * 100))
        return round(score, 2)

    def record(self, metric_name: str, period: str, mean_value: float, std_dev: float) -> str:
        with self._lock:
            mid = self._next_id()
            score = self._compute_stability_score(mean_value, std_dev)
            drift = score < 50.0
            self._records.append(StabilityRecord(
                mon_id=mid,
                metric_name=metric_name,
                period=period,
                mean_value=mean_value,
                std_dev=std_dev,
                stability_score=score,
                drift_detected=drift,
                recorded_at=int(time.time() * 1000),
            ))
            return mid

    def unstable_metrics(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.drift_detected]

    def stability_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total_metrics": 0, "stable_pct": 100.0, "ts": int(time.time() * 1000)}
            stable = sum(1 for r in self._records if not r.drift_detected)
            avg_score = sum(r.stability_score for r in self._records) / total
            return {
                "total_metrics": total,
                "stable_count": stable,
                "unstable_count": total - stable,
                "stable_pct": round(stable / total * 100, 2),
                "avg_stability_score": round(avg_score, 2),
                "ts": int(time.time() * 1000),
            }


stability_monitor = StabilityMonitor()

"""GAP-02: Expectation Gap Tracker — tracks gaps between expected and observed behavior."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ExpectationGap:
    gap_id: str
    behavior_name: str
    expected_value: float
    observed_value: float
    gap_pct: float
    gap_direction: str  # OVERPERFORM/UNDERPERFORM/AS_EXPECTED
    recorded_at: int


class ExpectationGapTracker:
    """Tracks gaps between expected and observed market behavior. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._gaps: Dict[str, ExpectationGap] = {}
        self._counter = 0
        logger.info("[GAP-02] ExpectationGapTracker initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"EXG-{self._counter:03d}"

    def record(self, behavior_name: str, expected_value: float, observed_value: float) -> str:
        with self._lock:
            if expected_value != 0:
                gap_pct = round((observed_value - expected_value) / abs(expected_value) * 100, 4)
            else:
                gap_pct = 0.0

            if gap_pct > 2:
                direction = "OVERPERFORM"
            elif gap_pct < -2:
                direction = "UNDERPERFORM"
            else:
                direction = "AS_EXPECTED"

            gid = self._next_id()
            self._gaps[gid] = ExpectationGap(
                gap_id=gid,
                behavior_name=behavior_name,
                expected_value=expected_value,
                observed_value=observed_value,
                gap_pct=gap_pct,
                gap_direction=direction,
                recorded_at=int(time.time() * 1000),
            )
            return gid

    def significant_gaps(self, threshold_pct: float = 10.0) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(g) for g in self._gaps.values() if abs(g.gap_pct) >= threshold_pct]

    def gap_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._gaps)
            over = sum(1 for g in self._gaps.values() if g.gap_direction == "OVERPERFORM")
            under = sum(1 for g in self._gaps.values() if g.gap_direction == "UNDERPERFORM")
            as_exp = total - over - under
            return {
                "total_gaps": total,
                "overperforming": over,
                "underperforming": under,
                "as_expected": as_exp,
                "ts": int(time.time() * 1000),
            }


expectation_gap_tracker = ExpectationGapTracker()

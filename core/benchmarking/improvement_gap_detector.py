"""GAP-07: Improvement Gap Detector — detects improvement opportunities vs benchmarks."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ImprovementGap:
    gap_id: str
    area: str
    current_value: float
    benchmark_value: float
    gap_pct: float
    opportunity_size: str  # LARGE/MEDIUM/SMALL
    detected_at: int


class ImprovementGapDetector:
    """Detects improvement opportunities vs benchmarks. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._gaps: Dict[str, ImprovementGap] = {}
        self._counter = 0
        logger.info("[GAP-07] ImprovementGapDetector initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"IMG-{self._counter:03d}"

    def _size_from_gap(self, gap_pct: float) -> str:
        if abs(gap_pct) >= 20:
            return "LARGE"
        elif abs(gap_pct) >= 10:
            return "MEDIUM"
        return "SMALL"

    def detect(self, area: str, current_value: float, benchmark_value: float) -> str:
        with self._lock:
            gid = self._next_id()
            gap_pct = round((benchmark_value - current_value) / abs(benchmark_value) * 100, 4) if benchmark_value != 0 else 0.0
            self._gaps[gid] = ImprovementGap(
                gap_id=gid,
                area=area,
                current_value=current_value,
                benchmark_value=benchmark_value,
                gap_pct=gap_pct,
                opportunity_size=self._size_from_gap(gap_pct),
                detected_at=int(time.time() * 1000),
            )
            return gid

    def large_opportunities(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(g) for g in self._gaps.values() if g.opportunity_size == "LARGE"]

    def gap_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._gaps)
            large = sum(1 for g in self._gaps.values() if g.opportunity_size == "LARGE")
            medium = sum(1 for g in self._gaps.values() if g.opportunity_size == "MEDIUM")
            return {
                "total_gaps": total,
                "large_opportunities": large,
                "medium_opportunities": medium,
                "small_opportunities": total - large - medium,
                "ts": int(time.time() * 1000),
            }


improvement_gap_detector = ImprovementGapDetector()

"""GAP-07: Peer Comparison Tracker — tracks comparisons to peer/baseline strategies."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ComparisonRecord:
    comp_id: str
    benchmark_name: str
    benchmark_type: str  # INTERNAL_BASELINE/HISTORICAL_VERSION/PEER_STRATEGY/INDEX
    phoenix_sharpe: float
    benchmark_sharpe: float
    outperformance_pct: float
    period: str
    recorded_at: int


class PeerComparisonTracker:
    """Tracks comparisons to peer/baseline strategies. Thread-safe."""

    VALID_TYPES = {"INTERNAL_BASELINE", "HISTORICAL_VERSION", "PEER_STRATEGY", "INDEX"}

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, ComparisonRecord] = {}
        self._counter = 0
        logger.info("[GAP-07] PeerComparisonTracker initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"PCM-{self._counter:03d}"

    def record(
        self,
        benchmark_name: str,
        benchmark_type: str,
        phoenix_sharpe: float,
        benchmark_sharpe: float,
        period: str,
    ) -> str:
        with self._lock:
            cid = self._next_id()
            outperf = round(phoenix_sharpe - benchmark_sharpe, 4)
            self._records[cid] = ComparisonRecord(
                comp_id=cid,
                benchmark_name=benchmark_name,
                benchmark_type=benchmark_type if benchmark_type in self.VALID_TYPES else "PEER_STRATEGY",
                phoenix_sharpe=phoenix_sharpe,
                benchmark_sharpe=benchmark_sharpe,
                outperformance_pct=outperf,
                period=period,
                recorded_at=int(time.time() * 1000),
            )
            return cid

    def outperforming_benchmarks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.outperformance_pct > 0]

    def underperforming_benchmarks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.outperformance_pct <= 0]

    def all_records(self) -> List[ComparisonRecord]:
        with self._lock:
            return list(self._records.values())


peer_comparison_tracker = PeerComparisonTracker()

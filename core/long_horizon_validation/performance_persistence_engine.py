"""GAP-04: Performance Persistence Engine — validates that performance persists (not luck)."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class PersistenceRecord:
    persist_id: str
    strategy_name: str
    period_a_sharpe: float
    period_b_sharpe: float
    correlation: float
    persistence_verdict: str  # PERSISTENT/DEGRADING/INCONSISTENT
    analyzed_at: int


class PerformancePersistenceEngine:
    """Validates that performance persists (not luck). Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[PersistenceRecord] = []
        self._counter = 0
        logger.info("[GAP-04] PerformancePersistenceEngine initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"PPE-{self._counter:03d}"

    def _determine_verdict(self, period_a_sharpe: float, period_b_sharpe: float, correlation: float) -> str:
        degradation = (period_a_sharpe - period_b_sharpe) / abs(period_a_sharpe) if period_a_sharpe != 0 else 0
        if correlation > 0.5 and degradation < 0.2:
            return "PERSISTENT"
        elif degradation > 0.3:
            return "DEGRADING"
        return "INCONSISTENT"

    def analyze(
        self,
        strategy_name: str,
        period_a_sharpe: float,
        period_b_sharpe: float,
        correlation: float,
    ) -> str:
        with self._lock:
            pid = self._next_id()
            verdict = self._determine_verdict(period_a_sharpe, period_b_sharpe, correlation)
            self._records.append(PersistenceRecord(
                persist_id=pid,
                strategy_name=strategy_name,
                period_a_sharpe=period_a_sharpe,
                period_b_sharpe=period_b_sharpe,
                correlation=correlation,
                persistence_verdict=verdict,
                analyzed_at=int(time.time() * 1000),
            ))
            return pid

    def persistent_strategies(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.persistence_verdict == "PERSISTENT"]

    def persistence_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            persistent = sum(1 for r in self._records if r.persistence_verdict == "PERSISTENT")
            degrading = sum(1 for r in self._records if r.persistence_verdict == "DEGRADING")
            return {
                "total_analyzed": total,
                "persistent": persistent,
                "degrading": degrading,
                "inconsistent": total - persistent - degrading,
                "persistence_rate_pct": round(persistent / total * 100, 2) if total > 0 else 0.0,
                "ts": int(time.time() * 1000),
            }


performance_persistence_engine = PerformancePersistenceEngine()

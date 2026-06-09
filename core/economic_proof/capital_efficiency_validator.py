"""GAP-08: Capital Efficiency Validator — validates capital efficiency claims."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class EfficiencyRecord:
    eff_id: str
    metric_name: str
    expected_value: float
    actual_value: float
    efficiency_score: float  # 0-100
    verdict: str  # EFFICIENT/ACCEPTABLE/INEFFICIENT
    measured_at: int


class CapitalEfficiencyValidator:
    """Validates capital efficiency claims. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, EfficiencyRecord] = {}
        self._counter = 0
        logger.info("[GAP-08] CapitalEfficiencyValidator initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"CEV-{self._counter:03d}"

    def _compute_efficiency(self, expected: float, actual: float) -> tuple:
        if expected == 0:
            return 50.0, "ACCEPTABLE"
        ratio = actual / expected
        score = min(100.0, max(0.0, ratio * 100))
        if score >= 80:
            verdict = "EFFICIENT"
        elif score >= 50:
            verdict = "ACCEPTABLE"
        else:
            verdict = "INEFFICIENT"
        return round(score, 2), verdict

    def validate(self, metric_name: str, expected_value: float, actual_value: float) -> str:
        with self._lock:
            eid = self._next_id()
            score, verdict = self._compute_efficiency(expected_value, actual_value)
            self._records[eid] = EfficiencyRecord(
                eff_id=eid,
                metric_name=metric_name,
                expected_value=expected_value,
                actual_value=actual_value,
                efficiency_score=score,
                verdict=verdict,
                measured_at=int(time.time() * 1000),
            )
            return eid

    def inefficient_metrics(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.verdict == "INEFFICIENT"]

    def efficiency_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total_metrics": 0, "efficient_pct": 0.0, "avg_efficiency_score": 0.0, "ts": int(time.time() * 1000)}
            efficient = sum(1 for r in self._records.values() if r.verdict == "EFFICIENT")
            avg_score = sum(r.efficiency_score for r in self._records.values()) / total
            return {
                "total_metrics": total,
                "efficient": efficient,
                "acceptable": sum(1 for r in self._records.values() if r.verdict == "ACCEPTABLE"),
                "inefficient": sum(1 for r in self._records.values() if r.verdict == "INEFFICIENT"),
                "efficient_pct": round(efficient / total * 100, 2),
                "avg_efficiency_score": round(avg_score, 2),
                "ts": int(time.time() * 1000),
            }


capital_efficiency_validator = CapitalEfficiencyValidator()

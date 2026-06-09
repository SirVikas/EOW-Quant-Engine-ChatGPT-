"""GAP-01: Signal Truth Validator — validates whether signals have real predictive value."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ValidationRecord:
    validation_id: str
    signal_name: str
    forward_returns_correlation: float
    hit_rate_pct: float
    sample_size: int
    verdict: str  # TRUE_ALPHA/NOISE/INSUFFICIENT_DATA
    validated_at: int


class SignalTruthValidator:
    """Validates whether signals have real predictive value. Thread-safe."""

    MIN_SAMPLE = 30

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, ValidationRecord] = {}
        self._counter = 0
        logger.info("[GAP-01] SignalTruthValidator initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"STV-{self._counter:03d}"

    def _determine_verdict(self, correlation: float, hit_rate_pct: float, sample_size: int) -> str:
        if sample_size < self.MIN_SAMPLE:
            return "INSUFFICIENT_DATA"
        if correlation > 0.1 and hit_rate_pct > 52.0:
            return "TRUE_ALPHA"
        return "NOISE"

    def validate(
        self,
        signal_name: str,
        forward_returns_correlation: float,
        hit_rate_pct: float,
        sample_size: int,
    ) -> str:
        with self._lock:
            vid = self._next_id()
            verdict = self._determine_verdict(forward_returns_correlation, hit_rate_pct, sample_size)
            self._records[vid] = ValidationRecord(
                validation_id=vid,
                signal_name=signal_name,
                forward_returns_correlation=forward_returns_correlation,
                hit_rate_pct=hit_rate_pct,
                sample_size=sample_size,
                verdict=verdict,
                validated_at=int(time.time() * 1000),
            )
            return vid

    def true_alpha_signals(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.verdict == "TRUE_ALPHA"]

    def noise_signals(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.verdict == "NOISE"]

    def validation_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            true_alpha = sum(1 for r in self._records.values() if r.verdict == "TRUE_ALPHA")
            noise = sum(1 for r in self._records.values() if r.verdict == "NOISE")
            insufficient = total - true_alpha - noise
            return {
                "total_validations": total,
                "true_alpha_count": true_alpha,
                "noise_count": noise,
                "insufficient_data_count": insufficient,
                "noise_pct": round(noise / total * 100, 2) if total > 0 else 0.0,
                "ts": int(time.time() * 1000),
            }


signal_truth_validator = SignalTruthValidator()

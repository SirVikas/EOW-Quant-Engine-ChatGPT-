"""GAP-08: ROI Validation Engine — validates ROI claims against observations."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ROIValidation:
    val_id: str
    claim_description: str
    expected_roi_pct: float
    observed_roi_pct: float
    variance_pct: float
    verdict: str  # PROVEN/PARTIALLY_PROVEN/REFUTED/INSUFFICIENT_DATA
    validated_at: int


class ROIValidationEngine:
    """Validates ROI claims against observations. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, ROIValidation] = {}
        self._counter = 0
        logger.info("[GAP-08] ROIValidationEngine initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"ROI-{self._counter:03d}"

    def _verdict(self, expected: float, observed: float) -> str:
        if expected == 0:
            return "INSUFFICIENT_DATA"
        variance = abs(observed - expected) / abs(expected) * 100
        if variance <= 10:
            return "PROVEN"
        elif variance <= 30:
            return "PARTIALLY_PROVEN"
        elif observed < 0 < expected:
            return "REFUTED"
        return "PARTIALLY_PROVEN"

    def validate(self, claim_description: str, expected_roi_pct: float, observed_roi_pct: float) -> str:
        with self._lock:
            vid = self._next_id()
            variance = round(abs(observed_roi_pct - expected_roi_pct), 4)
            self._records[vid] = ROIValidation(
                val_id=vid,
                claim_description=claim_description,
                expected_roi_pct=expected_roi_pct,
                observed_roi_pct=observed_roi_pct,
                variance_pct=variance,
                verdict=self._verdict(expected_roi_pct, observed_roi_pct),
                validated_at=int(time.time() * 1000),
            )
            return vid

    def proven_claims(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.verdict == "PROVEN"]

    def refuted_claims(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.verdict == "REFUTED"]

    def validation_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            proven = sum(1 for r in self._records.values() if r.verdict == "PROVEN")
            refuted = sum(1 for r in self._records.values() if r.verdict == "REFUTED")
            return {
                "total_validations": total,
                "proven": proven,
                "refuted": refuted,
                "partially_proven": total - proven - refuted,
                "proof_rate_pct": round(proven / total * 100, 2) if total > 0 else 0.0,
                "ts": int(time.time() * 1000),
            }


roi_validation_engine = ROIValidationEngine()

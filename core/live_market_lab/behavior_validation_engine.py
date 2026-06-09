"""GAP-02: Behavior Validation Engine — validates behavioral hypotheses against real data."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class HypothesisRecord:
    hyp_id: str
    hypothesis: str
    expected_behavior: str
    observed_behavior: str
    validation_result: str  # CONFIRMED/REFUTED/INCONCLUSIVE
    confidence_pct: float
    validated_at: int


class BehaviorValidationEngine:
    """Validates behavioral hypotheses against real data. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, HypothesisRecord] = {}
        self._counter = 0
        logger.info("[GAP-02] BehaviorValidationEngine initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"BHV-{self._counter:03d}"

    def validate(
        self,
        hypothesis: str,
        expected_behavior: str,
        observed_behavior: str,
        confidence_pct: float,
    ) -> str:
        with self._lock:
            hid = self._next_id()
            if confidence_pct >= 70:
                result = "CONFIRMED" if expected_behavior.lower() in observed_behavior.lower() else "REFUTED"
            else:
                result = "INCONCLUSIVE"
            self._records[hid] = HypothesisRecord(
                hyp_id=hid,
                hypothesis=hypothesis,
                expected_behavior=expected_behavior,
                observed_behavior=observed_behavior,
                validation_result=result,
                confidence_pct=confidence_pct,
                validated_at=int(time.time() * 1000),
            )
            return hid

    def confirmed_hypotheses(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.validation_result == "CONFIRMED"]

    def refuted_hypotheses(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.validation_result == "REFUTED"]

    def hypothesis_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            confirmed = sum(1 for r in self._records.values() if r.validation_result == "CONFIRMED")
            refuted = sum(1 for r in self._records.values() if r.validation_result == "REFUTED")
            return {
                "total": total,
                "confirmed": confirmed,
                "refuted": refuted,
                "inconclusive": total - confirmed - refuted,
                "ts": int(time.time() * 1000),
            }


behavior_validation_engine = BehaviorValidationEngine()

"""GAP-05: Crisis Response Validator — validates crisis response performance."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class CrisisRecord:
    crisis_id: str
    crisis_name: str
    crisis_type: str  # MARKET_CRASH/FLASH_CRASH/LIQUIDITY_CRISIS/GOVERNANCE_FAILURE
    response_time_mins: float
    drawdown_pct: float
    recovery_pct: float
    outcome: str  # SURVIVED/DEGRADED/FAILED
    validated_at: int


class CrisisResponseValidator:
    """Validates crisis response performance. Thread-safe."""

    VALID_TYPES = {"MARKET_CRASH", "FLASH_CRASH", "LIQUIDITY_CRISIS", "GOVERNANCE_FAILURE"}
    VALID_OUTCOMES = {"SURVIVED", "DEGRADED", "FAILED"}

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[CrisisRecord] = []
        self._counter = 0
        logger.info("[GAP-05] CrisisResponseValidator initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"CRV-{self._counter:03d}"

    def record(
        self,
        crisis_name: str,
        crisis_type: str,
        response_time_mins: float,
        drawdown_pct: float,
        recovery_pct: float,
        outcome: str,
    ) -> str:
        with self._lock:
            cid = self._next_id()
            self._records.append(CrisisRecord(
                crisis_id=cid,
                crisis_name=crisis_name,
                crisis_type=crisis_type if crisis_type in self.VALID_TYPES else "MARKET_CRASH",
                response_time_mins=response_time_mins,
                drawdown_pct=drawdown_pct,
                recovery_pct=recovery_pct,
                outcome=outcome if outcome in self.VALID_OUTCOMES else "DEGRADED",
                validated_at=int(time.time() * 1000),
            ))
            return cid

    def failed_crises(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.outcome == "FAILED"]

    def crisis_survival_rate(self) -> float:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return 0.0
            survived = sum(1 for r in self._records if r.outcome == "SURVIVED")
            return round(survived / total * 100, 2)

    def crisis_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            survived = sum(1 for r in self._records if r.outcome == "SURVIVED")
            degraded = sum(1 for r in self._records if r.outcome == "DEGRADED")
            failed = sum(1 for r in self._records if r.outcome == "FAILED")
            return {
                "total_crises": total,
                "survived": survived,
                "degraded": degraded,
                "failed": failed,
                "survival_rate_pct": self.crisis_survival_rate(),
                "ts": int(time.time() * 1000),
            }


crisis_response_validator = CrisisResponseValidator()

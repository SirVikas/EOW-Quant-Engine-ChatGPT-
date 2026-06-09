"""
Data integrity validator — records and tracks OHLC/volume/timestamp check results.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class IntegrityCheck:
    val_id: str
    feed_name: str
    check_type: str   # OHLC_VALID / VOLUME_POSITIVE / TIMESTAMP_SEQUENTIAL / PRICE_REASONABLE
    result: str       # PASS / FAIL
    checked_at: str


class DataIntegrityValidator:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._checks: List[IntegrityCheck] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DIV-{self._counter:03d}"

    def record_check(self, feed_name: str, check_type: str, result: str) -> IntegrityCheck:
        with self._lock:
            chk = IntegrityCheck(
                val_id=self._next_id(),
                feed_name=feed_name,
                check_type=check_type,
                result=result,
                checked_at=datetime.utcnow().isoformat(),
            )
            self._checks.append(chk)
            return chk

    def failing_checks(self) -> List[IntegrityCheck]:
        with self._lock:
            return [c for c in self._checks if c.result == "FAIL"]

    def integrity_score_pct(self, feed_name: str) -> float:
        with self._lock:
            feed_checks = [c for c in self._checks if c.feed_name == feed_name]
            if not feed_checks:
                return 100.0
            passed = sum(1 for c in feed_checks if c.result == "PASS")
            return round(passed / len(feed_checks) * 100, 2)


data_integrity_validator = DataIntegrityValidator()

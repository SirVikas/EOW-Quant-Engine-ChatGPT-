"""Repeat Failure Tracker — tracks recurring failure patterns."""
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class FailureRecord:
    failure_id: str
    failure_type: str
    description: str
    first_seen: float
    last_seen: float
    occurrence_count: int
    root_causes: list
    status: str  # ACTIVE/RESOLVED/MONITORING


class RepeatFailureTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._failures: dict[str, FailureRecord] = {}  # keyed by failure_type
        self._counter = 0

    def record_failure(self, failure_type: str, description: str, root_cause: str = "") -> str:
        with self._lock:
            if failure_type in self._failures:
                rec = self._failures[failure_type]
                rec.occurrence_count += 1
                rec.last_seen = time.time()
                if root_cause and root_cause not in rec.root_causes:
                    rec.root_causes.append(root_cause)
                return rec.failure_id
            else:
                self._counter += 1
                fid = f"FAIL-{self._counter:04d}"
                rec = FailureRecord(
                    failure_id=fid,
                    failure_type=failure_type,
                    description=description,
                    first_seen=time.time(),
                    last_seen=time.time(),
                    occurrence_count=1,
                    root_causes=[root_cause] if root_cause else [],
                    status="ACTIVE",
                )
                self._failures[failure_type] = rec
                return fid

    def most_repeated(self, limit: int = 10) -> list:
        with self._lock:
            sorted_recs = sorted(self._failures.values(), key=lambda r: r.occurrence_count, reverse=True)
            return [asdict(r) for r in sorted_recs[:limit]]

    def chronic_failures(self) -> list:
        with self._lock:
            return [asdict(r) for r in self._failures.values() if r.occurrence_count >= 3]

    def failure_stats(self) -> dict:
        with self._lock:
            total_types = len(self._failures)
            total_occ = sum(r.occurrence_count for r in self._failures.values())
            chronic = sum(1 for r in self._failures.values() if r.occurrence_count >= 3)
            by_type = {ft: r.occurrence_count for ft, r in self._failures.items()}
            return {
                "total_types": total_types,
                "total_occurrences": total_occ,
                "chronic_count": chronic,
                "by_type": by_type,
            }


repeat_failure_tracker = RepeatFailureTracker()

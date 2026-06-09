"""Outcome Tracker — registers expectations and records actual outcomes."""
import threading
import time
from dataclasses import dataclass, field


@dataclass
class OutcomeRecord:
    record_id: str
    subject_id: str
    subject_type: str
    expected_outcome: dict
    actual_outcome: dict
    variance_pct: float
    status: str  # PENDING/CONFIRMED/FAILED/INCONCLUSIVE
    tracked_since: float
    resolved_at: float


class OutcomeTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, OutcomeRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"OTR-{self._counter:03d}"

    def register_expectation(self, subject_id: str, subject_type: str,
                              expected_outcome: dict) -> str:
        with self._lock:
            rec_id = self._next_id()
            self._records[rec_id] = OutcomeRecord(
                record_id=rec_id,
                subject_id=subject_id,
                subject_type=subject_type,
                expected_outcome=expected_outcome,
                actual_outcome={},
                variance_pct=0.0,
                status="PENDING",
                tracked_since=time.time(),
                resolved_at=0.0,
            )
            return rec_id

    def record_actual(self, subject_id: str, actual_outcome: dict) -> dict:
        with self._lock:
            # Find PENDING record for this subject
            record = None
            for r in self._records.values():
                if r.subject_id == subject_id and r.status == "PENDING":
                    record = r
                    break
            if not record:
                return {}

            record.actual_outcome = actual_outcome
            record.resolved_at = time.time()

            # Compute variance on primary numeric field
            expected = record.expected_outcome
            numeric_variances = []
            for k, v in expected.items():
                if isinstance(v, (int, float)) and k in actual_outcome:
                    av = actual_outcome[k]
                    if isinstance(av, (int, float)):
                        vp = abs(av - v) / max(1, abs(v)) * 100
                        numeric_variances.append(vp)

            variance_pct = numeric_variances[0] if numeric_variances else 0.0
            record.variance_pct = variance_pct

            if variance_pct <= 20:
                record.status = "CONFIRMED"
            elif variance_pct <= 50:
                record.status = "INCONCLUSIVE"
            else:
                record.status = "FAILED"

            return vars(record)

    def pending_validations(self) -> list:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.status == "PENDING"]

    def all_outcomes(self, status_filter: str = None) -> list:
        with self._lock:
            items = list(self._records.values())
            if status_filter:
                items = [r for r in items if r.status == status_filter]
            return [vars(r) for r in items]

    def outcome_stats(self) -> dict:
        with self._lock:
            items = list(self._records.values())
            total = len(items)
            variances = [r.variance_pct for r in items if r.status != "PENDING"]
            return {
                "total": total,
                "confirmed": sum(1 for r in items if r.status == "CONFIRMED"),
                "failed": sum(1 for r in items if r.status == "FAILED"),
                "inconclusive": sum(1 for r in items if r.status == "INCONCLUSIVE"),
                "pending": sum(1 for r in items if r.status == "PENDING"),
                "avg_variance_pct": sum(variances) / len(variances) if variances else 0.0,
            }


outcome_tracker = OutcomeTracker()

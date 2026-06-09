"""Root Cause Validation Engine — validates that implemented fixes resolve root causes."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ValidationRecord:
    validation_id: str
    root_cause_id: str
    root_cause_description: str
    implemented_fix: str
    observed_outcome: Optional[str]
    validation_result: Optional[str]  # CONFIRMED/PARTIALLY_CONFIRMED/REFUTED/INCONCLUSIVE
    accuracy_score: Optional[float]
    validated_at: Optional[float]


class RootCauseValidationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, ValidationRecord] = {}
        self._counter = 0

    def submit_for_validation(self, root_cause_id: str, root_cause_description: str,
                               implemented_fix: str) -> str:
        with self._lock:
            self._counter += 1
            vid = f"RCV-{self._counter:04d}"
            self._records[vid] = ValidationRecord(
                validation_id=vid,
                root_cause_id=root_cause_id,
                root_cause_description=root_cause_description,
                implemented_fix=implemented_fix,
                observed_outcome=None,
                validation_result=None,
                accuracy_score=None,
                validated_at=None,
            )
            return vid

    def record_outcome(self, validation_id: str, observed_outcome: str,
                       validation_result: str, accuracy_score: float) -> bool:
        with self._lock:
            rec = self._records.get(validation_id)
            if not rec:
                return False
            rec.observed_outcome = observed_outcome
            rec.validation_result = validation_result
            rec.accuracy_score = accuracy_score
            rec.validated_at = time.time()
            return True

    def root_cause_accuracy(self, root_cause_description: str) -> float:
        with self._lock:
            matches = [
                r for r in self._records.values()
                if r.root_cause_description == root_cause_description
                and r.accuracy_score is not None
            ]
            if not matches:
                return 0.0
            return round(sum(r.accuracy_score for r in matches) / len(matches), 4)

    def all_validations(self, result_filter: Optional[str] = None) -> list:
        with self._lock:
            if result_filter:
                return [asdict(r) for r in self._records.values() if r.validation_result == result_filter]
            return [asdict(r) for r in self._records.values()]

    def validation_stats(self) -> dict:
        with self._lock:
            recs = list(self._records.values())
            completed = [r for r in recs if r.validation_result is not None]
            if not completed:
                return {"total": len(recs), "confirmed": 0, "partially_confirmed": 0,
                        "refuted": 0, "inconclusive": 0, "avg_accuracy_score": 0,
                        "most_reliable_cause": None}
            counts = {"CONFIRMED": 0, "PARTIALLY_CONFIRMED": 0, "REFUTED": 0, "INCONCLUSIVE": 0}
            for r in completed:
                counts[r.validation_result] = counts.get(r.validation_result, 0) + 1
            avg_acc = sum(r.accuracy_score for r in completed) / len(completed)
            # Most reliable: highest avg accuracy score by root_cause_description
            cause_scores: dict[str, list] = {}
            for r in completed:
                cause_scores.setdefault(r.root_cause_description, []).append(r.accuracy_score)
            most_reliable = max(cause_scores, key=lambda c: sum(cause_scores[c]) / len(cause_scores[c])) if cause_scores else None
            return {
                "total": len(recs),
                "confirmed": counts["CONFIRMED"],
                "partially_confirmed": counts["PARTIALLY_CONFIRMED"],
                "refuted": counts["REFUTED"],
                "inconclusive": counts["INCONCLUSIVE"],
                "avg_accuracy_score": round(avg_acc, 4),
                "most_reliable_cause": most_reliable,
            }

    def diagnostic_reliability_report(self) -> dict:
        with self._lock:
            completed = [r for r in self._records.values() if r.accuracy_score is not None]
            cause_data: dict[str, list] = {}
            for r in completed:
                cause_data.setdefault(r.root_cause_description, []).append(r.accuracy_score)
            report = {}
            for cause, scores in cause_data.items():
                report[cause] = {
                    "samples": len(scores),
                    "avg_accuracy": round(sum(scores) / len(scores), 4),
                    "min_accuracy": min(scores),
                    "max_accuracy": max(scores),
                }
            return report


root_cause_validation_engine = RootCauseValidationEngine()

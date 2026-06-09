"""CTAO — Impact Verification Engine: verifies actual vs expected benefit after implementation."""
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class ImpactRecord:
    record_id: str
    rec_id: str
    expected_benefit: float
    actual_benefit: float
    accuracy_pct: float
    verified_at: float
    verdict: str


class ImpactVerificationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[ImpactRecord] = []
        self._expected: Dict[str, float] = {}

    def record_expected(self, rec_id: str, expected_benefit: float):
        with self._lock:
            self._expected[rec_id] = expected_benefit
            return {"recorded": rec_id, "expected_benefit": expected_benefit}

    def verify_impact(self, rec_id: str, actual_benefit: float) -> dict:
        with self._lock:
            expected = self._expected.get(rec_id, 1.0)
            if actual_benefit < 0:
                verdict = "NEGATIVE"
                accuracy = (actual_benefit / expected * 100) if expected != 0 else 0.0
            elif expected == 0:
                accuracy = 100.0
                verdict = "MET"
            else:
                accuracy = (actual_benefit / expected) * 100
                if accuracy >= 120:
                    verdict = "EXCEEDED"
                elif accuracy >= 90:
                    verdict = "MET"
                elif accuracy >= 50:
                    verdict = "PARTIAL"
                else:
                    verdict = "MISSED"

            rec = ImpactRecord(
                record_id=str(uuid.uuid4()),
                rec_id=rec_id,
                expected_benefit=expected,
                actual_benefit=actual_benefit,
                accuracy_pct=round(accuracy, 2),
                verified_at=time.time(),
                verdict=verdict,
            )
            self._records.append(rec)
            return asdict(rec)

    def all_records(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._records[-limit:]]

    def verification_stats(self) -> dict:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {
                    "total_verified": 0,
                    "avg_accuracy": 0.0,
                    "by_verdict": {},
                    "recommendation_engine_reliability": 0.0,
                }
            avg_acc = sum(r.accuracy_pct for r in self._records) / total
            by_verdict: Dict[str, int] = {}
            for r in self._records:
                by_verdict[r.verdict] = by_verdict.get(r.verdict, 0) + 1
            return {
                "total_verified": total,
                "avg_accuracy": round(avg_acc, 2),
                "by_verdict": by_verdict,
                "recommendation_engine_reliability": round(avg_acc, 2),
            }


impact_verification_engine = ImpactVerificationEngine()

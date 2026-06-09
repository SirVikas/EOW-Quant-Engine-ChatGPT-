"""Recommendation Accuracy Engine — tracks success/failure rates per recommendation."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class AccuracyRecord:
    rec_id: str
    times_suggested: int
    times_successful: int
    times_failed: int
    success_pct: float
    failure_pct: float
    trust_contribution: float
    last_updated: float


class RecommendationAccuracyEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, AccuracyRecord] = {}

    def _get_or_create(self, rec_id: str) -> AccuracyRecord:
        if rec_id not in self._records:
            self._records[rec_id] = AccuracyRecord(
                rec_id=rec_id,
                times_suggested=0,
                times_successful=0,
                times_failed=0,
                success_pct=0.0,
                failure_pct=0.0,
                trust_contribution=0.5,
                last_updated=time.time(),
            )
        return self._records[rec_id]

    def _recompute(self, rec: AccuracyRecord):
        total = rec.times_suggested
        if total == 0:
            rec.success_pct = 0.0
            rec.failure_pct = 0.0
        else:
            rec.success_pct = round(rec.times_successful / total * 100, 2)
            rec.failure_pct = round(rec.times_failed / total * 100, 2)
        rec.last_updated = time.time()

    def record_suggestion(self, rec_id: str):
        with self._lock:
            rec = self._get_or_create(rec_id)
            rec.times_suggested += 1
            self._recompute(rec)

    def record_success(self, rec_id: str):
        with self._lock:
            rec = self._get_or_create(rec_id)
            rec.times_successful += 1
            self._recompute(rec)
            rec.trust_contribution = min(1.0, rec.trust_contribution + 0.05)

    def record_failure(self, rec_id: str):
        with self._lock:
            rec = self._get_or_create(rec_id)
            rec.times_failed += 1
            self._recompute(rec)
            rec.trust_contribution = max(0.0, rec.trust_contribution - 0.10)

    def get_accuracy(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            rec = self._records.get(rec_id)
            return asdict(rec) if rec else None

    def all_accuracy_records(self, min_suggestions: int = 1) -> list:
        with self._lock:
            return [asdict(r) for r in self._records.values() if r.times_suggested >= min_suggestions]

    def accuracy_stats(self) -> dict:
        with self._lock:
            recs = list(self._records.values())
            if not recs:
                return {"total_tracked": 0, "avg_success_pct": 0,
                        "high_trust_recs": 0, "low_trust_recs": 0, "top_3_performers": []}
            avg_success = sum(r.success_pct for r in recs) / len(recs)
            high_trust = sum(1 for r in recs if r.trust_contribution >= 0.7)
            low_trust = sum(1 for r in recs if r.trust_contribution < 0.3)
            top3 = sorted(recs, key=lambda r: r.success_pct, reverse=True)[:3]
            return {
                "total_tracked": len(recs),
                "avg_success_pct": round(avg_success, 2),
                "high_trust_recs": high_trust,
                "low_trust_recs": low_trust,
                "top_3_performers": [asdict(r) for r in top3],
            }


recommendation_accuracy_engine = RecommendationAccuracyEngine()

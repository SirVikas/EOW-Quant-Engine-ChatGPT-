"""Consensus Quality Tracker — monitors quality of collective consensus decisions."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List
import uuid


@dataclass
class QualityRecord:
    record_id: str
    consensus_topic: str
    participating_count: int
    agreement_rate: float  # 0-1
    quality_score: float   # 0-1
    outcome_validated: bool
    recorded_at: str


class ConsensusQualityTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, QualityRecord] = {}

    def record_consensus(self, topic: str, participating_count: int,
                         agreement_rate: float) -> str:
        with self._lock:
            record_id = str(uuid.uuid4())[:8]
            quality_score = agreement_rate * min(1.0, participating_count / 5.0)
            r = QualityRecord(
                record_id=record_id,
                consensus_topic=topic,
                participating_count=participating_count,
                agreement_rate=agreement_rate,
                quality_score=quality_score,
                outcome_validated=False,
                recorded_at=datetime.now(timezone.utc).isoformat(),
            )
            self._records[record_id] = r
            return record_id

    def validate_outcome(self, record_id: str, successful: bool) -> bool:
        with self._lock:
            r = self._records.get(record_id)
            if r is None:
                return False
            r.outcome_validated = True
            if successful:
                r.quality_score = min(1.0, r.quality_score + 0.1)
            return True

    def all_records(self, limit: int = 50) -> List[dict]:
        with self._lock:
            records = sorted(self._records.values(),
                             key=lambda x: x.recorded_at, reverse=True)
            return [asdict(r) for r in records[:limit]]

    def quality_stats(self) -> dict:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total": 0, "avg_quality_score": 0, "high_quality_count": 0, "validated_count": 0}
            avg_quality = sum(r.quality_score for r in self._records.values()) / total
            high_quality = sum(1 for r in self._records.values() if r.quality_score >= 0.7)
            validated = sum(1 for r in self._records.values() if r.outcome_validated)
            return {
                "total": total,
                "avg_quality_score": avg_quality,
                "high_quality_count": high_quality,
                "validated_count": validated,
            }


consensus_quality_tracker = ConsensusQualityTracker()

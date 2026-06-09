"""Strategy Alignment Tracker — tracks how well operations align to strategy."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AlignmentRecord:
    alignment_id: str
    department: str
    initiative_id: str
    alignment_score: int
    assessed_at: datetime


class StrategyAlignmentTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, AlignmentRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SAL-{self._counter:03d}"

    def record_alignment(self, department: str, initiative_id: str,
                         alignment_score: int) -> AlignmentRecord:
        with self._lock:
            rec = AlignmentRecord(
                alignment_id=self._next_id(),
                department=department,
                initiative_id=initiative_id,
                alignment_score=max(0, min(100, alignment_score)),
                assessed_at=datetime.utcnow(),
            )
            self._records[rec.alignment_id] = rec
            return rec

    def misaligned_departments(self, threshold: int = 60) -> list[dict]:
        with self._lock:
            # Latest score per department
            latest: dict[str, int] = {}
            for r in sorted(self._records.values(), key=lambda x: x.assessed_at):
                latest[r.department] = r.alignment_score
            return [
                {"department": dept, "alignment_score": score}
                for dept, score in latest.items() if score < threshold
            ]

    def alignment_report(self) -> dict:
        with self._lock:
            if not self._records:
                return {"total_assessments": 0, "avg_alignment_score": 0}
            scores = [r.alignment_score for r in self._records.values()]
            return {
                "total_assessments": len(self._records),
                "avg_alignment_score": round(sum(scores) / len(scores), 1),
                "departments_assessed": len({r.department for r in self._records.values()}),
            }


strategy_alignment_tracker = StrategyAlignmentTracker()

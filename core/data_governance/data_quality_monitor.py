"""Data Quality Monitor — tracks data quality checks across datasets."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


CheckType = Literal["COMPLETENESS", "ACCURACY", "FRESHNESS", "CONSISTENCY"]
CheckResult = Literal["PASS", "FAIL", "WARN"]


@dataclass
class QualityCheck:
    check_id: str
    dataset_name: str
    check_type: CheckType
    result: CheckResult
    score_pct: float
    checked_at: datetime = field(default_factory=datetime.utcnow)


class DataQualityMonitor:
    def __init__(self):
        self._lock = threading.RLock()
        self._checks: List[QualityCheck] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DQC-{self._counter:03d}"

    def record_check(self, dataset_name: str, check_type: CheckType, result: CheckResult, score_pct: float) -> QualityCheck:
        with self._lock:
            chk = QualityCheck(
                check_id=self._next_id(),
                dataset_name=dataset_name,
                check_type=check_type,
                result=result,
                score_pct=score_pct,
            )
            self._checks.append(chk)
            return chk

    def quality_report(self, dataset_name: str) -> dict:
        with self._lock:
            checks = [c for c in self._checks if c.dataset_name == dataset_name]
            if not checks:
                return {"dataset_name": dataset_name, "checks": 0}
            avg_score = sum(c.score_pct for c in checks) / len(checks)
            return {
                "dataset_name": dataset_name,
                "checks": len(checks),
                "avg_score_pct": round(avg_score, 2),
                "pass_count": sum(1 for c in checks if c.result == "PASS"),
                "fail_count": sum(1 for c in checks if c.result == "FAIL"),
            }

    def failing_datasets(self) -> List[str]:
        with self._lock:
            return list({c.dataset_name for c in self._checks if c.result == "FAIL"})


data_quality_monitor = DataQualityMonitor()

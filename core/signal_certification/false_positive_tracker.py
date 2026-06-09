"""
False positive tracker — measures precision per signal over observation periods.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class FPRecord:
    fp_id: str
    signal_name: str
    period: str
    total_signals: int
    false_positives: int
    precision_pct: float
    recorded_at: str


class FalsePositiveTracker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[FPRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"FPT-{self._counter:03d}"

    def record(
        self,
        signal_name: str,
        period: str,
        total_signals: int,
        false_positives: int,
    ) -> FPRecord:
        precision = round((total_signals - false_positives) / total_signals * 100, 2) if total_signals else 0.0
        with self._lock:
            rec = FPRecord(
                fp_id=self._next_id(),
                signal_name=signal_name,
                period=period,
                total_signals=total_signals,
                false_positives=false_positives,
                precision_pct=precision,
                recorded_at=datetime.utcnow().isoformat(),
            )
            self._records.append(rec)
            return rec

    def high_fp_signals(self, threshold_pct: float = 30) -> List[FPRecord]:
        with self._lock:
            return [r for r in self._records if (r.false_positives / r.total_signals * 100 if r.total_signals else 0) > threshold_pct]

    def precision_report(self) -> dict:
        with self._lock:
            return {
                "total_records": len(self._records),
                "avg_precision_pct": round(
                    sum(r.precision_pct for r in self._records) / len(self._records), 2
                ) if self._records else 100.0,
                "records": [
                    {
                        "signal_name": r.signal_name,
                        "period": r.period,
                        "precision_pct": r.precision_pct,
                        "false_positives": r.false_positives,
                    }
                    for r in self._records
                ],
            }


false_positive_tracker = FalsePositiveTracker()

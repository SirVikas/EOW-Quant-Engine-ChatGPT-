"""
False negative tracker — measures recall per signal to surface missed opportunities.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class FNRecord:
    fn_id: str
    signal_name: str
    period: str
    total_opportunities: int
    missed_opportunities: int
    recall_pct: float
    recorded_at: str


class FalseNegativeTracker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[FNRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"FNT-{self._counter:03d}"

    def record(
        self,
        signal_name: str,
        period: str,
        total_opportunities: int,
        missed_opportunities: int,
    ) -> FNRecord:
        recall = round(
            (total_opportunities - missed_opportunities) / total_opportunities * 100, 2
        ) if total_opportunities else 0.0
        with self._lock:
            rec = FNRecord(
                fn_id=self._next_id(),
                signal_name=signal_name,
                period=period,
                total_opportunities=total_opportunities,
                missed_opportunities=missed_opportunities,
                recall_pct=recall,
                recorded_at=datetime.utcnow().isoformat(),
            )
            self._records.append(rec)
            return rec

    def low_recall_signals(self, threshold_pct: float = 50) -> List[FNRecord]:
        with self._lock:
            return [r for r in self._records if r.recall_pct < threshold_pct]

    def recall_report(self) -> dict:
        with self._lock:
            return {
                "total_records": len(self._records),
                "avg_recall_pct": round(
                    sum(r.recall_pct for r in self._records) / len(self._records), 2
                ) if self._records else 100.0,
                "records": [
                    {
                        "signal_name": r.signal_name,
                        "period": r.period,
                        "recall_pct": r.recall_pct,
                        "missed_opportunities": r.missed_opportunities,
                    }
                    for r in self._records
                ],
            }


false_negative_tracker = FalseNegativeTracker()

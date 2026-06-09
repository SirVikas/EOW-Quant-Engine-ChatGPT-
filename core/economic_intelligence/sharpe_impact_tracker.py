"""Sharpe Impact Tracker — measures Sharpe ratio improvements from recommendations."""
import threading
import time
from dataclasses import dataclass, asdict


@dataclass
class SharpeRecord:
    record_id: str
    rec_id: str
    sharpe_before: float
    sharpe_after: float
    sharpe_delta: float
    period_days: int
    recorded_at: float


class SharpeImpactTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, SharpeRecord] = {}
        self._counter = 0

    def record(self, rec_id: str, sharpe_before: float, sharpe_after: float,
               period_days: int = 30) -> str:
        with self._lock:
            self._counter += 1
            rid = f"SIT-{self._counter:04d}"
            delta = sharpe_after - sharpe_before
            self._records[rec_id] = SharpeRecord(
                record_id=rid,
                rec_id=rec_id,
                sharpe_before=sharpe_before,
                sharpe_after=sharpe_after,
                sharpe_delta=round(delta, 4),
                period_days=period_days,
                recorded_at=time.time(),
            )
            return rid

    def all_records(self, limit: int = 50) -> list:
        with self._lock:
            recs = list(self._records.values())
            return [asdict(r) for r in recs[-limit:]]

    def sharpe_stats(self) -> dict:
        with self._lock:
            recs = list(self._records.values())
            if not recs:
                return {"total_records": 0, "avg_sharpe_delta": 0,
                        "positive_impact_pct": 0, "best_delta": None, "worst_delta": None}
            avg_delta = sum(r.sharpe_delta for r in recs) / len(recs)
            positive = sum(1 for r in recs if r.sharpe_delta > 0)
            best = max(recs, key=lambda r: r.sharpe_delta)
            worst = min(recs, key=lambda r: r.sharpe_delta)
            return {
                "total_records": len(recs),
                "avg_sharpe_delta": round(avg_delta, 4),
                "positive_impact_pct": round(positive / len(recs) * 100, 2),
                "best_delta": best.sharpe_delta,
                "worst_delta": worst.sharpe_delta,
            }


sharpe_impact_tracker = SharpeImpactTracker()

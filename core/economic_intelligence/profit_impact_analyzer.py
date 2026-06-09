"""Profit Impact Analyzer — tracks expected vs actual profit/drawdown for recommendations."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ProfitImpactRecord:
    record_id: str
    rec_id: str
    expected_profit_pct: float
    actual_profit_pct: Optional[float]
    expected_drawdown_reduction: float
    actual_drawdown_reduction: Optional[float]
    accuracy_pct: Optional[float]
    recorded_at: float


class ProfitImpactAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, ProfitImpactRecord] = {}  # keyed by rec_id
        self._counter = 0

    def record_expected(self, rec_id: str, expected_profit_pct: float,
                        expected_drawdown_reduction: float = 0.0) -> str:
        with self._lock:
            self._counter += 1
            rid = f"PIA-{self._counter:04d}"
            self._records[rec_id] = ProfitImpactRecord(
                record_id=rid,
                rec_id=rec_id,
                expected_profit_pct=expected_profit_pct,
                actual_profit_pct=None,
                expected_drawdown_reduction=expected_drawdown_reduction,
                actual_drawdown_reduction=None,
                accuracy_pct=None,
                recorded_at=time.time(),
            )
            return rid

    def record_actual(self, rec_id: str, actual_profit_pct: float,
                      actual_drawdown_reduction: float = 0.0) -> bool:
        with self._lock:
            rec = self._records.get(rec_id)
            if not rec:
                return False
            rec.actual_profit_pct = actual_profit_pct
            rec.actual_drawdown_reduction = actual_drawdown_reduction
            if rec.expected_profit_pct != 0:
                rec.accuracy_pct = round(
                    100.0 - abs(rec.expected_profit_pct - actual_profit_pct) / abs(rec.expected_profit_pct) * 100, 2
                )
            else:
                rec.accuracy_pct = 100.0 if actual_profit_pct == 0 else 0.0
            return True

    def all_records(self, limit: int = 50) -> list:
        with self._lock:
            recs = list(self._records.values())
            return [asdict(r) for r in recs[-limit:]]

    def impact_stats(self) -> dict:
        with self._lock:
            evaluated = [r for r in self._records.values() if r.accuracy_pct is not None]
            if not evaluated:
                return {"total_evaluated": 0, "avg_profit_accuracy": 0, "avg_drawdown_accuracy": 0,
                        "best_rec_id": None, "worst_rec_id": None}
            avg_pa = sum(r.accuracy_pct for r in evaluated) / len(evaluated)
            dd_accs = []
            for r in evaluated:
                if r.expected_drawdown_reduction != 0:
                    dd_acc = 100.0 - abs(r.expected_drawdown_reduction - (r.actual_drawdown_reduction or 0)) / abs(r.expected_drawdown_reduction) * 100
                    dd_accs.append(dd_acc)
            avg_dd = sum(dd_accs) / len(dd_accs) if dd_accs else 0
            best = max(evaluated, key=lambda r: r.accuracy_pct)
            worst = min(evaluated, key=lambda r: r.accuracy_pct)
            return {
                "total_evaluated": len(evaluated),
                "avg_profit_accuracy": round(avg_pa, 2),
                "avg_drawdown_accuracy": round(avg_dd, 2),
                "best_rec_id": best.rec_id,
                "worst_rec_id": worst.rec_id,
            }


profit_impact_analyzer = ProfitImpactAnalyzer()

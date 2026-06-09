"""Expectation vs Reality — gap analysis between expected and actual outcomes."""
import threading
import time
from dataclasses import dataclass


@dataclass
class EVRReport:
    report_id: str
    subject_id: str
    expected: dict
    actual: dict
    gap_analysis: dict
    market_regime: str
    accuracy_score: float  # 0-1
    generated_at: float


class ExpectationVsReality:
    def __init__(self):
        self._lock = threading.RLock()
        self._reports: list[EVRReport] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"EVR-{self._counter:03d}"

    def generate_report(self, subject_id: str, expected: dict, actual: dict,
                        market_regime: str = "UNKNOWN") -> dict:
        with self._lock:
            gap_analysis = {}
            gap_pcts = []
            for k, ev in expected.items():
                if k in actual:
                    av = actual[k]
                    if isinstance(ev, (int, float)) and isinstance(av, (int, float)):
                        gap = av - ev
                        gap_pct = gap / max(0.001, abs(ev)) * 100
                        gap_analysis[k] = {"expected": ev, "actual": av, "gap": gap,
                                           "gap_pct": gap_pct}
                        gap_pcts.append(abs(gap_pct))

            accuracy_score = max(0.0, 1.0 - (sum(gap_pcts) / len(gap_pcts) / 100
                                              if gap_pcts else 0.0))

            report = EVRReport(
                report_id=self._next_id(),
                subject_id=subject_id,
                expected=expected,
                actual=actual,
                gap_analysis=gap_analysis,
                market_regime=market_regime,
                accuracy_score=accuracy_score,
                generated_at=time.time(),
            )
            self._reports.append(report)
            return vars(report)

    def all_reports(self, limit: int = 50) -> list:
        with self._lock:
            return [vars(r) for r in self._reports[-limit:]]

    def accuracy_trend(self) -> dict:
        with self._lock:
            scores = [r.accuracy_score for r in self._reports]
            count = len(scores)
            avg = sum(scores) / count if scores else 0.0
            last3 = scores[-3:] if len(scores) >= 3 else scores
            last3_avg = sum(last3) / len(last3) if last3 else 0.0
            improving = last3_avg > avg if count > 3 else False
            return {
                "reports_count": count,
                "avg_accuracy": avg,
                "improving": improving,
                "last_3_avg": last3_avg,
            }


expectation_vs_reality = ExpectationVsReality()

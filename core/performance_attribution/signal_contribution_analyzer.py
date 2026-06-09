"""Signal Contribution Analyzer — tracks which signals drove performance."""
import threading
import time
from dataclasses import dataclass


@dataclass
class SignalContribution:
    analysis_id: str
    period: str
    signal_name: str
    profit_contribution_pct: float
    trade_count: int
    win_rate: float
    avg_pnl: float
    analyzed_at: float


class SignalContributionAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list[SignalContribution] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SCA-{self._counter:03d}"

    def record_signal_performance(self, signal_name: str, period: str,
                                   profit_contribution_pct: float, trade_count: int,
                                   win_rate: float, avg_pnl: float) -> str:
        with self._lock:
            aid = self._next_id()
            self._records.append(SignalContribution(
                analysis_id=aid,
                period=period,
                signal_name=signal_name,
                profit_contribution_pct=profit_contribution_pct,
                trade_count=trade_count,
                win_rate=win_rate,
                avg_pnl=avg_pnl,
                analyzed_at=time.time(),
            ))
            return aid

    def top_signals(self, period: str = None, limit: int = 5) -> list:
        with self._lock:
            items = self._records[:]
            if period:
                items = [r for r in items if r.period == period]
            items.sort(key=lambda x: x.profit_contribution_pct, reverse=True)
            return [vars(r) for r in items[:limit]]

    def signal_breakdown(self, period: str) -> list:
        with self._lock:
            return [vars(r) for r in self._records if r.period == period]

    def all_analyses(self, limit: int = 50) -> list:
        with self._lock:
            return [vars(r) for r in self._records[-limit:]]


signal_contribution_analyzer = SignalContributionAnalyzer()

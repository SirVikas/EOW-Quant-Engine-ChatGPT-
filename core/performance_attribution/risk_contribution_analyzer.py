"""Risk Contribution Analyzer — tracks which risk factors drove drawdown."""
import threading
import time
from dataclasses import dataclass


@dataclass
class RiskContribution:
    analysis_id: str
    period: str
    risk_factor: str
    drawdown_contribution_pct: float
    volatility_contribution_pct: float
    var_contribution_pct: float
    analyzed_at: float


class RiskContributionAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list[RiskContribution] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RCA-{self._counter:03d}"

    def record_risk_contribution(self, risk_factor: str, period: str,
                                  drawdown_pct: float, volatility_pct: float,
                                  var_pct: float) -> str:
        with self._lock:
            aid = self._next_id()
            self._records.append(RiskContribution(
                analysis_id=aid,
                period=period,
                risk_factor=risk_factor,
                drawdown_contribution_pct=drawdown_pct,
                volatility_contribution_pct=volatility_pct,
                var_contribution_pct=var_pct,
                analyzed_at=time.time(),
            ))
            return aid

    def top_risk_contributors(self, period: str = None, limit: int = 5) -> list:
        with self._lock:
            items = self._records[:]
            if period:
                items = [r for r in items if r.period == period]
            items.sort(key=lambda x: x.drawdown_contribution_pct, reverse=True)
            return [vars(r) for r in items[:limit]]

    def risk_breakdown(self, period: str) -> list:
        with self._lock:
            return [vars(r) for r in self._records if r.period == period]


risk_contribution_analyzer = RiskContributionAnalyzer()

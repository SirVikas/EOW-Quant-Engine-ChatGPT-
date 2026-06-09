"""Regime Contribution Analyzer — tracks performance attribution by market regime."""
import threading
import time
from dataclasses import dataclass


@dataclass
class RegimeContribution:
    analysis_id: str
    regime: str  # BULL/BEAR/SIDEWAYS/VOLATILE/CRISIS
    period: str
    profit_in_regime_pct: float
    days_in_regime: int
    strategy_performance_score: float
    analyzed_at: float


class RegimeContributionAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list[RegimeContribution] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RGCA-{self._counter:03d}"

    def record_regime_performance(self, regime: str, period: str, profit_pct: float,
                                   days_in_regime: int, strategy_score: float) -> str:
        with self._lock:
            aid = self._next_id()
            self._records.append(RegimeContribution(
                analysis_id=aid,
                regime=regime,
                period=period,
                profit_in_regime_pct=profit_pct,
                days_in_regime=days_in_regime,
                strategy_performance_score=strategy_score,
                analyzed_at=time.time(),
            ))
            return aid

    def best_regime(self) -> dict:
        with self._lock:
            if not self._records:
                return {}
            by_regime: dict = {}
            for r in self._records:
                if r.regime not in by_regime:
                    by_regime[r.regime] = []
                by_regime[r.regime].append(r.profit_in_regime_pct)
            avg_by_regime = {rg: sum(v) / len(v) for rg, v in by_regime.items()}
            best = max(avg_by_regime, key=avg_by_regime.get)
            return {"regime": best, "avg_profit_pct": avg_by_regime[best]}

    def worst_regime(self) -> dict:
        with self._lock:
            if not self._records:
                return {}
            by_regime: dict = {}
            for r in self._records:
                if r.regime not in by_regime:
                    by_regime[r.regime] = []
                by_regime[r.regime].append(r.profit_in_regime_pct)
            avg_by_regime = {rg: sum(v) / len(v) for rg, v in by_regime.items()}
            worst = min(avg_by_regime, key=avg_by_regime.get)
            return {"regime": worst, "avg_profit_pct": avg_by_regime[worst]}

    def regime_breakdown(self, period: str = None) -> list:
        with self._lock:
            items = self._records[:]
            if period:
                items = [r for r in items if r.period == period]
            return [vars(r) for r in items]


regime_contribution_analyzer = RegimeContributionAnalyzer()

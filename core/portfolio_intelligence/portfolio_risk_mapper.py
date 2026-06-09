"""Portfolio risk mapper — risk map creation and history."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RiskMap:
    map_id: str
    total_var_pct: float
    max_drawdown_pct: float
    sharpe_estimate: float
    diversification_score: float
    regime_sensitivity: str
    created_at: str


class PortfolioRiskMapper:
    def __init__(self):
        self._lock = threading.RLock()
        self._maps: list = []
        self._counter = 0

    def create_risk_map(self, total_var_pct: float, max_drawdown_pct: float, sharpe_estimate: float) -> dict:
        with self._lock:
            self._counter += 1
            div_score = max(0.0, 1.0 - total_var_pct / 20.0)
            if max_drawdown_pct > 15:
                regime_sens = "HIGH"
            elif max_drawdown_pct > 8:
                regime_sens = "MEDIUM"
            else:
                regime_sens = "LOW"
            m = RiskMap(
                map_id=f"RM-{self._counter:04d}",
                total_var_pct=total_var_pct,
                max_drawdown_pct=max_drawdown_pct,
                sharpe_estimate=sharpe_estimate,
                diversification_score=div_score,
                regime_sensitivity=regime_sens,
                created_at=datetime.utcnow().isoformat(),
            )
            self._maps.append(m)
            return asdict(m)

    def latest_risk_map(self) -> dict:
        with self._lock:
            if not self._maps:
                return {}
            return asdict(self._maps[-1])

    def risk_map_history(self, limit: int = 20) -> list:
        with self._lock:
            return [asdict(m) for m in self._maps[-limit:]]

    def risk_summary(self) -> dict:
        with self._lock:
            if not self._maps:
                return {}
            m = self._maps[-1]
            return {
                "latest_var": m.total_var_pct,
                "latest_drawdown": m.max_drawdown_pct,
                "latest_sharpe": m.sharpe_estimate,
                "regime_sensitivity": m.regime_sensitivity,
                "diversification_score": m.diversification_score,
            }


portfolio_risk_mapper = PortfolioRiskMapper()

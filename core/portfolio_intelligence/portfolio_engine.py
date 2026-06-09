"""Portfolio engine — portfolio snapshot and rebalance recommendations."""
import threading
from datetime import datetime


class PortfolioEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def portfolio_snapshot(self) -> dict:
        from core.portfolio_intelligence.exposure_analyzer import exposure_analyzer
        from core.portfolio_intelligence.portfolio_risk_mapper import portfolio_risk_mapper
        from core.portfolio_intelligence.capital_allocator import capital_allocator

        exposures = exposure_analyzer.concentration_report()
        risk = portfolio_risk_mapper.risk_summary()
        allocations = capital_allocator.allocation_report()

        current_regime = {}
        try:
            from core.regime_intelligence.regime_engine import current_regime as _cr
            current_regime = _cr() if callable(_cr) else {}
        except Exception:
            pass

        critical_count = len(exposures.get("critical_concentrations", []))
        max_dd = risk.get("latest_drawdown", 0)
        health = max(0.0, 100.0 - critical_count * 20.0 - max_dd * 2.0)

        return {
            "snapshot_at": datetime.utcnow().isoformat(),
            "exposures": exposures,
            "risk": risk,
            "allocations": allocations,
            "current_regime": current_regime,
            "portfolio_health_score": health,
        }

    def rebalance_recommendation(self) -> list:
        from core.portfolio_intelligence.exposure_analyzer import exposure_analyzer
        from core.portfolio_intelligence.capital_allocator import capital_allocator

        recs = []
        conc = exposure_analyzer.concentration_report()
        for r in conc.get("critical_concentrations", []):
            recs.append(f"Reduce {r['name']} ({r['exposure_type']}) from {r['exposure_pct']}% — CRITICAL concentration")
        for r in conc.get("high_concentrations", []):
            recs.append(f"Monitor {r['name']} ({r['exposure_type']}) at {r['exposure_pct']}% — HIGH concentration")

        alloc = capital_allocator.allocation_report()
        if alloc.get("over_allocated"):
            recs.append("Portfolio is over-allocated (>100%) — reduce positions")
        if alloc.get("suspended_strategies", 0) > 0:
            recs.append(f"{alloc['suspended_strategies']} strategy(ies) suspended — review for reinstatement")
        return recs


portfolio_engine = PortfolioEngine()

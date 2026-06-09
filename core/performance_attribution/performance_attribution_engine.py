"""Performance Attribution Engine — orchestrates multi-horizon performance attribution."""
import threading
import time


class PerformanceAttributionEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def attribute(self, period: str, total_pnl_pct: float, drawdown_pct: float) -> dict:
        from core.performance_attribution.signal_contribution_analyzer import signal_contribution_analyzer
        from core.performance_attribution.risk_contribution_analyzer import risk_contribution_analyzer
        from core.performance_attribution.regime_contribution_analyzer import regime_contribution_analyzer

        regime_context = {}
        try:
            from core.regime_intelligence.regime_engine import regime_engine
            regime_context = regime_engine.regime_context()
        except Exception:
            pass

        signal_contribs = signal_contribution_analyzer.signal_breakdown(period)
        risk_contribs = risk_contribution_analyzer.risk_breakdown(period)

        # Attribution confidence based on data availability
        attribution_confidence = min(1.0, (len(signal_contribs) + len(risk_contribs)) / 10)

        return {
            "period": period,
            "total_pnl_pct": total_pnl_pct,
            "drawdown_pct": drawdown_pct,
            "signal_contributions": signal_contribs,
            "risk_contributions": risk_contribs,
            "regime_context": regime_context,
            "attribution_confidence": attribution_confidence,
            "generated_at": time.time(),
        }

    def attribution_report(self, period: str = None) -> dict:
        from core.performance_attribution.signal_contribution_analyzer import signal_contribution_analyzer
        from core.performance_attribution.risk_contribution_analyzer import risk_contribution_analyzer
        from core.performance_attribution.regime_contribution_analyzer import regime_contribution_analyzer

        return {
            "period": period,
            "top_signals": signal_contribution_analyzer.top_signals(period=period),
            "top_risks": risk_contribution_analyzer.top_risk_contributors(period=period),
            "regime_breakdown": regime_contribution_analyzer.regime_breakdown(period=period),
            "best_regime": regime_contribution_analyzer.best_regime(),
            "worst_regime": regime_contribution_analyzer.worst_regime(),
            "generated_at": time.time(),
        }

    def why_did_we_win(self, period: str) -> list:
        from core.performance_attribution.signal_contribution_analyzer import signal_contribution_analyzer
        return signal_contribution_analyzer.top_signals(period=period)

    def why_did_we_lose(self, period: str) -> list:
        from core.performance_attribution.risk_contribution_analyzer import risk_contribution_analyzer
        return risk_contribution_analyzer.top_risk_contributors(period=period)


performance_attribution_engine = PerformanceAttributionEngine()

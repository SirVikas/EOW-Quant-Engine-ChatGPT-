"""Strategic outlook builder — assembles multi-horizon strategic outlook."""
import threading
from datetime import datetime


class StrategicOutlookBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build_outlook(self, horizon_days: int = 365) -> dict:
        from core.forecasting.future_risk_mapper import future_risk_mapper
        from core.forecasting.scenario_projection import scenario_projection

        regime_context = {}
        try:
            from core.regime_intelligence.regime_engine import regime_context as _rc
            regime_context = _rc() if callable(_rc) else {}
        except Exception:
            pass

        strategic_forecast = {}
        try:
            from core.strategic_memory.strategic_forecast_engine import strategic_forecast_engine
            strategic_forecast = strategic_forecast_engine.strategic_forecast(horizon_days)
        except Exception:
            pass

        risks = future_risk_mapper.risks_by_horizon(horizon_days)
        scenarios = scenario_projection.scenario_comparison()

        recommendations = []
        critical_risks = [r for r in risks if r.get("severity") == "CRITICAL"]
        for r in critical_risks[:3]:
            recommendations.append(f"Mitigate {r['risk_type']} risk (p={r['probability']:.2f}): {r.get('mitigation', 'No mitigation specified')}")
        if not recommendations:
            recommendations.append("No critical risks identified for this horizon — maintain current posture")

        return {
            "horizon_days": horizon_days,
            "regime_context": regime_context,
            "risk_outlook": risks,
            "scenario_projections": scenarios,
            "strategic_recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }


strategic_outlook_builder = StrategicOutlookBuilder()

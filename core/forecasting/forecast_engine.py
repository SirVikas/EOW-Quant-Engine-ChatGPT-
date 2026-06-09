"""Forecast engine — top-level forecasting interface."""
import threading
from datetime import datetime


class ForecastEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def forecast(self, horizon_days: int = 365) -> dict:
        from core.forecasting.strategic_outlook_builder import strategic_outlook_builder
        return strategic_outlook_builder.build_outlook(horizon_days)

    def multi_horizon_forecast(self) -> dict:
        from core.forecasting.strategic_outlook_builder import strategic_outlook_builder
        return {
            "90d": strategic_outlook_builder.build_outlook(90),
            "180d": strategic_outlook_builder.build_outlook(180),
            "365d": strategic_outlook_builder.build_outlook(365),
            "730d": strategic_outlook_builder.build_outlook(730),
        }

    def forecast_status(self) -> dict:
        from core.forecasting.future_risk_mapper import future_risk_mapper
        from core.forecasting.scenario_projection import scenario_projection
        risk_report = future_risk_mapper.risk_map_report()
        projections = scenario_projection.all_projections()
        horizons = list({p["horizon_days"] for p in projections})
        return {
            "total_projections": len(projections),
            "total_future_risks": risk_report.get("total_projected", 0),
            "horizons_covered": sorted(horizons),
        }


forecast_engine = ForecastEngine()

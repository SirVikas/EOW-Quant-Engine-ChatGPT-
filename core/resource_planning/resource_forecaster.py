"""Resource Forecaster — master resource planning."""
import threading


class ResourceForecaster:
    def __init__(self):
        self._lock = threading.RLock()

    def forecast_report(self) -> dict:
        from core.resource_planning.resource_demand_predictor import resource_demand_predictor
        from core.resource_planning.capacity_planner import capacity_planner
        from core.resource_planning.resource_procurement_engine import resource_procurement_engine

        demand = resource_demand_predictor.upcoming_demand()
        gaps = capacity_planner.capacity_gaps()
        pending = resource_procurement_engine.pending_procurements()

        if len(gaps) > 3 or len(pending) > 5:
            health = "CRITICAL"
        elif gaps or pending:
            health = "STRAINED"
        else:
            health = "ADEQUATE"

        return {
            "demand_summary": demand,
            "capacity_gaps_count": len(gaps),
            "pending_procurements": len(pending),
            "planning_health": health,
        }

    def one_liner(self) -> str:
        report = self.forecast_report()
        return (f"ResourcePlan: health={report['planning_health']} | "
                f"gaps={report['capacity_gaps_count']} | "
                f"pending_procurement={report['pending_procurements']}")


resource_forecaster = ResourceForecaster()

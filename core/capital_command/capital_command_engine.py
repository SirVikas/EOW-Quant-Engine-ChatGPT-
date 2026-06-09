"""Capital Command Engine — master capital command."""
import threading


class CapitalCommandEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def command_status(self) -> dict:
        from core.capital_command.capital_strategy_director import capital_strategy_director
        from core.capital_command.capital_deployment_engine import capital_deployment_engine
        from core.capital_command.capital_reserve_manager import capital_reserve_manager

        current_strategy = capital_strategy_director.current_strategy()
        reserve_health = capital_reserve_manager.reserve_health()
        recent = capital_deployment_engine.recent_deployments(n=5)

        if reserve_health == "CRITICAL":
            readiness = "CRITICAL"
        elif reserve_health == "LOW":
            readiness = "CAUTION"
        else:
            readiness = "READY"

        return {
            "current_strategy": current_strategy,
            "reserve_health": reserve_health,
            "recent_deployments_count": len(recent),
            "capital_readiness": readiness,
        }

    def one_liner(self) -> str:
        status = self.command_status()
        return (f"CapCmd: readiness={status['capital_readiness']} | "
                f"reserve={status['reserve_health']} | "
                f"recent_deployments={status['recent_deployments_count']}")


capital_command_engine = CapitalCommandEngine()

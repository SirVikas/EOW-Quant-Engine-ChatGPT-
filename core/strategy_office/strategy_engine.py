"""Strategy Engine — master strategy office."""
import threading


class StrategyEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def strategy_report(self) -> dict:
        from core.strategy_office.initiative_registry import initiative_registry
        from core.strategy_office.strategy_execution_monitor import strategy_execution_monitor
        from core.strategy_office.strategy_alignment_tracker import strategy_alignment_tracker

        active = initiative_registry.active_initiatives()
        at_risk = strategy_execution_monitor.at_risk_milestones()
        alignment = strategy_alignment_tracker.alignment_report()

        avg_progress = 0.0
        if active:
            avg_progress = round(sum(i["progress_pct"] for i in active) / len(active), 1)

        if at_risk:
            exec_health = "AT_RISK" if len(at_risk) < 3 else "CRITICAL"
        else:
            exec_health = "ON_TRACK"

        return {
            "active_initiatives": len(active),
            "avg_progress_pct": avg_progress,
            "execution_health": exec_health,
            "alignment_summary": alignment,
        }

    def one_liner(self) -> str:
        report = self.strategy_report()
        return (f"Strategy: {report['active_initiatives']} initiatives | "
                f"progress={report['avg_progress_pct']}% | "
                f"health={report['execution_health']}")


strategy_engine = StrategyEngine()

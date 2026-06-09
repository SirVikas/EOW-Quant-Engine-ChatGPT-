"""Command center engine — top-level PHOENIX command center."""
import threading
from datetime import datetime


class CommandCenterEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def dashboard(self) -> dict:
        from core.command_center.mission_control import mission_control
        from core.command_center.executive_console import executive_console
        from core.command_center.alert_center import alert_center

        mc = mission_control.full_status()
        console = executive_console.console_view()
        alert_stats = alert_center.alert_stats()

        return {
            "dashboard_type": "COMMAND_CENTER",
            "mission_control": mc,
            "executive_console": console,
            "alert_stats": alert_stats,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def raise_alert(self, title: str, source_system: str, severity: str, message: str,
                    action_required: bool = False) -> str:
        from core.command_center.alert_center import alert_center
        return alert_center.raise_alert(title, source_system, severity, message, action_required)

    def command_center_status(self) -> dict:
        from core.command_center.mission_control import mission_control
        from core.command_center.alert_center import alert_center
        from core.institutional_scorecard.continuous_score_engine import continuous_score_engine

        mc = mission_control.full_status()
        inst_score = {}
        try:
            inst_score = continuous_score_engine.score()
        except Exception:
            pass
        alert_stats = alert_center.alert_stats()

        return {
            "mission_status": mc.get("mission_status", "UNKNOWN"),
            "score": inst_score.get("continuous_score", 0),
            "alerts_active": alert_stats.get("active", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }


command_center_engine = CommandCenterEngine()

"""Executive console — abbreviated executive-facing command center view."""
import threading
from datetime import datetime


class ExecutiveConsole:
    def __init__(self):
        self._lock = threading.RLock()

    def console_view(self) -> dict:
        from core.command_center.mission_control import mission_control
        status = mission_control.full_status()
        mission_st = status.get("mission_status", "UNKNOWN")
        inst_score = status.get("institutional_score", {})
        score = inst_score.get("continuous_score", 0)
        score_label = inst_score.get("score_label", "UNKNOWN")
        active_alerts = status.get("active_alerts_count", 0)
        critical_alerts = status.get("critical_alerts", [])
        top_3 = critical_alerts[:3]
        executive_verdict = status.get("executive_verdict", {})
        pcao_posture = executive_verdict.get("posture", executive_verdict.get("recommended_posture", "UNKNOWN"))

        if mission_st == "MISSION_CRITICAL":
            next_action = "IMMEDIATE: Address all emergency alerts and escalate to human governance"
        elif mission_st == "RED":
            next_action = "URGENT: Investigate critical alerts and review risk posture"
        elif mission_st == "AMBER":
            next_action = "MONITOR: Review active warnings and validate system health"
        else:
            next_action = "MAINTAIN: System healthy — continue current institutional posture"

        return {
            "system_status": mission_st,
            "institutional_score": score,
            "score_label": score_label,
            "top_3_alerts": top_3,
            "executive_verdict": executive_verdict,
            "pcao_posture": pcao_posture,
            "next_recommended_action": next_action,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def one_liner(self) -> str:
        view = self.console_view()
        status = view.get("system_status", "UNKNOWN")
        score = view.get("institutional_score", 0)
        label = view.get("score_label", "UNKNOWN")
        posture = view.get("pcao_posture", "UNKNOWN")
        from core.command_center.alert_center import alert_center
        critical_count = len(alert_center.active_alerts(severity_filter="CRITICAL"))
        return f"PHOENIX {status} | Score: {score} | {label} | Posture: {posture} | {critical_count} critical alerts"


executive_console = ExecutiveConsole()

"""Mission control — single pane of glass for PHOENIX command center."""
import threading
from datetime import datetime


class MissionControl:
    def __init__(self):
        self._lock = threading.RLock()

    def full_status(self) -> dict:
        from core.command_center.alert_center import alert_center

        obs_health = {}
        try:
            from core.observability_platform.observability_engine import observability_engine
            obs_health = observability_engine.observability_health()
        except Exception:
            pass

        executive_briefing = {}
        try:
            from core.pcao.pcao_engine import pcao_engine
            executive_briefing = pcao_engine.executive_briefing() if hasattr(pcao_engine, "executive_briefing") else {}
        except Exception:
            pass

        institutional_dash = {}
        try:
            from core.maturity_scorecard.institutional_dashboard import institutional_dashboard
            institutional_dash = institutional_dashboard.full_dashboard() if hasattr(institutional_dashboard, "full_dashboard") else {}
        except Exception:
            pass

        human_gov = {}
        try:
            from core.human_governance.human_governance_engine import human_governance_engine
            human_gov = human_governance_engine.human_governance_status() if hasattr(human_governance_engine, "human_governance_status") else {}
        except Exception:
            pass

        institutional_score = {}
        try:
            from core.institutional_scorecard.continuous_score_engine import continuous_score_engine
            institutional_score = continuous_score_engine.score()
        except Exception:
            pass

        active_alerts = alert_center.active_alerts()
        critical_alerts = alert_center.active_alerts(severity_filter="CRITICAL")
        emergency_alerts = alert_center.active_alerts(severity_filter="EMERGENCY")

        if emergency_alerts:
            mission_status = "MISSION_CRITICAL"
        elif critical_alerts:
            mission_status = "RED"
        elif active_alerts:
            mission_status = "AMBER"
        else:
            mission_status = "GREEN"

        return {
            "mission_status": mission_status,
            "executive_verdict": executive_briefing,
            "institutional_score": institutional_score,
            "active_alerts_count": len(active_alerts),
            "critical_alerts": critical_alerts,
            "human_governance": human_gov,
            "observability": obs_health,
            "generated_at": datetime.utcnow().isoformat(),
        }


mission_control = MissionControl()

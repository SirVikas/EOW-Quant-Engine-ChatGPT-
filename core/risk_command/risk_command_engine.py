"""Risk Command Engine — master risk command."""
import threading


class RiskCommandEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def command_center(self) -> dict:
        from core.risk_command.risk_radar import risk_radar
        from core.risk_command.risk_escalation_center import risk_escalation_center
        from core.risk_command.risk_response_director import risk_response_director

        active_risks = risk_radar.active_risks()
        critical_risks = [r for r in active_risks if r["severity"] == "CRITICAL"]
        open_esc = risk_escalation_center.open_escalations()
        effectiveness = risk_response_director.response_effectiveness()

        if critical_risks:
            posture = "RED"
        elif len(active_risks) > 5 or len(open_esc) > 3:
            posture = "YELLOW"
        else:
            posture = "GREEN"

        return {
            "active_risks_count": len(active_risks),
            "critical_risks": critical_risks,
            "open_escalations": len(open_esc),
            "response_effectiveness_pct": effectiveness["effectiveness_pct"],
            "overall_risk_posture": posture,
        }

    def one_liner(self) -> str:
        cc = self.command_center()
        return (f"RiskCmd: posture={cc['overall_risk_posture']} | "
                f"active={cc['active_risks_count']} | "
                f"critical={len(cc['critical_risks'])}")


risk_command_engine = RiskCommandEngine()

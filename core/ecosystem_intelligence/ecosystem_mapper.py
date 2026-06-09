"""Ecosystem Mapper — master ecosystem intelligence orchestrator."""
import threading
from datetime import datetime, timezone


class EcosystemMapper:
    def __init__(self):
        self._lock = threading.RLock()

    def ecosystem_map(self) -> dict:
        with self._lock:
            from core.ecosystem_intelligence.external_dependency_tracker import external_dependency_tracker
            from core.ecosystem_intelligence.environmental_risk_engine import environmental_risk_engine
            from core.ecosystem_intelligence.competitive_intelligence_engine import competitive_intelligence_engine

            health_summary = external_dependency_tracker.dependency_health_summary()
            risk_summary = environmental_risk_engine.risk_summary()
            obs_stats = competitive_intelligence_engine.observation_stats()

            overall_health = "HEALTHY"
            if health_summary.get("overall_health") == "CRITICAL" or risk_summary.get("high_severity_open", 0) > 0:
                overall_health = "AT_RISK"
            elif health_summary.get("overall_health") == "DEGRADED":
                overall_health = "DEGRADED"

            return {
                "external_dependencies": health_summary,
                "environmental_risks": risk_summary,
                "competitive_observations": obs_stats,
                "overall_health": overall_health,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def situational_awareness_report(self) -> dict:
        with self._lock:
            from core.ecosystem_intelligence.external_dependency_tracker import external_dependency_tracker
            from core.ecosystem_intelligence.environmental_risk_engine import environmental_risk_engine
            from core.ecosystem_intelligence.competitive_intelligence_engine import competitive_intelligence_engine

            eco_map = self.ecosystem_map()
            critical_deps = external_dependency_tracker.critical_dependencies()
            open_risks = environmental_risk_engine.open_risks()
            all_obs = competitive_intelligence_engine.all_observations(limit=5)

            return {
                "ecosystem_map": eco_map,
                "critical_dependencies": critical_deps,
                "open_risks": open_risks,
                "recent_competitive_observations": all_obs,
                "report_timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def one_liner(self) -> str:
        eco_map = self.ecosystem_map()
        return (
            f"PHOENIX Ecosystem: {eco_map['external_dependencies'].get('total', 0)} deps "
            f"({eco_map['overall_health']}), "
            f"{eco_map['environmental_risks'].get('open_risks', 0)} open risks"
        )


ecosystem_mapper = EcosystemMapper()

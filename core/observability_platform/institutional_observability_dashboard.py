"""Institutional observability dashboard — master aggregator."""
import threading
from datetime import datetime


class InstitutionalObservabilityDashboard:
    def __init__(self):
        self._lock = threading.RLock()

    def full_dashboard(self) -> dict:
        from core.observability_platform.observability_engine import observability_engine
        from core.observability_platform.anomaly_center import anomaly_center
        from core.observability_platform.real_time_metrics_bus import real_time_metrics_bus as bus

        mc = observability_engine.mission_control()
        stats = anomaly_center.anomaly_stats()
        metrics = bus.all_latest()

        readiness = {}
        try:
            from core.maturity_scorecard.institutional_dashboard import readiness_summary
            readiness = readiness_summary() if callable(readiness_summary) else {}
        except Exception:
            pass

        return {
            "dashboard_type": "INSTITUTIONAL_OBSERVABILITY",
            "mission_control": mc,
            "anomaly_stats": stats,
            "metrics": metrics,
            "readiness": readiness,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def quick_status(self) -> dict:
        from core.observability_platform.observability_engine import observability_engine
        from core.observability_platform.anomaly_center import anomaly_center
        mc = observability_engine.mission_control()
        stats = anomaly_center.anomaly_stats()
        return {
            "status": mc.get("mission_control_status", "UNKNOWN"),
            "critical_anomalies": stats.get("by_severity", {}).get("CRITICAL", 0),
            "layers_healthy": len(mc.get("layer_health", {})),
            "score": 100 - stats.get("active", 0) * 5,
            "generated_at": datetime.utcnow().isoformat(),
        }


institutional_observability_dashboard = InstitutionalObservabilityDashboard()

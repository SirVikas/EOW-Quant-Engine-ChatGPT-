"""
Drift engine — master drift detection aggregator.
"""
import threading


class DriftEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def drift_report(self) -> dict:
        from core.drift_detection.behavior_drift_tracker import behavior_drift_tracker
        from core.drift_detection.performance_drift_detector import performance_drift_detector
        from core.drift_detection.alert_generator import alert_generator

        b_summary = behavior_drift_tracker.drift_summary()
        p_report = performance_drift_detector.performance_drift_report()
        a_stats = alert_generator.alert_stats()

        drifting_count = b_summary["drifting"] + b_summary["critical"]
        critical_count = b_summary["critical"] + a_stats["by_severity"]["CRITICAL"]

        if critical_count > 0:
            overall = "CRITICAL"
        elif drifting_count > 0 or p_report["alerts_triggered"] > 0:
            overall = "DRIFTING"
        else:
            overall = "STABLE"

        return {
            "drifting_components_count": drifting_count,
            "triggered_alerts_count": p_report["alerts_triggered"],
            "critical_drifts": critical_count,
            "active_drift_alerts": a_stats["active"],
            "overall_drift_status": overall,
        }

    def one_liner(self) -> str:
        r = self.drift_report()
        return (
            f"Drift Engine | Status={r['overall_drift_status']} | "
            f"DriftingComponents={r['drifting_components_count']} | "
            f"ActiveAlerts={r['active_drift_alerts']} | "
            f"CriticalDrifts={r['critical_drifts']}"
        )


drift_engine = DriftEngine()

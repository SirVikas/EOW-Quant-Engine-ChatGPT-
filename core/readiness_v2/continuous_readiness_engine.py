"""
Continuous readiness engine — master readiness v2 aggregator.
"""
import threading


class ContinuousReadinessEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def readiness_report(self) -> dict:
        from core.readiness_v2.readiness_trend_tracker import readiness_trend_tracker
        from core.readiness_v2.certification_monitor import certification_monitor
        from core.readiness_v2.compliance_dashboard import compliance_dashboard

        latest_scores = readiness_trend_tracker.latest_scores()
        cert_summary = certification_monitor.certification_summary()
        health = compliance_dashboard.compliance_health()

        # Default scores for dimensions with no data yet
        dimensions = ["ARCHITECTURE", "GOVERNANCE", "VALIDATION", "OPERATIONS", "ECONOMIC"]
        dim_scores = {d: latest_scores.get(d, 0.0) for d in dimensions}
        overall = round(sum(dim_scores.values()) / len(dimensions), 2)

        # Trend is STABLE until we have historical data to compare
        trend = "STABLE"

        if overall >= 70 and health == "CERTIFIED":
            recommendation = "READY"
        elif overall >= 50:
            recommendation = "CAUTION"
        else:
            recommendation = "NOT_READY"

        return {
            "overall_readiness_pct": overall,
            "dimension_scores": dim_scores,
            "certifications_status": cert_summary,
            "trend": trend,
            "production_recommendation": recommendation,
        }

    def one_liner(self) -> str:
        r = self.readiness_report()
        return (
            f"Readiness v2 | Overall={r['overall_readiness_pct']}% | "
            f"Trend={r['trend']} | "
            f"Recommendation={r['production_recommendation']}"
        )


continuous_readiness_engine = ContinuousReadinessEngine()

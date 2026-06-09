"""
Compliance dashboard — surfaces aggregate compliance health across all dimensions.
"""
import threading
from datetime import datetime


class ComplianceDashboard:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def dashboard(self) -> dict:
        from core.readiness_v2.certification_monitor import certification_monitor
        from core.readiness_v2.readiness_trend_tracker import readiness_trend_tracker

        cert_summary = certification_monitor.certification_summary()
        latest_scores = readiness_trend_tracker.latest_scores()

        avg_score = (
            sum(latest_scores.values()) / len(latest_scores)
            if latest_scores
            else 0.0
        )

        dimensions = {
            "ARCHITECTURE": latest_scores.get("ARCHITECTURE", 0.0),
            "GOVERNANCE": latest_scores.get("GOVERNANCE", 0.0),
            "VALIDATION": latest_scores.get("VALIDATION", 0.0),
            "OPERATIONS": latest_scores.get("OPERATIONS", 0.0),
            "ECONOMIC": latest_scores.get("ECONOMIC", 0.0),
        }

        return {
            "certifications_active": cert_summary["certified"],
            "certifications_lapsed": cert_summary["lapsed"],
            "avg_readiness_score": round(avg_score, 2),
            "compliance_dimensions": dimensions,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def compliance_health(self) -> str:
        d = self.dashboard()
        if d["certifications_lapsed"] == 0 and d["avg_readiness_score"] >= 70:
            return "CERTIFIED"
        elif d["certifications_lapsed"] <= 2:
            return "PARTIAL"
        return "LAPSED"


compliance_dashboard = ComplianceDashboard()

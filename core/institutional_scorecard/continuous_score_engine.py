"""Continuous score engine — institutional health composite score."""
import threading
from datetime import datetime


def _score_label(score: float) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 60:
        return "ADEQUATE"
    if score >= 45:
        return "NEEDS_ATTENTION"
    return "CRITICAL"


class ContinuousScoreEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def score(self) -> dict:
        from core.institutional_scorecard.institutional_kpi_tracker import institutional_kpi_tracker
        from core.institutional_scorecard.trend_analyzer import trend_analyzer
        from core.institutional_scorecard.degradation_detector import degradation_detector

        kpi_dash = institutional_kpi_tracker.kpi_dashboard()
        kpi_health = kpi_dash.get("overall_kpi_health_pct", 50.0)
        trends = trend_analyzer.all_trends()
        improving = sum(1 for t in trends if t.get("trend") == "IMPROVING")
        total_trends = max(1, len(trends))
        trend_health = (improving / total_trends) * 100

        deg_scan = degradation_detector.scan()
        active_degradations = deg_scan.get("alerts_found", 0)

        maturity_score = 50.0
        maturity_level = "UNKNOWN"
        try:
            from core.maturity_scorecard.maturity_engine import maturity_engine
            result = maturity_engine.assess()
            maturity_score = result.get("maturity_score", result.get("overall_score", 50.0))
            maturity_level = result.get("maturity_level", result.get("level", "UNKNOWN"))
        except Exception:
            pass

        composite = (maturity_score * 0.4 + kpi_health * 0.4 + trend_health * 0.2)

        return {
            "continuous_score": round(composite, 2),
            "maturity_level": maturity_level,
            "kpi_health": kpi_health,
            "trend_health": round(trend_health, 2),
            "active_degradations": active_degradations,
            "score_label": _score_label(composite),
            "generated_at": datetime.utcnow().isoformat(),
        }


continuous_score_engine = ContinuousScoreEngine()

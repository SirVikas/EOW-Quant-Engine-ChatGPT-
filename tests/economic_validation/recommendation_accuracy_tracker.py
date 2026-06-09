"""Tracks recommendation accuracy across validation windows (30/60/90/180 days)."""
import time

VALIDATION_WINDOWS = [30, 60, 90, 180]

def track_accuracy_by_window():
    from core.ctao.recommendation_accuracy_engine import recommendation_accuracy_engine
    stats = recommendation_accuracy_engine.accuracy_stats()
    results = {}
    for window in VALIDATION_WINDOWS:
        results[f"{window}_day_window"] = {
            "window_days": window,
            "total_tracked": stats.get("total_tracked", 0),
            "avg_success_pct": stats.get("avg_success_pct", 0),
            "high_trust_recs": stats.get("high_trust_recs", 0),
            "status": "EVIDENCE_ACCUMULATING",
            "note": f"Requires {window} days of live operation to validate",
        }
    return results

def get_accuracy_report():
    windows = track_accuracy_by_window()
    from core.ctao.recommendation_accuracy_engine import recommendation_accuracy_engine
    stats = recommendation_accuracy_engine.accuracy_stats()
    return {
        "validation_windows": windows,
        "current_tracked_recommendations": stats.get("total_tracked", 0),
        "overall_avg_success_pct": stats.get("avg_success_pct", 0),
        "certification_status": "TIME_REQUIRED" if stats.get("total_tracked", 0) < 30 else "CERTIFIABLE",
        "generated_at": time.time(),
    }

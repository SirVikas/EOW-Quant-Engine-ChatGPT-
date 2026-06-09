"""Optimization Recommender — master resource economics engine."""
import threading
from typing import List


class OptimizationRecommender:
    def __init__(self):
        self._lock = threading.RLock()

    def recommend(self) -> List[dict]:
        from core.resource_economics.resource_efficiency_analyzer import resource_efficiency_analyzer
        with self._lock:
            scores = resource_efficiency_analyzer.all_efficiency_scores()
            recommendations = []
            for s in scores:
                if s["efficiency_score"] < 70:
                    savings = round((70 - s["efficiency_score"]) * 0.5, 1)
                    recommendations.append({
                        "resource_type": s["resource_type"],
                        "recommendation": s["recommendation"],
                        "expected_savings_pct": savings,
                    })
            return recommendations

    def economics_report(self) -> dict:
        from core.resource_economics.resource_cost_engine import resource_cost_engine
        from core.resource_economics.resource_roi_tracker import resource_roi_tracker
        with self._lock:
            total_spend = resource_cost_engine.total_spend()
            roi_by_type = resource_roi_tracker.roi_by_type()
            avg_roi = (sum(roi_by_type.values()) / len(roi_by_type)) if roi_by_type else 0.0
            return {
                "total_spend": round(total_spend, 2),
                "avg_roi": round(avg_roi, 2),
                "top_optimizations": self.recommend(),
            }


optimization_recommender = OptimizationRecommender()

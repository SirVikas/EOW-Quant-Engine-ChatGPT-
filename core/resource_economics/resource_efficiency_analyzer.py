"""Resource Efficiency Analyzer — analyzes resource efficiency."""
import threading
from typing import List


class ResourceEfficiencyAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()

    def analyze(self, resource_type: str) -> dict:
        from core.resource_economics.resource_cost_engine import resource_cost_engine
        from core.resource_economics.resource_roi_tracker import resource_roi_tracker
        with self._lock:
            cost_by_type = resource_cost_engine.cost_by_type()
            roi_by_type = resource_roi_tracker.roi_by_type()
            cost = cost_by_type.get(resource_type, 0.0)
            roi = roi_by_type.get(resource_type, 0.0)
            # Efficiency score: higher ROI relative to cost = higher score
            efficiency_score = min(100.0, max(0.0, 50.0 + roi * 0.5)) if roi != 0 else 50.0
            recommendation = (
                "OPTIMIZE" if efficiency_score < 40
                else "MONITOR" if efficiency_score < 70
                else "MAINTAIN"
            )
            return {
                "resource_type": resource_type,
                "usage_trend": "STABLE",
                "efficiency_score": round(efficiency_score, 2),
                "recommendation": recommendation,
                "total_cost": cost,
                "avg_roi_pct": roi,
            }

    def all_efficiency_scores(self) -> List[dict]:
        from core.resource_economics.resource_cost_engine import resource_cost_engine
        with self._lock:
            types = list(resource_cost_engine.cost_by_type().keys()) or ["COMPUTE", "STORAGE", "API", "INTELLIGENCE"]
            return [self.analyze(t) for t in types]


resource_efficiency_analyzer = ResourceEfficiencyAnalyzer()

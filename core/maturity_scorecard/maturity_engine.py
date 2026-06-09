"""Institutional Maturity Scorecard — Maturity Engine."""
import threading, time

MATURITY_LEVELS = {
    (0, 40): "INITIAL",
    (40, 60): "DEVELOPING",
    (60, 75): "DEFINED",
    (75, 88): "MANAGED",
    (88, 95): "OPTIMIZING",
    (95, 101): "INSTITUTIONALIZED",
}


class MaturityEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def assess(self) -> dict:
        from core.maturity_scorecard.readiness_calculator import readiness_calculator, SCORECARD_DIMENSIONS
        with self._lock:
            dimension_scores = readiness_calculator.auto_calculate()
            total_score = readiness_calculator.calculate_score(dimension_scores)
            level = self.maturity_level(total_score)
            gaps = self.gap_analysis(dimension_scores)
        return {
            "total_score": total_score,
            "maturity_level": level,
            "dimension_scores": dimension_scores,
            "gap_analysis": gaps,
            "dimensions": SCORECARD_DIMENSIONS,
            "generated_at": time.time(),
        }

    def maturity_level(self, score: float) -> str:
        for (low, high), level in MATURITY_LEVELS.items():
            if low <= score < high:
                return level
        return "INITIAL"

    def gap_analysis(self, scores: dict) -> list:
        recommendations = []
        for dim, score in scores.items():
            if score < 75:
                recommendations.append({
                    "dimension": dim,
                    "current_score": score,
                    "target_score": 75,
                    "gap": 75 - score,
                    "recommendation": f"Improve {dim} coverage to reach MANAGED level",
                })
        return recommendations


maturity_engine = MaturityEngine()

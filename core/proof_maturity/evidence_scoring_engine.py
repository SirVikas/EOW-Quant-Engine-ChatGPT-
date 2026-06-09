"""
Evidence scoring engine — raw 0–100 maturity scores for the four proof
dimensions, derived from sibling layers (each source optional, defaults 0).
"""
import threading


class EvidenceScoringEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def validation_maturity(self) -> float:
        try:
            from core.maturity_scorecard.maturity_engine import maturity_engine
            return float(maturity_engine.assess().get("total_score", 0.0))
        except Exception:
            return 0.0

    def runtime_maturity(self) -> float:
        try:
            from core.readiness_v2.continuous_readiness_engine import continuous_readiness_engine
            return float(
                continuous_readiness_engine.readiness_report().get("overall_readiness_pct", 0.0))
        except Exception:
            return 0.0

    def evidence_maturity(self) -> float:
        try:
            from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
            return float(
                evidence_warehouse.warehouse_report().get("warehouse_health_score", 0.0))
        except Exception:
            return 0.0

    def certification_maturity(self) -> float:
        try:
            from core.readiness_v2.certification_monitor import certification_monitor
            summary = certification_monitor.certification_summary()
            total = summary.get("total", 0)
            if not total:
                return 0.0
            return round(100.0 * summary.get("certified", 0) / total, 2)
        except Exception:
            return 0.0

    def dimension_scores(self) -> dict:
        with self._lock:
            return {
                "VALIDATION": round(self.validation_maturity(), 2),
                "RUNTIME": round(self.runtime_maturity(), 2),
                "EVIDENCE": round(self.evidence_maturity(), 2),
                "CERTIFICATION": round(self.certification_maturity(), 2),
            }


evidence_scoring_engine = EvidenceScoringEngine()

"""
Proof Maturity Index (PMI) — single confidence-weighted maturity score over
Validation, Runtime, Evidence, and Certification maturity dimensions.
"""
import threading
import time

PROOF_LEVELS = {
    (0, 40): "FOUNDATIONAL",
    (40, 60): "DEVELOPING",
    (60, 75): "ESTABLISHED",
    (75, 90): "PROVEN",
    (90, 101): "INSTITUTIONAL",
}


class ProofMaturityEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def proof_level(self, score: float) -> str:
        for (low, high), level in PROOF_LEVELS.items():
            if low <= score < high:
                return level
        return "FOUNDATIONAL"

    def proof_maturity_report(self) -> dict:
        from core.proof_maturity.evidence_scoring_engine import evidence_scoring_engine
        from core.proof_maturity.confidence_weighting import confidence_weighting
        with self._lock:
            scores = evidence_scoring_engine.dimension_scores()
            pmi = confidence_weighting.weighted_score(scores)
            report = {
                "proof_maturity_index": pmi,
                "proof_level": self.proof_level(pmi),
                "dimension_scores": scores,
                "weights": confidence_weighting.weights(),
                "generated_at": time.time(),
            }
        try:
            from core.proof_maturity.maturity_dashboard import maturity_dashboard
            maturity_dashboard.record(report)
        except Exception:
            pass
        return report

    def one_liner(self) -> str:
        r = self.proof_maturity_report()
        return (
            f"Proof Maturity | PMI={r['proof_maturity_index']} | "
            f"Level={r['proof_level']}"
        )


proof_maturity_engine = ProofMaturityEngine()

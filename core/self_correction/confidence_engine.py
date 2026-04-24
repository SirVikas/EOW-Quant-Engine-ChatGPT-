"""
FTD-029 Part 2 — Confidence Engine

Composite confidence (locked formula, Q3):
  confidence = 0.4 * MetaScore + 0.3 * DecisionScore + 0.2 * StabilityScore + 0.1 * ConsistencyScore

Output: confidence ∈ [0, 100], allowed_delta_pct
"""
from __future__ import annotations
from typing import Any, Dict


# Weights (locked — do not change without FTD amendment)
W_META_SCORE      = 0.40
W_DECISION_SCORE  = 0.30
W_STABILITY_SCORE = 0.20
W_CONSISTENCY     = 0.10


def _allowed_delta(confidence: float) -> float:
    """Q3: dynamic change limit based on confidence."""
    if confidence >= 80:
        return 0.15
    if confidence >= 60:
        return 0.10
    return 0.05


class ConfidenceEngine:
    """
    Computes composite confidence from FTD-028 sub-scores.
    """

    MODULE = "CONFIDENCE_ENGINE"
    PHASE  = "029"

    def compute(
        self,
        meta_score: float        = 0.0,
        decision_score: float    = 0.0,   # DecisionScorer avg score (−1..1) → mapped to 0–100
        stability_score: float   = 0.0,   # FTD-028 stability_score (0–100)
        consistency_score: float = 0.0,   # FTD-028 or SystemConsistency (0–100)
    ) -> Dict[str, Any]:
        # Normalise decision_score from [−1, 1] → [0, 100]
        ds_normalised = max(0.0, min(100.0, (decision_score + 1.0) * 50.0))

        raw = (
            W_META_SCORE      * float(meta_score)
            + W_DECISION_SCORE  * ds_normalised
            + W_STABILITY_SCORE * float(stability_score)
            + W_CONSISTENCY     * float(consistency_score)
        )

        confidence    = round(max(0.0, min(100.0, raw)), 2)
        allowed_delta = _allowed_delta(confidence)

        return {
            "module":           self.MODULE,
            "phase":            self.PHASE,
            "confidence":       confidence,
            "allowed_delta_pct": allowed_delta,
            "components": {
                "meta_score":       round(float(meta_score), 2),
                "decision_score_raw": round(float(decision_score), 4),
                "decision_score_norm": round(ds_normalised, 2),
                "stability_score":  round(float(stability_score), 2),
                "consistency_score": round(float(consistency_score), 2),
            },
            "weights": {
                "meta":        W_META_SCORE,
                "decision":    W_DECISION_SCORE,
                "stability":   W_STABILITY_SCORE,
                "consistency": W_CONSISTENCY,
            },
        }

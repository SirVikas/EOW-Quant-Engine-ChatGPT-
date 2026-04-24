"""
FTD-028 Part 13 — Meta Score Engine

Aggregates all validator results into a unified system intelligence score.

Outputs:
  - System Intelligence Score (0–100)
  - Risk Score (0–100)
  - Stability Score (0–100)
  - Confidence Score (0–100)
  - Final Verdict: PASS | FAIL
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


PASS_THRESHOLD = 70   # overall score must be ≥ 70 to PASS

_WEIGHTS: Dict[str, float] = {
    "contradiction":     0.20,   # logical integrity is highest weight
    "data_integrity":    0.10,
    "decision_quality":  0.15,
    "risk":              0.15,
    "tuning":            0.05,
    "evolution":         0.05,
    "capital":           0.10,
    "audit":             0.05,
    "alert":             0.05,
    "performance":       0.10,
    "failure_resilience": 0.00,   # bonus category, not penalised if no data
    "consistency":       0.00,   # informational only
}


class MetaScoreEngine:
    """
    Aggregates all validator results into composite system score.
    """

    MODULE = "META_SCORE_ENGINE"
    PHASE  = "028"

    def run(self, validator_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        validator_results: dict of validator_name → result dict (each has `passed: bool`)
        """
        component_scores: Dict[str, float] = {}

        for key, weight in _WEIGHTS.items():
            result = validator_results.get(key, {})
            if not result:
                component_scores[key] = 100.0   # missing validator → assume OK
                continue
            passed = result.get("passed", True)
            # Partial credit based on issue count where available
            issue_count = result.get("issue_count", 0) or 0
            if passed:
                component_scores[key] = 100.0
            else:
                penalty = min(issue_count * 15, 80)   # each issue -15pts, max -80pts
                component_scores[key] = max(0.0, 100.0 - penalty)

        # Weighted overall score
        total_weight = sum(_WEIGHTS.values())
        if total_weight > 0:
            overall = sum(
                component_scores[k] * _WEIGHTS[k]
                for k in _WEIGHTS
                if k in component_scores
            ) / total_weight
        else:
            overall = 100.0

        # Risk score: driven by risk + capital + contradiction
        risk_score = (
            component_scores.get("risk", 100.0) * 0.40
            + component_scores.get("capital", 100.0) * 0.30
            + component_scores.get("contradiction", 100.0) * 0.30
        )

        # Stability score: driven by consistency + data + failure resilience
        stability_score = (
            component_scores.get("consistency", 100.0) * 0.30
            + component_scores.get("data_integrity", 100.0) * 0.40
            + component_scores.get("failure_resilience", 100.0) * 0.30
        )

        # Confidence score: driven by decision quality + performance + audit
        confidence_score = (
            component_scores.get("decision_quality", 100.0) * 0.40
            + component_scores.get("performance", 100.0) * 0.40
            + component_scores.get("audit", 100.0) * 0.20
        )

        overall_rounded      = round(overall, 1)
        risk_rounded         = round(risk_score, 1)
        stability_rounded    = round(stability_score, 1)
        confidence_rounded   = round(confidence_score, 1)

        verdict = "PASS" if overall_rounded >= PASS_THRESHOLD else "FAIL"

        # Collect all critical errors
        critical_errors: List[str] = []
        for key, result in validator_results.items():
            if not result.get("passed", True):
                for err in result.get("errors", result.get("issues", result.get("contradictions", []))):
                    msg = err.get("message", str(err))
                    critical_errors.append(f"[{key.upper()}] {msg}")

        return {
            "module":             self.MODULE,
            "phase":              self.PHASE,
            "system_score":       overall_rounded,
            "risk_score":         risk_rounded,
            "stability_score":    stability_rounded,
            "confidence_score":   confidence_rounded,
            "component_scores":   {k: round(v, 1) for k, v in component_scores.items()},
            "verdict":            verdict,
            "pass_threshold":     PASS_THRESHOLD,
            "critical_errors":    critical_errors,
            "critical_error_count": len(critical_errors),
            "snapshot_ts":        int(time.time() * 1000),
        }

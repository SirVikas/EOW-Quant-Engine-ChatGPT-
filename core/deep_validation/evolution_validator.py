"""
FTD-028 Part 6 — Evolution Validator

Validates:
  - Mutation effectiveness (champion vs challenger)
  - Overfitting detection (in-sample vs out-of-sample divergence)
  - Champion vs challenger comparison correctness
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


OVERFIT_DIVERGENCE_THRESHOLD = 0.25   # >25% in-sample/out-of-sample gap → overfitting
MIN_CHAMPION_SCORE           = 0.0    # champion must beat neutral baseline


class EvolutionValidator:
    """
    Validates evolution/mutation cycles for correctness.
    """

    MODULE = "EVOLUTION_VALIDATOR"
    PHASE  = "028"

    def run(self, evolution_state: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        generation      = evolution_state.get("generation", 0) or 0
        champion_score  = evolution_state.get("champion_score", 0.0) or 0.0
        challenger_score = evolution_state.get("challenger_score", None)
        in_sample_score = evolution_state.get("in_sample_score", None)
        out_sample_score = evolution_state.get("out_sample_score", None)
        strategies      = evolution_state.get("strategies", [])

        # Champion quality
        if generation > 0 and champion_score < MIN_CHAMPION_SCORE:
            issues.append(self._mk("CHAMPION_BELOW_BASELINE",
                f"champion_score={champion_score:.4f} is below baseline {MIN_CHAMPION_SCORE}"))

        # Champion vs challenger correctness
        if challenger_score is not None and challenger_score > champion_score:
            issues.append(self._mk("CHALLENGER_BEATS_CHAMPION",
                f"challenger ({challenger_score:.4f}) outperforms champion ({champion_score:.4f}) — champion should be promoted"))

        # Overfitting detection
        if in_sample_score is not None and out_sample_score is not None and in_sample_score > 0:
            divergence = abs(in_sample_score - out_sample_score) / abs(in_sample_score)
            if divergence > OVERFIT_DIVERGENCE_THRESHOLD:
                issues.append(self._mk("OVERFITTING_DETECTED",
                    f"in-sample={in_sample_score:.4f} vs out-of-sample={out_sample_score:.4f}; "
                    f"divergence={divergence:.2%} exceeds {OVERFIT_DIVERGENCE_THRESHOLD:.0%}"))

        # No strategies in evolved system
        if generation > 0 and not strategies:
            issues.append(self._mk("NO_ACTIVE_STRATEGIES",
                f"generation={generation} but no active strategies found"))

        passed = len(issues) == 0
        return {
            "module":        self.MODULE,
            "phase":         self.PHASE,
            "generation":    generation,
            "issues":        issues,
            "issue_count":   len(issues),
            "passed":        passed,
            "verdict":       "PASS" if passed else "FAIL",
            "snapshot_ts":   int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

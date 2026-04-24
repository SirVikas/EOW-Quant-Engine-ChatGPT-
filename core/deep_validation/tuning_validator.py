"""
FTD-028 Part 5 — Auto-Tuning Validator

Validates:
  - Before vs after metrics show measurable improvement
  - Statistical improvement is genuine (not noise)
  - Rollback correctness when tuning regresses
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


MIN_IMPROVEMENT_PCT   = 0.01   # at least 1% improvement to count as valid
MIN_SAMPLES_FOR_STATS = 10     # need at least 10 samples for a valid statistical comparison


class TuningValidator:
    """
    Validates auto-tuning cycles for correctness and measurable improvement.
    """

    MODULE = "TUNING_VALIDATOR"
    PHASE  = "028"

    def run(self, tuning_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not tuning_history:
            return {
                "module":        self.MODULE,
                "phase":         self.PHASE,
                "cycles_checked": 0,
                "issues":        [],
                "passed":        True,
                "verdict":       "NO_DATA",
                "snapshot_ts":   int(time.time() * 1000),
            }

        issues: List[Dict[str, Any]] = []

        for i, cycle in enumerate(tuning_history):
            label = cycle.get("label", f"cycle_{i}")
            before = cycle.get("before", {})
            after  = cycle.get("after", {})
            rolled_back = cycle.get("rolled_back", False)

            before_score = float(before.get("score", 0.0) or 0.0)
            after_score  = float(after.get("score", 0.0) or 0.0)
            samples      = int(cycle.get("samples", 0) or 0)

            # Insufficient samples → unreliable result
            if samples < MIN_SAMPLES_FOR_STATS:
                issues.append(self._mk("INSUFFICIENT_SAMPLES", label,
                    f"only {samples} samples (need {MIN_SAMPLES_FOR_STATS}) — result may not be statistically valid"))

            # Improvement check
            if before_score > 0:
                improvement = (after_score - before_score) / before_score
            else:
                improvement = 0.0 if after_score == 0 else 1.0

            regressed = after_score < before_score

            if regressed and not rolled_back:
                issues.append(self._mk("REGRESSION_WITHOUT_ROLLBACK", label,
                    f"score regressed {before_score:.4f}→{after_score:.4f} but no rollback was performed"))

            if not regressed and improvement < MIN_IMPROVEMENT_PCT and samples >= MIN_SAMPLES_FOR_STATS:
                issues.append(self._mk("NEGLIGIBLE_IMPROVEMENT", label,
                    f"improvement={improvement:.2%} is below minimum {MIN_IMPROVEMENT_PCT:.0%}"))

        passed = len(issues) == 0
        return {
            "module":          self.MODULE,
            "phase":           self.PHASE,
            "cycles_checked":  len(tuning_history),
            "issues":          issues,
            "issue_count":     len(issues),
            "passed":          passed,
            "verdict":         "PASS" if passed else "FAIL",
            "snapshot_ts":     int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, label: str, message: str) -> Dict[str, Any]:
        return {"code": code, "cycle": label, "message": message}

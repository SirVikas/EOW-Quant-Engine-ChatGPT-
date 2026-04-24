"""
FTD-029 Part 5 — Change Planner

Converts Issues into concrete, bounded change plans.
Each plan specifies: target_module, parameter, current → proposed, delta%, rationale, expected_impact.
Delta is enforced against allowed_delta_pct from ConfidenceEngine.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.self_correction.issue_extractor import Issue, IssueType
from core.self_correction.correction_proposal import TUNABLE_PARAMS, HARD_LIMITS


# Maps IssueType → list of (param, adjustment_direction, magnitude_hint)
# direction: +1 = increase, -1 = decrease
_ISSUE_TO_PARAMS: Dict[IssueType, List[tuple]] = {
    IssueType.CONTRADICTION:    [],   # No direct param fix; needs manual resolution
    IssueType.DATA_INTEGRITY:   [],   # Pipeline issue; no parameter fix available
    IssueType.DECISION_QUALITY: [("TR_EV_WEIGHT", +1, 0.08), ("P7B_PERF_WIN_THRESHOLD", +1, 0.05)],
    IssueType.RISK_VIOLATION:   [("KELLY_FRACTION", -1, 0.10)],
    IssueType.CAPITAL_MISMATCH: [("KELLY_FRACTION", -1, 0.08), ("EXPLORE_EV_FLOOR", +1, 0.05)],
    IssueType.PERFORMANCE_DRIFT:[("TR_EV_WEIGHT", +1, 0.06), ("P7B_EV_HIGH_THRESHOLD", -1, 0.05)],
    IssueType.EVOLUTION_OVERFIT:[("ADAPTIVE_LR", -1, 0.08)],
    IssueType.TUNING_REGRESSION:[("ADAPTIVE_LR", -1, 0.10)],
    IssueType.ALERT_QUALITY:    [],   # Alert config not in tunable params
    IssueType.CONSISTENCY_DRIFT:[("ADAPTIVE_LR", +1, 0.05)],
}


@dataclass
class ChangePlan:
    plan_id:         str
    issue_type:      str
    target_module:   str
    parameter:       str
    current_value:   float
    proposed_value:  float
    delta_pct:       float
    rationale:       str
    expected_impact: str
    auto_eligible:   bool   # True if delta_pct ≤ 5%
    priority_rank:   int


class ChangePlanner:
    """
    Generates bounded change plans from prioritised issues.
    Rejects plans that exceed allowed_delta or target HARD_LIMITS.
    """

    MODULE = "CHANGE_PLANNER"
    PHASE  = "029"

    def plan(
        self,
        issues: List[Issue],
        current_params: Dict[str, float],
        allowed_delta_pct: float,
    ) -> List[ChangePlan]:
        plans: List[ChangePlan] = []
        seen_params: set = set()

        for rank, issue in enumerate(issues):
            param_list = _ISSUE_TO_PARAMS.get(issue.issue_type, [])
            for param, direction, magnitude_hint in param_list:
                if param in seen_params:
                    continue
                if param in HARD_LIMITS:
                    continue
                if param not in TUNABLE_PARAMS:
                    continue

                bounds = TUNABLE_PARAMS[param]
                lo, hi, description = bounds

                current = current_params.get(param)
                if current is None:
                    continue

                # Compute bounded delta
                raw_delta = min(allowed_delta_pct, magnitude_hint) * current
                proposed  = current + direction * raw_delta
                proposed  = max(lo, min(hi, proposed))

                if math.isclose(proposed, current, rel_tol=1e-6):
                    continue

                actual_delta_pct = abs(proposed - current) / abs(current) if current else 0.0

                # Block if delta exceeds 15% (Q2 hard cap)
                if actual_delta_pct > 0.15 + 1e-9:
                    continue

                plans.append(ChangePlan(
                    plan_id=f"{issue.issue_type.value}_{param}_{int(time.time())}",
                    issue_type=issue.issue_type.value,
                    target_module=issue.affected_module,
                    parameter=param,
                    current_value=round(current, 6),
                    proposed_value=round(proposed, 6),
                    delta_pct=round(actual_delta_pct, 4),
                    rationale=f"[{issue.issue_type.value}] {issue.suggested_fix}",
                    expected_impact=description,
                    auto_eligible=actual_delta_pct <= 0.05,
                    priority_rank=rank,
                ))
                seen_params.add(param)

        return plans

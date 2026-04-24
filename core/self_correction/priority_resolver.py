"""
FTD-029 Part 4a — Priority Resolver

Sorts issues by locked priority order (Q1 / Part 4):
  1. Risk safety
  2. Signal pipeline correctness
  3. Strategy parameters
  4. Portfolio allocation
  5. Capital scaling
"""
from __future__ import annotations
from typing import List

from core.self_correction.issue_extractor import Issue, IssueType, IssueSeverity


# Locked priority order — lower index = higher priority
_PRIORITY_ORDER: List[IssueType] = [
    IssueType.RISK_VIOLATION,       # 1. Risk safety
    IssueType.CONTRADICTION,        # 1. Risk safety (logic)
    IssueType.DATA_INTEGRITY,       # 2. Signal pipeline correctness
    IssueType.DECISION_QUALITY,     # 2. Signal pipeline
    IssueType.EVOLUTION_OVERFIT,    # 3. Strategy parameters
    IssueType.TUNING_REGRESSION,    # 3. Strategy parameters
    IssueType.PERFORMANCE_DRIFT,    # 3. Strategy parameters
    IssueType.CAPITAL_MISMATCH,     # 4. Portfolio allocation
    IssueType.ALERT_QUALITY,        # 5. Capital scaling / auxiliary
    IssueType.CONSISTENCY_DRIFT,    # 5. Auxiliary
]

_SEVERITY_ORDER = {
    IssueSeverity.CRITICAL: 0,
    IssueSeverity.HIGH:     1,
    IssueSeverity.MEDIUM:   2,
    IssueSeverity.LOW:      3,
}


def _priority_index(issue: Issue) -> tuple:
    """Lower tuple → higher priority."""
    try:
        type_rank = _PRIORITY_ORDER.index(issue.issue_type)
    except ValueError:
        type_rank = len(_PRIORITY_ORDER)
    sev_rank = _SEVERITY_ORDER.get(issue.severity, 99)
    return (type_rank, sev_rank)


class PriorityResolver:
    """
    Returns issues sorted by locked priority (risk-safety first).
    """

    MODULE = "PRIORITY_RESOLVER"
    PHASE  = "029"

    def sort(self, issues: List[Issue]) -> List[Issue]:
        return sorted(issues, key=_priority_index)

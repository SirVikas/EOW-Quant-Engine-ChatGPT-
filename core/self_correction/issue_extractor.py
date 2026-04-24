"""
FTD-029 Part 1 — Issue Extractor

Parses FTD-027 and FTD-028 outputs into structured, actionable issues.
Input:  raw validator results dicts
Output: list of Issue objects with type, severity, affected module, suggested fix
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"


class IssueType(str, Enum):
    CONTRADICTION      = "CONTRADICTION"
    DATA_INTEGRITY     = "DATA_INTEGRITY"
    DECISION_QUALITY   = "DECISION_QUALITY"
    RISK_VIOLATION     = "RISK_VIOLATION"
    CAPITAL_MISMATCH   = "CAPITAL_MISMATCH"
    PERFORMANCE_DRIFT  = "PERFORMANCE_DRIFT"
    EVOLUTION_OVERFIT  = "EVOLUTION_OVERFIT"
    TUNING_REGRESSION  = "TUNING_REGRESSION"
    ALERT_QUALITY      = "ALERT_QUALITY"
    CONSISTENCY_DRIFT  = "CONSISTENCY_DRIFT"


# Maps validator result key → (IssueType, severity, affected_module, suggested_fix)
_VALIDATOR_MAP: Dict[str, tuple] = {
    "contradiction":   (IssueType.CONTRADICTION,    IssueSeverity.CRITICAL, "logic_layer",          "Remove contradictory state; check trade/signal sync"),
    "data_integrity":  (IssueType.DATA_INTEGRITY,   IssueSeverity.HIGH,     "pipeline",             "Validate missing fields; check data source"),
    "decision_quality":(IssueType.DECISION_QUALITY, IssueSeverity.HIGH,     "decision_scorer",      "Increase EV weight; improve signal quality"),
    "risk":            (IssueType.RISK_VIOLATION,   IssueSeverity.CRITICAL, "risk_engine",          "Reduce exposure; check kill switch"),
    "capital":         (IssueType.CAPITAL_MISMATCH, IssueSeverity.HIGH,     "capital_allocator",    "Reduce Kelly fraction; check drawdown scaling"),
    "performance":     (IssueType.PERFORMANCE_DRIFT,IssueSeverity.MEDIUM,   "performance_validator","Tune EV threshold; review strategy selection"),
    "evolution":       (IssueType.EVOLUTION_OVERFIT,IssueSeverity.MEDIUM,   "evolution_engine",     "Reduce mutation rate; increase out-of-sample testing"),
    "tuning":          (IssueType.TUNING_REGRESSION,IssueSeverity.MEDIUM,   "tuning_validator",     "Rollback last parameter change"),
    "alert":           (IssueType.ALERT_QUALITY,    IssueSeverity.LOW,      "alert_engine",         "Tune alert thresholds; review dedup window"),
    "consistency":     (IssueType.CONSISTENCY_DRIFT,IssueSeverity.LOW,      "system_consistency",   "Re-synchronise module states"),
}


@dataclass
class Issue:
    issue_type:      IssueType
    severity:        IssueSeverity
    affected_module: str
    suggested_fix:   str
    source_validator: str
    raw_errors:      List[str]
    issue_count:     int


class IssueExtractor:
    """
    Converts FTD-027 + FTD-028 validator results into a flat list of Issues.
    Only generates Issues for validators that failed (passed=False).
    """

    MODULE = "ISSUE_EXTRACTOR"
    PHASE  = "029"

    def extract(
        self,
        ftd028_validators: Dict[str, Dict[str, Any]],
        ftd027_result: Optional[Dict[str, Any]] = None,
    ) -> List[Issue]:
        issues: List[Issue] = []

        # FTD-028 validators
        for key, mapping in _VALIDATOR_MAP.items():
            result = ftd028_validators.get(key, {})
            if not result or result.get("passed", True):
                continue

            issue_type, severity, module, fix = mapping
            raw_errors = self._collect_errors(result)
            issues.append(Issue(
                issue_type=issue_type,
                severity=severity,
                affected_module=module,
                suggested_fix=fix,
                source_validator=key,
                raw_errors=raw_errors,
                issue_count=result.get("issue_count", result.get("error_count",
                    result.get("contradiction_count", len(raw_errors)))),
            ))

        # FTD-027 scenario failures (optional)
        if ftd027_result:
            failed = ftd027_result.get("failed_scenarios", [])
            for scenario in failed:
                issues.append(Issue(
                    issue_type=IssueType.CONSISTENCY_DRIFT,
                    severity=IssueSeverity.HIGH,
                    affected_module=scenario.get("module", "unknown"),
                    suggested_fix=scenario.get("fix", "Review FTD-027 scenario logs"),
                    source_validator="ftd027",
                    raw_errors=[scenario.get("detail", str(scenario))],
                    issue_count=1,
                ))

        return issues

    @staticmethod
    def _collect_errors(result: Dict[str, Any]) -> List[str]:
        msgs: List[str] = []
        for key in ("errors", "issues", "contradictions"):
            for item in result.get(key, []):
                msgs.append(item.get("message", str(item)))
        return msgs or [result.get("verdict", "unknown failure")]

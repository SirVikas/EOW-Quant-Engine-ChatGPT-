"""
FTD-028 Part 2 — Data Integrity Checker

Validates pipeline stage consistency, missing data, and invalid values.
"""
from __future__ import annotations
import math
import time
from typing import Any, Dict, List, Optional


_REQUIRED_PIPELINE_FIELDS = [
    "equity",
    "current_drawdown_pct",
    "total_trades",
    "win_rate",
    "total_pnl",
]

_NUMERIC_BOUNDS: Dict[str, tuple] = {
    "equity":               (0.0, 1e9),
    "current_drawdown_pct": (0.0, 1.0),
    "win_rate":             (0.0, 1.0),
    "total_trades":         (0,   1_000_000),
}


class DataIntegrityChecker:
    """
    Validates pipeline data for completeness and value sanity.
    """

    MODULE = "DATA_INTEGRITY_CHECKER"
    PHASE  = "028"

    def run(self, state: Dict[str, Any], pipeline_stages: Optional[List[str]] = None) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        # Check required fields present
        for field in _REQUIRED_PIPELINE_FIELDS:
            if field not in state or state[field] is None:
                issues.append(self._mk("MISSING_FIELD", field, f"Required field '{field}' is missing or None"))

        # Numeric bounds check
        for field, (lo, hi) in _NUMERIC_BOUNDS.items():
            val = state.get(field)
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                issues.append(self._mk("INVALID_TYPE", field, f"'{field}' expected numeric, got {type(val).__name__}"))
                continue
            if math.isnan(val) or math.isinf(val):
                issues.append(self._mk("NAN_OR_INF", field, f"'{field}' is NaN or Inf"))
                continue
            if not (lo <= val <= hi):
                issues.append(self._mk("OUT_OF_BOUNDS", field,
                    f"'{field}'={val} is outside valid range [{lo}, {hi}]"))

        # Pipeline stage consistency
        stages = pipeline_stages or state.get("pipeline_stages", [])
        expected_stages = ["market_data", "signal", "risk", "execution"]
        missing_stages = [s for s in expected_stages if s not in stages]
        if missing_stages:
            issues.append(self._mk("MISSING_PIPELINE_STAGE", "pipeline",
                f"Missing pipeline stages: {missing_stages}"))

        passed = len(issues) == 0
        return {
            "module":      self.MODULE,
            "phase":       self.PHASE,
            "issues":      issues,
            "issue_count": len(issues),
            "passed":      passed,
            "snapshot_ts": int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, field: str, message: str) -> Dict[str, Any]:
        return {"code": code, "field": field, "message": message}

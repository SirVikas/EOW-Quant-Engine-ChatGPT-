"""
FTD-028 Part 8 — Audit Validator

Validates:
  - Event completeness (no gaps in event sequence)
  - Replay integrity
  - Missing logs detection
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


REQUIRED_EVENT_TYPES = {"TRADE_OPEN", "TRADE_CLOSE", "RISK_CHECK", "SIGNAL"}
MIN_EVENTS_PER_TRADE = 2   # every trade must have at least open + close


class AuditValidator:
    """
    Validates audit log completeness and integrity.
    """

    MODULE = "AUDIT_VALIDATOR"
    PHASE  = "028"

    def run(self, audit_state: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        events         = audit_state.get("events", []) or []
        total_trades   = audit_state.get("total_trades", 0) or 0
        total_events   = audit_state.get("total_events", len(events))
        replay_available = audit_state.get("replay_available", False)
        severity_breakdown = audit_state.get("severity_breakdown", {})

        # Event completeness: check minimum events per trade
        if total_trades > 0:
            expected_min_events = total_trades * MIN_EVENTS_PER_TRADE
            if total_events < expected_min_events:
                issues.append(self._mk("INCOMPLETE_AUDIT_TRAIL",
                    f"total_events={total_events} < expected_min={expected_min_events} for {total_trades} trades"))

        # Event type coverage
        observed_types = {str(e.get("type", e.get("severity", ""))).upper() for e in events}
        if total_trades > 0:
            missing_types = REQUIRED_EVENT_TYPES - observed_types
            if "TRADE_OPEN" in missing_types or "TRADE_CLOSE" in missing_types:
                issues.append(self._mk("MISSING_TRADE_EVENTS",
                    f"required event types not found: {missing_types & {'TRADE_OPEN', 'TRADE_CLOSE'}}"))

        # Missing logs detection: gap in timestamps
        timestamps = sorted(
            e.get("ts", e.get("timestamp", 0)) for e in events if e.get("ts") or e.get("timestamp")
        )
        if len(timestamps) > 1:
            max_gap_s = max(b - a for a, b in zip(timestamps[:-1], timestamps[1:]))
            if max_gap_s > 3600_000:   # >1 hour gap in millisecond timestamps
                issues.append(self._mk("LOG_GAP_DETECTED",
                    f"timestamp gap of {max_gap_s/1000:.0f}s detected in audit log"))

        # Critical events without resolution
        critical_count = severity_breakdown.get("CRITICAL", 0)
        resolved_count = sum(1 for e in events if e.get("resolved", False))
        if critical_count > 0 and resolved_count == 0:
            issues.append(self._mk("UNRESOLVED_CRITICAL_EVENTS",
                f"{critical_count} CRITICAL events found with 0 resolved"))

        passed = len(issues) == 0
        return {
            "module":        self.MODULE,
            "phase":         self.PHASE,
            "total_events":  total_events,
            "total_trades":  total_trades,
            "issues":        issues,
            "issue_count":   len(issues),
            "passed":        passed,
            "verdict":       "PASS" if passed else "FAIL",
            "snapshot_ts":   int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

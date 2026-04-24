"""
FTD-028 Part 9 — Alert Validator

Validates:
  - False alert rate (too many alerts without real events)
  - Missed alerts (real events without corresponding alert)
  - Priority correctness (severity ordering)
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


MAX_FALSE_ALERT_RATE  = 0.30   # >30% false alerts → alerting is broken
_SEVERITY_ORDER       = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


class AlertValidator:
    """
    Validates alert quality: false positives, missed alerts, priority correctness.
    """

    MODULE = "ALERT_VALIDATOR"
    PHASE  = "028"

    def run(self, alert_state: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        alerts        = alert_state.get("alerts", []) or []
        total_alerts  = len(alerts)
        false_alerts  = alert_state.get("false_alert_count", 0) or 0
        missed_alerts = alert_state.get("missed_alert_count", 0) or 0
        critical_events = alert_state.get("critical_events_detected", 0) or 0
        critical_alerts = sum(1 for a in alerts if str(a.get("severity", "")).upper() == "CRITICAL")

        # False alert rate
        if total_alerts > 0:
            false_rate = false_alerts / total_alerts
            if false_rate > MAX_FALSE_ALERT_RATE:
                issues.append(self._mk("HIGH_FALSE_ALERT_RATE",
                    f"false_alerts={false_alerts}/{total_alerts} ({false_rate:.0%}) exceeds max {MAX_FALSE_ALERT_RATE:.0%}"))

        # Missed critical alerts
        if missed_alerts > 0:
            issues.append(self._mk("MISSED_ALERTS",
                f"{missed_alerts} alerts were missed — real events without notification"))

        # Critical events must generate critical alerts
        if critical_events > 0 and critical_alerts == 0:
            issues.append(self._mk("CRITICAL_EVENTS_NOT_ALERTED",
                f"{critical_events} critical events detected but 0 CRITICAL alerts raised"))

        # Priority ordering — CRITICAL must come before HIGH
        severities = [str(a.get("severity", "INFO")).upper() for a in alerts]
        for i in range(1, len(severities)):
            prev_ord = _SEVERITY_ORDER.get(severities[i - 1], 99)
            curr_ord = _SEVERITY_ORDER.get(severities[i], 99)
            if curr_ord < prev_ord:
                issues.append(self._mk("PRIORITY_ORDER_VIOLATION",
                    f"alert at index {i} ({severities[i]}) has higher priority than preceding ({severities[i-1]})"))
                break   # one report is enough

        passed = len(issues) == 0
        return {
            "module":       self.MODULE,
            "phase":        self.PHASE,
            "total_alerts": total_alerts,
            "false_alerts": false_alerts,
            "missed_alerts": missed_alerts,
            "issues":       issues,
            "issue_count":  len(issues),
            "passed":       passed,
            "verdict":      "PASS" if passed else "FAIL",
            "snapshot_ts":  int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

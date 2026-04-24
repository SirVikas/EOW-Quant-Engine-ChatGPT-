"""
FTD-022 Audit Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.audit.audit_engine.AuditEngine
SOURCE: Delegates to core.error_registry (existing logic, no duplication)

Immutable event log, audit trail, event replay summary.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


class AuditEngine:
    """
    FTD-022: Wraps error_registry to expose structured audit log
    with event counts, severity breakdown, and replay summary.
    """

    PHASE  = "022"
    MODULE = "AUDIT_ENGINE"

    def get_log(self, limit: int = 100) -> Dict[str, Any]:
        """Return structured audit log from error_registry."""
        from core.error_registry import error_registry
        events = error_registry.recent(limit)

        severity_counts: Dict[str, int] = {}
        for e in events:
            sev = str(e.get("severity", "INFO"))
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "total_events":      len(events),
            "severity_breakdown": severity_counts,
            "events":            events,
            "replay_available":  False,   # full replay requires trade log + signals
            "module":            self.MODULE,
            "phase":             self.PHASE,
            "snapshot_ts":       int(time.time() * 1000),
        }

    def summary(self) -> Dict[str, Any]:
        try:
            log = self.get_log(limit=50)
            return {
                "total_events":       log["total_events"],
                "severity_breakdown": log["severity_breakdown"],
                "module":             self.MODULE,
                "phase":              self.PHASE,
            }
        except Exception as e:
            return {"module": self.MODULE, "phase": self.PHASE, "error": str(e)}


audit_engine = AuditEngine()

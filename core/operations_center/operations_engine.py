"""GAP-06: Operations Engine — master operations center aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class OperationsEngine:
    """Master operations center. Aggregates runtime, incidents, and scoreboard."""

    def ops_status(self) -> Dict[str, Any]:
        from core.operations_center.runtime_monitor import runtime_monitor
        from core.operations_center.incident_center import incident_center
        from core.operations_center.operations_scoreboard import operations_scoreboard

        runtime_summary = runtime_monitor.runtime_health_summary()
        incident_summary = incident_center.incident_stats()
        scoreboard_snapshot = operations_scoreboard.scoreboard()

        ops_score = scoreboard_snapshot.get("ops_health_score", 0)
        open_p1 = incident_summary.get("open_p1", 0)
        critical_count = runtime_summary.get("critical_count", 0)

        if open_p1 > 0 or critical_count > 0:
            readiness = "CRITICAL"
        elif ops_score < 60:
            readiness = "DEGRADED"
        else:
            readiness = "READY"

        return {
            "runtime_summary": runtime_summary,
            "incident_summary": incident_summary,
            "scoreboard_snapshot": scoreboard_snapshot,
            "operational_readiness": readiness,
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        status = self.ops_status()
        sb = status["scoreboard_snapshot"]
        return (
            f"Operations: score={sb['ops_health_score']} | "
            f"P1={sb['open_p1_incidents']} | "
            f"readiness={status['operational_readiness']}"
        )


operations_engine = OperationsEngine()

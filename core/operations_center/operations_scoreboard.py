"""GAP-06: Operations Scoreboard — operational scorecard."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class OperationsScoreboard:
    """Operational scorecard. Aggregates runtime and incident data."""

    def scoreboard(self) -> Dict[str, Any]:
        from core.operations_center.runtime_monitor import runtime_monitor
        from core.operations_center.incident_center import incident_center

        health = runtime_monitor.runtime_health_summary()
        stats = incident_center.incident_stats()

        healthy_pct = health.get("healthy_pct", 100.0)
        critical = health.get("critical_count", 0)
        degraded = health.get("degraded_count", 0)
        open_p1 = stats.get("open_p1", 0)
        open_p2 = stats.get("open_p2", 0)

        # Ops health score
        base = healthy_pct * 0.6
        penalty = open_p1 * 20 + open_p2 * 10 + critical * 15 + degraded * 5
        ops_score = max(0, min(100, int(base - penalty)))

        # Uptime pct: derived from healthy checks
        uptime_pct = healthy_pct

        return {
            "uptime_pct": uptime_pct,
            "open_p1_incidents": open_p1,
            "open_p2_incidents": open_p2,
            "degraded_components_count": degraded,
            "ops_health_score": ops_score,
            "ts": int(time.time() * 1000),
        }

    def trend_report(self) -> Dict[str, Any]:
        from core.operations_center.runtime_monitor import runtime_monitor
        health = runtime_monitor.runtime_health_summary()
        return {
            "runtime_health": health,
            "trend": "stable",
            "ts": int(time.time() * 1000),
        }


operations_scoreboard = OperationsScoreboard()

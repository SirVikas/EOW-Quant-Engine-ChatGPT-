"""GAP-06: Runtime Monitor — monitors live runtime health."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class RuntimeCheck:
    check_id: str
    component: str
    metric_name: str
    value: float
    status: str  # HEALTHY/DEGRADED/CRITICAL
    checked_at: int


class RuntimeMonitor:
    """Monitors live runtime health. Thread-safe."""

    VALID_STATUSES = {"HEALTHY", "DEGRADED", "CRITICAL"}

    def __init__(self):
        self._lock = threading.RLock()
        self._checks: List[RuntimeCheck] = []
        self._counter = 0
        logger.info("[GAP-06] RuntimeMonitor initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"RTM-{self._counter:03d}"

    def record(self, component: str, metric_name: str, value: float, status: str) -> str:
        with self._lock:
            cid = self._next_id()
            self._checks.append(RuntimeCheck(
                check_id=cid,
                component=component,
                metric_name=metric_name,
                value=value,
                status=status if status in self.VALID_STATUSES else "HEALTHY",
                checked_at=int(time.time() * 1000),
            ))
            return cid

    def degraded_components(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(c) for c in self._checks if c.status in {"DEGRADED", "CRITICAL"}]

    def runtime_health_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._checks)
            if total == 0:
                return {"total_checks": 0, "healthy_pct": 100.0, "critical_count": 0, "ts": int(time.time() * 1000)}
            healthy = sum(1 for c in self._checks if c.status == "HEALTHY")
            critical = sum(1 for c in self._checks if c.status == "CRITICAL")
            degraded = sum(1 for c in self._checks if c.status == "DEGRADED")
            components = list({c.component for c in self._checks})
            return {
                "total_checks": total,
                "healthy_count": healthy,
                "degraded_count": degraded,
                "critical_count": critical,
                "healthy_pct": round(healthy / total * 100, 2),
                "components_monitored": components,
                "ts": int(time.time() * 1000),
            }


runtime_monitor = RuntimeMonitor()

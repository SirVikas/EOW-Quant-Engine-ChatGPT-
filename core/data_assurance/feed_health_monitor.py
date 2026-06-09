"""
Feed health monitor — tracks latency and freshness of market data feeds.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class FeedHealthCheck:
    check_id: str
    feed_name: str
    is_healthy: bool
    latency_ms: float
    last_update_age_secs: float
    checked_at: str


class FeedHealthMonitor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._checks: List[FeedHealthCheck] = []
        self._latest: Dict[str, FeedHealthCheck] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"FHM-{self._counter:03d}"

    def record(
        self,
        feed_name: str,
        is_healthy: bool,
        latency_ms: float,
        last_update_age_secs: float,
    ) -> FeedHealthCheck:
        with self._lock:
            chk = FeedHealthCheck(
                check_id=self._next_id(),
                feed_name=feed_name,
                is_healthy=is_healthy,
                latency_ms=latency_ms,
                last_update_age_secs=last_update_age_secs,
                checked_at=datetime.utcnow().isoformat(),
            )
            self._checks.append(chk)
            self._latest[feed_name] = chk
            return chk

    def unhealthy_feeds(self) -> List[str]:
        with self._lock:
            return [name for name, chk in self._latest.items() if not chk.is_healthy]

    def feed_health_report(self) -> dict:
        with self._lock:
            total = len(self._latest)
            healthy = sum(1 for chk in self._latest.values() if chk.is_healthy)
            return {
                "total_feeds_monitored": total,
                "healthy": healthy,
                "unhealthy": total - healthy,
                "health_pct": round(healthy / total * 100, 2) if total else 100.0,
                "feeds": {
                    name: {
                        "is_healthy": chk.is_healthy,
                        "latency_ms": chk.latency_ms,
                        "last_update_age_secs": chk.last_update_age_secs,
                    }
                    for name, chk in self._latest.items()
                },
            }


feed_health_monitor = FeedHealthMonitor()

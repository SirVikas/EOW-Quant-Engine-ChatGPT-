"""External Dependency Tracker — tracks health of external system dependencies."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class ExternalDependency:
    dep_id: str
    name: str
    criticality: str  # CRITICAL / HIGH / MEDIUM / LOW
    status: str       # HEALTHY / DEGRADED / FAILED
    last_checked: str


_SEED_DEPS = [
    ("market_data_feed", "CRITICAL"),
    ("broker_api", "CRITICAL"),
    ("news_feed", "HIGH"),
    ("regulatory_feed", "MEDIUM"),
]


class ExternalDependencyTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._deps: Dict[str, ExternalDependency] = {}
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"DEP-{self._counter:03d}"

    def _seed(self):
        for name, criticality in _SEED_DEPS:
            dep = ExternalDependency(
                dep_id=self._next_id(),
                name=name,
                criticality=criticality,
                status="HEALTHY",
                last_checked=datetime.now(timezone.utc).isoformat(),
            )
            self._deps[name] = dep

    def record_status(self, name: str, status: str) -> dict:
        with self._lock:
            if name in self._deps:
                self._deps[name].status = status
                self._deps[name].last_checked = datetime.now(timezone.utc).isoformat()
                return asdict(self._deps[name])
            dep = ExternalDependency(
                dep_id=self._next_id(),
                name=name,
                criticality="MEDIUM",
                status=status,
                last_checked=datetime.now(timezone.utc).isoformat(),
            )
            self._deps[name] = dep
            return asdict(dep)

    def critical_dependencies(self) -> List[dict]:
        with self._lock:
            return [asdict(d) for d in self._deps.values() if d.criticality == "CRITICAL"]

    def dependency_health_summary(self) -> dict:
        with self._lock:
            total = len(self._deps)
            healthy = sum(1 for d in self._deps.values() if d.status == "HEALTHY")
            degraded = sum(1 for d in self._deps.values() if d.status == "DEGRADED")
            failed = sum(1 for d in self._deps.values() if d.status == "FAILED")
            return {
                "total": total,
                "healthy": healthy,
                "degraded": degraded,
                "failed": failed,
                "overall_health": "HEALTHY" if failed == 0 and degraded == 0 else ("DEGRADED" if failed == 0 else "CRITICAL"),
            }


external_dependency_tracker = ExternalDependencyTracker()

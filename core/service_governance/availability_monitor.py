"""Availability Monitor — monitors service availability."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class AvailabilityCheck:
    check_id: str
    service_name: str
    is_up: bool
    response_ms: float
    checked_at: datetime = field(default_factory=datetime.utcnow)


class AvailabilityMonitor:
    def __init__(self):
        self._lock = threading.RLock()
        self._checks: List[AvailabilityCheck] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"AVL-{self._counter:03d}"

    def record_check(self, service_name: str, is_up: bool, response_ms: float) -> AvailabilityCheck:
        with self._lock:
            chk = AvailabilityCheck(self._next_id(), service_name, is_up, response_ms)
            self._checks.append(chk)
            return chk

    def uptime_pct(self, service_name: str) -> float:
        with self._lock:
            checks = [c for c in self._checks if c.service_name == service_name]
            if not checks:
                return 100.0
            up = sum(1 for c in checks if c.is_up)
            return round(up / len(checks) * 100, 2)

    def degraded_services(self) -> List[str]:
        with self._lock:
            services = list({c.service_name for c in self._checks})
            return [s for s in services if self.uptime_pct(s) < 99.0]


availability_monitor = AvailabilityMonitor()

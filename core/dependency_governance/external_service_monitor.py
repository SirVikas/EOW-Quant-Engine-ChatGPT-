"""External Service Monitor — monitors external service health."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


ServiceStatus = Literal["UP", "DEGRADED", "DOWN"]


@dataclass
class ServiceCheck:
    check_id: str
    vendor_id: str
    service_name: str
    status: ServiceStatus
    latency_ms: float
    checked_at: datetime = field(default_factory=datetime.utcnow)


class ExternalServiceMonitor:
    def __init__(self):
        self._lock = threading.RLock()
        self._checks: List[ServiceCheck] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ESM-{self._counter:03d}"

    def record_check(self, vendor_id: str, service_name: str, status: ServiceStatus, latency_ms: float) -> ServiceCheck:
        with self._lock:
            chk = ServiceCheck(self._next_id(), vendor_id, service_name, status, latency_ms)
            self._checks.append(chk)
            return chk

    def degraded_vendors(self) -> List[str]:
        with self._lock:
            return list({c.vendor_id for c in self._checks if c.status in ("DEGRADED", "DOWN")})

    def health_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for c in self._checks:
                summary[c.status] = summary.get(c.status, 0) + 1
            return {"total_checks": len(self._checks), "by_status": summary}


external_service_monitor = ExternalServiceMonitor()

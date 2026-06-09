"""SLA Registry — registry of Service Level Agreements."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


SLAStatus = Literal["ACTIVE", "BREACHED", "SUSPENDED"]


@dataclass
class SLARecord:
    sla_id: str
    service_name: str
    availability_target_pct: float
    latency_target_ms: int
    recovery_time_objective_mins: int
    status: SLAStatus
    created_at: datetime = field(default_factory=datetime.utcnow)


class SLARegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._slas: List[SLARecord] = []
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"SLA-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("trading_engine", 99.9, 100, 5),
            ("api_layer", 99.5, 200, 10),
            ("data_feeds", 99.0, 500, 15),
            ("governance_layer", 99.0, 1000, 30),
        ]
        for svc, avail, lat, rto in seeds:
            self._slas.append(SLARecord(self._next_id(), svc, avail, lat, rto, "ACTIVE"))

    def register(self, service_name: str, availability_target_pct: float, latency_target_ms: int, rto_mins: int) -> SLARecord:
        with self._lock:
            rec = SLARecord(self._next_id(), service_name, availability_target_pct, latency_target_ms, rto_mins, "ACTIVE")
            self._slas.append(rec)
            return rec

    def active_slas(self) -> List[dict]:
        with self._lock:
            return [vars(s) for s in self._slas if s.status == "ACTIVE"]

    def breached_slas(self) -> List[dict]:
        with self._lock:
            return [vars(s) for s in self._slas if s.status == "BREACHED"]


sla_registry = SLARegistry()

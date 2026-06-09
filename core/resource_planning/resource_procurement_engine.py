"""Resource Procurement Engine — manages resource procurement."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ProcurementRequest:
    proc_id: str
    resource_type: str
    quantity: float
    estimated_cost: float
    status: str
    requested_at: datetime


class ResourceProcurementEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._requests: dict[str, ProcurementRequest] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"PRC-{self._counter:03d}"

    def request(self, resource_type: str, quantity: float,
                estimated_cost: float) -> ProcurementRequest:
        with self._lock:
            req = ProcurementRequest(
                proc_id=self._next_id(),
                resource_type=resource_type,
                quantity=quantity,
                estimated_cost=estimated_cost,
                status="PLANNED",
                requested_at=datetime.utcnow(),
            )
            self._requests[req.proc_id] = req
            return req

    def approve(self, proc_id: str) -> Optional[ProcurementRequest]:
        with self._lock:
            req = self._requests.get(proc_id)
            if req and req.status == "PLANNED":
                req.status = "APPROVED"
            return req

    def complete(self, proc_id: str) -> Optional[ProcurementRequest]:
        with self._lock:
            req = self._requests.get(proc_id)
            if req and req.status == "APPROVED":
                req.status = "PROCURED"
            return req

    def pending_procurements(self) -> list[dict]:
        with self._lock:
            return [
                {"proc_id": r.proc_id, "resource_type": r.resource_type,
                 "quantity": r.quantity, "estimated_cost": r.estimated_cost,
                 "status": r.status}
                for r in self._requests.values() if r.status != "PROCURED"
            ]


resource_procurement_engine = ResourceProcurementEngine()

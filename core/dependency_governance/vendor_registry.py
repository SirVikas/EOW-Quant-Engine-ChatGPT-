"""Vendor Registry — registry of third-party vendors."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


VendorType = Literal["DATA_PROVIDER", "BROKER", "INFRASTRUCTURE", "ANALYTICS"]
Criticality = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
ContractStatus = Literal["ACTIVE", "EXPIRING", "EXPIRED"]


@dataclass
class VendorRecord:
    vendor_id: str
    name: str
    vendor_type: VendorType
    criticality: Criticality
    contract_status: ContractStatus
    last_reviewed: datetime = field(default_factory=datetime.utcnow)


class VendorRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._vendors: List[VendorRecord] = []
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"VND-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("Market Data Provider", "DATA_PROVIDER", "CRITICAL"),
            ("Prime Broker", "BROKER", "CRITICAL"),
            ("Cloud Infrastructure", "INFRASTRUCTURE", "HIGH"),
        ]
        for name, vtype, crit in seeds:
            self._vendors.append(VendorRecord(self._next_id(), name, vtype, crit, "ACTIVE"))

    def register(self, name: str, vendor_type: VendorType, criticality: Criticality) -> VendorRecord:
        with self._lock:
            rec = VendorRecord(self._next_id(), name, vendor_type, criticality, "ACTIVE")
            self._vendors.append(rec)
            return rec

    def critical_vendors(self) -> List[dict]:
        with self._lock:
            return [vars(v) for v in self._vendors if v.criticality == "CRITICAL"]

    def vendor_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for v in self._vendors:
                summary[v.criticality] = summary.get(v.criticality, 0) + 1
            return {"total_vendors": len(self._vendors), "by_criticality": summary}

    def get(self, vendor_id: str):
        with self._lock:
            return next((v for v in self._vendors if v.vendor_id == vendor_id), None)


vendor_registry = VendorRegistry()

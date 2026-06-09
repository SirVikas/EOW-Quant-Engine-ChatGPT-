"""Dependency Risk Engine — assesses dependency risks."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


RiskType = Literal["CONCENTRATION", "AVAILABILITY", "COMPLIANCE", "FINANCIAL"]
Severity = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass
class DependencyRisk:
    risk_id: str
    vendor_id: str
    risk_type: RiskType
    severity: Severity
    description: str
    identified_at: datetime = field(default_factory=datetime.utcnow)


class DependencyRiskEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._risks: List[DependencyRisk] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DRK-{self._counter:03d}"

    def record_risk(self, vendor_id: str, risk_type: RiskType, severity: Severity, description: str) -> DependencyRisk:
        with self._lock:
            rec = DependencyRisk(self._next_id(), vendor_id, risk_type, severity, description)
            self._risks.append(rec)
            return rec

    def risks_for_vendor(self, vendor_id: str) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._risks if r.vendor_id == vendor_id]

    def high_severity_risks(self) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._risks if r.severity == "HIGH"]


dependency_risk_engine = DependencyRiskEngine()

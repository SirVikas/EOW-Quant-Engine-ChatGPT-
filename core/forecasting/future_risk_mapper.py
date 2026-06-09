"""Future risk mapper — strategic risk projection."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class FutureRisk:
    risk_id: str
    horizon_days: int
    risk_type: str
    probability: float
    severity: str
    mitigation: str
    projected_at: str


class FutureRiskMapper:
    def __init__(self):
        self._lock = threading.RLock()
        self._risks: list = []
        self._counter = 0

    def project_risk(self, risk_type: str, horizon_days: int, probability: float,
                     severity: str, mitigation: str = "") -> dict:
        with self._lock:
            self._counter += 1
            r = FutureRisk(
                risk_id=f"FRSK-{self._counter:04d}",
                horizon_days=horizon_days, risk_type=risk_type,
                probability=probability, severity=severity,
                mitigation=mitigation, projected_at=datetime.utcnow().isoformat(),
            )
            self._risks.append(r)
            return asdict(r)

    def risks_by_horizon(self, horizon_days: int) -> list:
        with self._lock:
            return sorted([asdict(r) for r in self._risks if r.horizon_days == horizon_days],
                          key=lambda x: x["probability"], reverse=True)

    def critical_future_risks(self) -> list:
        with self._lock:
            return [asdict(r) for r in self._risks if r.severity == "CRITICAL"]

    def risk_map_report(self) -> dict:
        with self._lock:
            total = len(self._risks)
            by_type: dict = {}
            by_sev: dict = {}
            for r in self._risks:
                by_type[r.risk_type] = by_type.get(r.risk_type, 0) + 1
                by_sev[r.severity] = by_sev.get(r.severity, 0) + 1
            critical = by_sev.get("CRITICAL", 0)
            return {"total_projected": total, "by_type": by_type, "by_severity": by_sev, "critical_count": critical}


future_risk_mapper = FutureRiskMapper()

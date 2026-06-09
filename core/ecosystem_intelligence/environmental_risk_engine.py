"""Environmental Risk Engine — tracks regulatory, infrastructure, and competitive risks."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List


@dataclass
class EnvironmentalRisk:
    risk_id: str
    risk_name: str
    risk_type: str      # REGULATORY / INFRASTRUCTURE / COMPETITIVE
    severity: str       # HIGH / MEDIUM / LOW
    probability_pct: float
    mitigation_status: str  # OPEN / MITIGATED
    registered_at: str


class EnvironmentalRiskEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._risks: List[EnvironmentalRisk] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ENV-{self._counter:03d}"

    def register_risk(self, risk_name: str, risk_type: str, severity: str,
                      probability_pct: float, mitigation_status: str = "OPEN") -> dict:
        with self._lock:
            risk = EnvironmentalRisk(
                risk_id=self._next_id(),
                risk_name=risk_name,
                risk_type=risk_type,
                severity=severity,
                probability_pct=probability_pct,
                mitigation_status=mitigation_status,
                registered_at=datetime.now(timezone.utc).isoformat(),
            )
            self._risks.append(risk)
            return asdict(risk)

    def open_risks(self) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._risks if r.mitigation_status == "OPEN"]

    def risk_summary(self) -> dict:
        with self._lock:
            total = len(self._risks)
            open_count = sum(1 for r in self._risks if r.mitigation_status == "OPEN")
            high_severity = sum(1 for r in self._risks if r.severity == "HIGH" and r.mitigation_status == "OPEN")
            return {
                "total_risks": total,
                "open_risks": open_count,
                "high_severity_open": high_severity,
                "mitigated": total - open_count,
            }


environmental_risk_engine = EnvironmentalRiskEngine()

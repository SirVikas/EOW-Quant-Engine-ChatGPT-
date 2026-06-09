"""Exposure analyzer — portfolio concentration tracking."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class ExposureRecord:
    record_id: str
    exposure_type: str
    name: str
    exposure_pct: float
    risk_contribution_pct: float
    concentration_risk: str
    recorded_at: str


def _concentration_risk(pct: float) -> str:
    if pct > 40:
        return "CRITICAL"
    if pct > 25:
        return "HIGH"
    if pct > 15:
        return "MEDIUM"
    return "LOW"


class ExposureAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list = []
        self._counter = 0

    def record_exposure(self, exposure_type: str, name: str, exposure_pct: float, risk_contribution_pct: float) -> dict:
        with self._lock:
            self._counter += 1
            r = ExposureRecord(
                record_id=f"EXP-{self._counter:04d}",
                exposure_type=exposure_type,
                name=name,
                exposure_pct=exposure_pct,
                risk_contribution_pct=risk_contribution_pct,
                concentration_risk=_concentration_risk(exposure_pct),
                recorded_at=datetime.utcnow().isoformat(),
            )
            self._records.append(r)
            return asdict(r)

    def all_exposures(self, exposure_type: Optional[str] = None) -> list:
        with self._lock:
            if exposure_type:
                return [asdict(r) for r in self._records if r.exposure_type == exposure_type]
            return [asdict(r) for r in self._records]

    def concentration_report(self) -> dict:
        with self._lock:
            groups: dict = {}
            for r in self._records:
                groups.setdefault(r.exposure_type, []).append(asdict(r))
            critical = [asdict(r) for r in self._records if r.concentration_risk == "CRITICAL"]
            high = [asdict(r) for r in self._records if r.concentration_risk == "HIGH"]
            return {"by_type": groups, "critical_concentrations": critical, "high_concentrations": high}

    def total_exposure_by_type(self) -> dict:
        with self._lock:
            totals: dict = {}
            for r in self._records:
                totals[r.exposure_type] = totals.get(r.exposure_type, 0) + r.exposure_pct
            return totals


exposure_analyzer = ExposureAnalyzer()

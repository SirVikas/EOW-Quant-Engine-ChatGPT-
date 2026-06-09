"""Strategic KPI Engine — tracks strategic KPIs."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


Trend = Literal["UP", "DOWN", "STABLE"]
KPICategory = Literal["FINANCIAL", "OPERATIONAL", "GOVERNANCE", "RESEARCH"]


@dataclass
class KPIRecord:
    kpi_id: str
    name: str
    current_value: float
    target_value: float
    unit: str
    trend: Trend
    category: KPICategory
    updated_at: datetime = field(default_factory=datetime.utcnow)


class StrategicKPIEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._kpis: List[KPIRecord] = []
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"KPI-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("Governance Layers Active", 10.0, 10.0, "layers", "STABLE", "GOVERNANCE"),
            ("Trade Win Rate", 55.0, 60.0, "pct", "UP", "FINANCIAL"),
            ("System Uptime", 99.9, 99.9, "pct", "STABLE", "OPERATIONAL"),
            ("Institutional Facts", 11.0, 500.0, "facts", "UP", "RESEARCH"),
            ("ETE Calibration Trades", 0.0, 500.0, "trades", "STABLE", "OPERATIONAL"),
        ]
        for name, cur, tgt, unit, trend, cat in seeds:
            self._kpis.append(KPIRecord(self._next_id(), name, cur, tgt, unit, trend, cat))

    def record_kpi(self, name: str, current_value: float, target_value: float, unit: str, category: KPICategory) -> KPIRecord:
        with self._lock:
            # Upsert by name
            for k in self._kpis:
                if k.name == name:
                    trend = "UP" if current_value > k.current_value else ("DOWN" if current_value < k.current_value else "STABLE")
                    k.current_value = current_value
                    k.target_value = target_value
                    k.trend = trend
                    k.updated_at = datetime.utcnow()
                    return k
            rec = KPIRecord(self._next_id(), name, current_value, target_value, unit, "STABLE", category)
            self._kpis.append(rec)
            return rec

    def off_target_kpis(self) -> List[dict]:
        with self._lock:
            return [vars(k) for k in self._kpis if k.current_value < k.target_value]

    def kpi_dashboard(self) -> List[dict]:
        with self._lock:
            return [vars(k) for k in self._kpis]


strategic_kpi_engine = StrategicKPIEngine()

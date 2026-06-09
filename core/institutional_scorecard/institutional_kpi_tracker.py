"""Institutional KPI tracker — pre-seeded KPI monitoring."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class KPI:
    kpi_id: str
    name: str
    category: str
    current_value: float
    target_value: float
    unit: str
    trend: str
    last_updated: str


class InstitutionalKPITracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._kpis: list = []
        self._previous: dict = {}
        self._seed()

    def _seed(self):
        seeds = [
            ("TRUST_SCORE", "TRUST", 50.0, 80.0, "score"),
            ("GOVERNANCE_COMPLIANCE", "GOVERNANCE", 75.0, 95.0, "pct"),
            ("ECONOMIC_ACCURACY", "ECONOMIC", 55.0, 70.0, "pct"),
            ("SAFETY_SCORE", "SAFETY", 70.0, 90.0, "score"),
            ("LEARNING_CYCLES", "LEARNING", 0.0, 10.0, "count"),
            ("AUDIT_COVERAGE", "AUDITABILITY", 60.0, 85.0, "pct"),
        ]
        for name, cat, current, target, unit in seeds:
            kpi = KPI(
                kpi_id=f"KPI-{len(self._kpis)+1:03d}",
                name=name, category=cat,
                current_value=current, target_value=target, unit=unit,
                trend="STABLE", last_updated=datetime.utcnow().isoformat(),
            )
            self._kpis.append(kpi)

    def update_kpi(self, name: str, current_value: float) -> bool:
        with self._lock:
            for kpi in self._kpis:
                if kpi.name == name:
                    prev = self._previous.get(name, kpi.current_value)
                    self._previous[name] = kpi.current_value
                    kpi.current_value = current_value
                    if current_value > prev + 0.5:
                        kpi.trend = "IMPROVING"
                    elif current_value < prev - 0.5:
                        kpi.trend = "DECLINING"
                    else:
                        kpi.trend = "STABLE"
                    kpi.last_updated = datetime.utcnow().isoformat()
                    return True
            return False

    def all_kpis(self) -> list:
        with self._lock:
            return [asdict(k) for k in self._kpis]

    def kpis_below_target(self) -> list:
        with self._lock:
            return [asdict(k) for k in self._kpis if k.current_value < k.target_value]

    def kpi_dashboard(self) -> dict:
        with self._lock:
            total = len(self._kpis)
            on_target = sum(1 for k in self._kpis if k.current_value >= k.target_value)
            below = total - on_target
            health_pct = (on_target / max(1, total)) * 100
            return {"total_kpis": total, "on_target": on_target, "below_target": below,
                    "overall_kpi_health_pct": health_pct}


institutional_kpi_tracker = InstitutionalKPITracker()

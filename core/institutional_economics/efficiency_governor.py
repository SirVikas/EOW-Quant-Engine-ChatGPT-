"""Efficiency Governor — computes institutional efficiency."""
import threading
from datetime import datetime


class EfficiencyGovernor:
    def __init__(self):
        self._lock = threading.RLock()
        self._history: list[dict] = []

    def compute_efficiency(self) -> dict:
        from core.institutional_economics.institutional_cost_engine import institutional_cost_engine
        from core.institutional_economics.value_creation_tracker import value_creation_tracker

        total_cost = institutional_cost_engine.total_cost()
        total_value = value_creation_tracker.total_value()
        cost_breakdown = institutional_cost_engine.cost_by_category()
        value_breakdown = value_creation_tracker.value_by_type()

        if total_cost == 0:
            roi_pct = 0.0
        else:
            roi_pct = round((total_value - total_cost) / total_cost * 100, 1)

        if roi_pct >= 50:
            grade = "A"
        elif roi_pct >= 20:
            grade = "B"
        elif roi_pct >= 0:
            grade = "C"
        elif roi_pct >= -20:
            grade = "D"
        else:
            grade = "F"

        result = {
            "roi_pct": roi_pct,
            "efficiency_grade": grade,
            "cost_breakdown": cost_breakdown,
            "value_breakdown": value_breakdown,
        }

        with self._lock:
            self._history.append({**result, "computed_at": datetime.utcnow().isoformat()})

        return result

    def efficiency_trend(self) -> list[dict]:
        with self._lock:
            return list(self._history[-10:])


efficiency_governor = EfficiencyGovernor()

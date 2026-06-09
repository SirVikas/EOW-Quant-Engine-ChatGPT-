"""Trend analyzer — rolling metric trend analysis."""
import threading
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque


@dataclass
class TrendRecord:
    metric_name: str
    values: list
    trend: str
    slope: float
    last_updated: str


class TrendAnalyzer:
    def __init__(self):
        self._lock = threading.RLock()
        self._trends: dict = {}  # metric_name -> TrendRecord

    def record(self, metric_name: str, value: float) -> dict:
        with self._lock:
            if metric_name not in self._trends:
                self._trends[metric_name] = TrendRecord(
                    metric_name=metric_name, values=[], trend="STABLE",
                    slope=0.0, last_updated=datetime.utcnow().isoformat(),
                )
            tr = self._trends[metric_name]
            tr.values.append(value)
            if len(tr.values) > 20:
                tr.values = tr.values[-20:]
            vals = tr.values
            n = len(vals)
            if n >= 2:
                slope = (vals[-1] - vals[0]) / max(1, n - 1)
            else:
                slope = 0.0
            tr.slope = slope
            if n >= 2:
                mean = sum(vals) / n
                variance = sum((v - mean) ** 2 for v in vals) / n
                std = math.sqrt(variance)
            else:
                std = 0.0
            if std > 5:
                tr.trend = "VOLATILE"
            elif slope > 0.5:
                tr.trend = "IMPROVING"
            elif slope < -0.5:
                tr.trend = "DECLINING"
            else:
                tr.trend = "STABLE"
            tr.last_updated = datetime.utcnow().isoformat()
            return asdict(tr)

    def get_trend(self, metric_name: str) -> dict:
        with self._lock:
            if metric_name in self._trends:
                return asdict(self._trends[metric_name])
            return {}

    def all_trends(self) -> list:
        with self._lock:
            return [asdict(t) for t in self._trends.values()]

    def declining_metrics(self) -> list:
        with self._lock:
            return [asdict(t) for t in self._trends.values() if t.trend == "DECLINING"]


trend_analyzer = TrendAnalyzer()

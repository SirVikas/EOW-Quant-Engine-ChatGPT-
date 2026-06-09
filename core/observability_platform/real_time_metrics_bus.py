"""Real-time metrics bus for cross-layer observability."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque
from typing import Optional


@dataclass
class Metric:
    metric_id: str
    layer: str
    metric_name: str
    value: float
    unit: str
    timestamp: str


class RealTimeMetricsBus:
    _MAX = 10000

    def __init__(self):
        self._lock = threading.RLock()
        self._metrics: deque = deque(maxlen=self._MAX)
        self._counter = 0

    def publish(self, layer: str, metric_name: str, value: float, unit: str = "") -> Metric:
        with self._lock:
            self._counter += 1
            m = Metric(
                metric_id=f"MET-{self._counter:05d}",
                layer=layer,
                metric_name=metric_name,
                value=value,
                unit=unit,
                timestamp=datetime.utcnow().isoformat(),
            )
            self._metrics.append(m)
            return m

    def latest(self, layer: Optional[str] = None, metric_name: Optional[str] = None) -> Optional[dict]:
        with self._lock:
            for m in reversed(list(self._metrics)):
                if layer and m.layer != layer:
                    continue
                if metric_name and m.metric_name != metric_name:
                    continue
                return asdict(m)
            return None

    def history(self, layer: str, metric_name: str, limit: int = 50) -> list:
        with self._lock:
            result = [asdict(m) for m in self._metrics if m.layer == layer and m.metric_name == metric_name]
            return result[-limit:]

    def all_latest(self) -> dict:
        with self._lock:
            seen = {}
            for m in reversed(list(self._metrics)):
                key = (m.layer, m.metric_name)
                if key not in seen:
                    seen[key] = m
            out: dict = {}
            for (layer, metric_name), m in seen.items():
                out.setdefault(layer, {})[metric_name] = m.value
            return out


real_time_metrics_bus = RealTimeMetricsBus()

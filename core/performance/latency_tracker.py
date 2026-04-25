"""
FTD-031 — Latency Tracker

Per-module nanosecond-precision timing with context manager support.
Maintains a rolling window of recent samples per module for p50/p95/p99 stats.

Usage:
    with latency_tracker.track("signal_pipeline"):
        ...

    stats = latency_tracker.stats("signal_pipeline")
    # {"p50_ms": 1.2, "p95_ms": 4.5, "p99_ms": 12.1, "samples": 500}
"""
from __future__ import annotations

import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from statistics import median, quantiles
from threading import Lock
from typing import Dict, Generator, List, Optional

_WINDOW = 500  # rolling samples per module


@dataclass
class LatencyStats:
    module: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    mean_ms: float
    samples: int


class _ModuleBuffer:
    __slots__ = ("_buf", "_lock")

    def __init__(self) -> None:
        self._buf: deque[float] = deque(maxlen=_WINDOW)
        self._lock = Lock()

    def record(self, ms: float) -> None:
        with self._lock:
            self._buf.append(ms)

    def stats(self) -> Optional[LatencyStats]:
        with self._lock:
            data = list(self._buf)
        if not data:
            return None
        n = len(data)
        sorted_data = sorted(data)
        p50 = median(sorted_data)
        if n >= 20:
            qs = quantiles(sorted_data, n=100)
            p95 = qs[94]
            p99 = qs[98]
        else:
            p95 = sorted_data[-1]
            p99 = sorted_data[-1]
        return LatencyStats(
            module="",
            p50_ms=round(p50, 3),
            p95_ms=round(p95, 3),
            p99_ms=round(p99, 3),
            min_ms=round(sorted_data[0], 3),
            max_ms=round(sorted_data[-1], 3),
            mean_ms=round(sum(data) / n, 3),
            samples=n,
        )


class LatencyTracker:
    """Singleton per-module latency tracker."""

    def __init__(self) -> None:
        self._modules: Dict[str, _ModuleBuffer] = {}
        self._lock = Lock()

    def _get_buf(self, module: str) -> _ModuleBuffer:
        with self._lock:
            if module not in self._modules:
                self._modules[module] = _ModuleBuffer()
            return self._modules[module]

    @contextmanager
    def track(self, module: str) -> Generator[None, None, None]:
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self._get_buf(module).record(elapsed_ms)

    def record(self, module: str, ms: float) -> None:
        self._get_buf(module).record(ms)

    def stats(self, module: str) -> Optional[LatencyStats]:
        buf = self._modules.get(module)
        if buf is None:
            return None
        s = buf.stats()
        if s is not None:
            s.module = module
        return s

    def all_stats(self) -> Dict[str, LatencyStats]:
        result: Dict[str, LatencyStats] = {}
        with self._lock:
            keys = list(self._modules.keys())
        for k in keys:
            s = self.stats(k)
            if s is not None:
                result[k] = s
        return result

    def snapshot(self) -> List[dict]:
        all_s = self.all_stats()
        out = []
        for name, s in all_s.items():
            out.append({
                "module": name,
                "p50_ms": s.p50_ms,
                "p95_ms": s.p95_ms,
                "p99_ms": s.p99_ms,
                "min_ms": s.min_ms,
                "max_ms": s.max_ms,
                "mean_ms": s.mean_ms,
                "samples": s.samples,
            })
        return sorted(out, key=lambda x: x["p99_ms"], reverse=True)


latency_tracker = LatencyTracker()

"""
FTD-031 — Rate Limiter

Token-bucket rate limiters for three domains (Q8):
  • cycle      — max run_cycle() calls per minute (PERF_MAX_CYCLES_PER_MIN)
  • api        — REST API requests per minute (PERF_API_RATE_MAX_PER_MIN)
  • dashboard  — WebSocket push per second (PERF_DASHBOARD_REFRESH_MAX_PER_SEC)

Thread-safe; non-blocking (check() returns bool immediately).

Usage:
    if not rate_limiter.check_cycle():
        return   # skip this tick
    if not rate_limiter.check_dashboard():
        return   # skip WS push

    rate_limiter.stats()  # {"cycle": {...}, "api": {...}, "dashboard": {...}}
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict

from config import cfg


@dataclass
class _Bucket:
    """Token-bucket: replenishes `rate` tokens per `period` seconds up to `capacity`."""
    capacity: float
    rate: float      # tokens per second
    _tokens: float = 0.0
    _last_refill: float = 0.0
    _allowed: int = 0
    _rejected: int = 0

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last_refill = time.monotonic()
        self._lock = Lock()

    def check(self) -> bool:
        now = time.monotonic()
        with self._lock:
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_refill = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self._allowed += 1
                return True
            self._rejected += 1
            return False

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._allowed + self._rejected
            return {
                "allowed":      self._allowed,
                "rejected":     self._rejected,
                "reject_pct":   round(self._rejected / total * 100, 1) if total else 0.0,
                "tokens_now":   round(self._tokens, 2),
            }


class RateLimiter:
    """Singleton facade with three buckets: cycle, api, dashboard."""

    def __init__(self) -> None:
        # cycle: PERF_MAX_CYCLES_PER_MIN → tokens/sec
        self._cycle = _Bucket(
            capacity=cfg.PERF_MAX_CYCLES_PER_MIN,
            rate=cfg.PERF_MAX_CYCLES_PER_MIN / 60.0,
        )
        # api: PERF_API_RATE_MAX_PER_MIN → tokens/sec
        self._api = _Bucket(
            capacity=cfg.PERF_API_RATE_MAX_PER_MIN,
            rate=cfg.PERF_API_RATE_MAX_PER_MIN / 60.0,
        )
        # dashboard: PERF_DASHBOARD_REFRESH_MAX_PER_SEC → tokens/sec
        self._dashboard = _Bucket(
            capacity=cfg.PERF_DASHBOARD_REFRESH_MAX_PER_SEC * 2,  # burst = 2×rate
            rate=cfg.PERF_DASHBOARD_REFRESH_MAX_PER_SEC,
        )

    def check_cycle(self) -> bool:
        return self._cycle.check()

    def check_api(self) -> bool:
        return self._api.check()

    def check_dashboard(self) -> bool:
        return self._dashboard.check()

    def stats(self) -> Dict[str, Any]:
        return {
            "cycle":     self._cycle.stats(),
            "api":       self._api.stats(),
            "dashboard": self._dashboard.stats(),
        }


rate_limiter = RateLimiter()

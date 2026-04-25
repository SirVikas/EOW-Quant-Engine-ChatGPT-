"""
FTD-031 — Cache Manager

Multi-level TTL cache for:
  • pattern_index       — learning engine pattern table
  • validation_result   — deep validation outcome
  • signal_state        — last signal per symbol
  • config_snapshot     — frozen EngineConfig view

Invalidation triggers (Q5):
  • new_trade_event     — clears signal_state + pattern_index
  • correction_applied  — clears validation_result + pattern_index
  • config_change       — clears config_snapshot
  • TTL expiry          — automatic per-entry

Thread-safe; async-compatible (no blocking I/O inside).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Optional, Tuple

from config import cfg


@dataclass
class _Entry:
    value: Any
    expires_at: float  # monotonic seconds


class _TTLCache:
    """Simple TTL dict, thread-safe."""

    def __init__(self, ttl_sec: float) -> None:
        self._ttl = ttl_sec
        self._data: Dict[str, _Entry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Tuple[bool, Any]:
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
        if entry is None or now > entry.expires_at:
            return False, None
        return True, entry.value

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None) -> None:
        ttl = ttl_sec if ttl_sec is not None else self._ttl
        expires_at = time.monotonic() + ttl
        with self._lock:
            self._data[key] = _Entry(value=value, expires_at=expires_at)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._data if k.startswith(prefix)]
            for k in keys:
                del self._data[k]
        return len(keys)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def size(self) -> int:
        now = time.monotonic()
        with self._lock:
            return sum(1 for e in self._data.values() if now <= e.expires_at)

    def evict_expired(self) -> int:
        now = time.monotonic()
        with self._lock:
            stale = [k for k, e in self._data.items() if now > e.expires_at]
            for k in stale:
                del self._data[k]
        return len(stale)


class CacheManager:
    """
    Singleton facade over four per-domain TTL caches.

    Domains:
        pattern     — PERF_CACHE_PATTERN_TTL_SEC
        validation  — PERF_CACHE_VALIDATION_TTL_SEC
        signal      — PERF_CACHE_SIGNAL_TTL_SEC
        config      — PERF_CACHE_CONFIG_TTL_SEC
    """

    def __init__(self) -> None:
        self.pattern    = _TTLCache(cfg.PERF_CACHE_PATTERN_TTL_SEC)
        self.validation = _TTLCache(cfg.PERF_CACHE_VALIDATION_TTL_SEC)
        self.signal     = _TTLCache(cfg.PERF_CACHE_SIGNAL_TTL_SEC)
        self.config     = _TTLCache(cfg.PERF_CACHE_CONFIG_TTL_SEC)
        self._hit = 0
        self._miss = 0
        self._lock = Lock()

    # ── Domain helpers ────────────────────────────────────────────────────────

    def get_pattern(self, key: str) -> Tuple[bool, Any]:
        hit, val = self.pattern.get(key)
        self._track(hit)
        return hit, val

    def set_pattern(self, key: str, value: Any) -> None:
        self.pattern.set(key, value)

    def get_validation(self, key: str) -> Tuple[bool, Any]:
        hit, val = self.validation.get(key)
        self._track(hit)
        return hit, val

    def set_validation(self, key: str, value: Any) -> None:
        self.validation.set(key, value)

    def get_signal(self, symbol: str) -> Tuple[bool, Any]:
        hit, val = self.signal.get(symbol)
        self._track(hit)
        return hit, val

    def set_signal(self, symbol: str, value: Any) -> None:
        self.signal.set(symbol, value)

    def get_config(self, key: str = "snapshot") -> Tuple[bool, Any]:
        hit, val = self.config.get(key)
        self._track(hit)
        return hit, val

    def set_config(self, value: Any, key: str = "snapshot") -> None:
        self.config.set(key, value)

    # ── Invalidation triggers (Q5) ────────────────────────────────────────────

    def on_new_trade_event(self, symbol: str) -> None:
        """Clear signal state + pattern index for this symbol."""
        self.signal.invalidate(symbol)
        self.pattern.invalidate_prefix(symbol)

    def on_correction_applied(self) -> None:
        """Clear validation results + entire pattern index."""
        self.validation.clear()
        self.pattern.clear()

    def on_config_change(self) -> None:
        """Clear config snapshot."""
        self.config.clear()

    # ── Maintenance ───────────────────────────────────────────────────────────

    def evict_all_expired(self) -> Dict[str, int]:
        return {
            "pattern":    self.pattern.evict_expired(),
            "validation": self.validation.evict_expired(),
            "signal":     self.signal.evict_expired(),
            "config":     self.config.evict_expired(),
        }

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hit + self._miss
            hit_rate = (self._hit / total * 100) if total else 0.0
        return {
            "hit": self._hit,
            "miss": self._miss,
            "hit_rate_pct": round(hit_rate, 1),
            "sizes": {
                "pattern":    self.pattern.size(),
                "validation": self.validation.size(),
                "signal":     self.signal.size(),
                "config":     self.config.size(),
            },
        }

    def _track(self, hit: bool) -> None:
        with self._lock:
            if hit:
                self._hit += 1
            else:
                self._miss += 1


cache_manager = CacheManager()

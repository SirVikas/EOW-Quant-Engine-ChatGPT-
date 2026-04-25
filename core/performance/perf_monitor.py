"""
FTD-031 — Performance Monitor

Central aggregator for all FTD-031 metrics (Q13/Q14/Q17):

  • Cycle time tracking (real-time + rolling p50/p95/p99)
  • Module latency via latency_tracker
  • Queue stats via task_queue
  • Rate limiter stats via rate_limiter
  • Memory footprint via memory_manager
  • Cache hit rate via cache_manager
  • Guard state via perf_guard
  • Alerting: latency breach, queue backlog, memory spike (Q14)
  • Benchmark baseline: locked after PERF_BENCHMARK_WARMUP_CYCLES (Q17)
  • Dynamic logging: full in dev, reduced in prod (Q10-C)

Usage:
    perf_monitor.on_cycle_start()
    ...
    perf_monitor.on_cycle_end(symbol="BTCUSDT")

    snapshot = perf_monitor.snapshot()    # full metrics dict
    perf_monitor.start_background_tasks() # call from lifespan
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from statistics import median, quantiles
from threading import Lock
from typing import Any, Deque, Dict, List, Optional

from loguru import logger

from config import cfg
from .cache_manager import cache_manager
from .latency_tracker import latency_tracker
from .memory_manager import memory_manager
from .perf_guard import perf_guard, STATE_SAFE_MODE
from .rate_limiter import rate_limiter

# Populated lazily to avoid circular imports at module load time
_task_queue_ref = None


def _get_task_queue():
    global _task_queue_ref
    if _task_queue_ref is None:
        from .async_task_queue import task_queue
        _task_queue_ref = task_queue
    return _task_queue_ref


@dataclass
class CycleRecord:
    symbol: str
    start_ts: float
    end_ts: float = 0.0

    @property
    def elapsed_ms(self) -> float:
        return (self.end_ts - self.start_ts) * 1000.0


class _BenchmarkBaseline:
    """Locks a cycle-time baseline after warmup cycles."""

    def __init__(self) -> None:
        self._samples: Deque[float] = deque(maxlen=cfg.PERF_BENCHMARK_WARMUP_CYCLES)
        self._locked = False
        self.baseline_p50_ms: float = 0.0
        self.baseline_p95_ms: float = 0.0
        self.baseline_p99_ms: float = 0.0
        self.baseline_mean_ms: float = 0.0
        self.target_ms: float = cfg.PERF_LATENCY_TARGET_MS

    def record(self, ms: float) -> bool:
        """Returns True when baseline is first locked."""
        if self._locked:
            return False
        self._samples.append(ms)
        if len(self._samples) >= cfg.PERF_BENCHMARK_WARMUP_CYCLES:
            self._lock_baseline()
            return True
        return False

    def _lock_baseline(self) -> None:
        data = sorted(self._samples)
        n = len(data)
        self.baseline_p50_ms = round(median(data), 3)
        if n >= 20:
            qs = quantiles(data, n=100)
            self.baseline_p95_ms = round(qs[94], 3)
            self.baseline_p99_ms = round(qs[98], 3)
        else:
            self.baseline_p95_ms = round(data[-1], 3)
            self.baseline_p99_ms = round(data[-1], 3)
        self.baseline_mean_ms = round(sum(data) / n, 3)
        self._locked = True
        logger.info(
            f"[FTD-031] Benchmark baseline locked after {n} cycles: "
            f"p50={self.baseline_p50_ms}ms p95={self.baseline_p95_ms}ms "
            f"p99={self.baseline_p99_ms}ms target={self.target_ms}ms"
        )

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def warmup_progress_pct(self) -> float:
        if self._locked:
            return 100.0
        return round(len(self._samples) / cfg.PERF_BENCHMARK_WARMUP_CYCLES * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "locked":           self._locked,
            "warmup_pct":       self.warmup_progress_pct,
            "p50_ms":           self.baseline_p50_ms,
            "p95_ms":           self.baseline_p95_ms,
            "p99_ms":           self.baseline_p99_ms,
            "mean_ms":          self.baseline_mean_ms,
            "target_ms":        self.target_ms,
        }


class PerfMonitor:
    """
    Singleton performance monitor — central FTD-031 hub.

    on_cycle_start() / on_cycle_end() are called from main.run_cycle().
    snapshot() returns a full metrics dictionary for /api/perf-status.
    """

    _MEM_CHECK_INTERVAL_CYCLES = 50   # check memory every N cycles

    def __init__(self) -> None:
        self._cycle_buf: Deque[float] = deque(maxlen=500)
        self._lock = Lock()
        self._cycle_count = 0
        self._active: Optional[CycleRecord] = None
        self._alerts: Deque[Dict[str, Any]] = deque(maxlen=200)
        self._baseline = _BenchmarkBaseline()
        self._log_mode = cfg.PERF_LOG_MODE  # "full" | "reduced" | "dynamic"
        self._session_start = time.monotonic()

    # ── Cycle hooks ───────────────────────────────────────────────────────────

    def on_cycle_start(self, symbol: str = "") -> None:
        self._active = CycleRecord(symbol=symbol, start_ts=time.perf_counter())

    def on_cycle_end(self, symbol: str = "") -> float:
        """Returns elapsed ms; feeds all downstream checks."""
        if self._active is None:
            return 0.0
        self._active.end_ts = time.perf_counter()
        elapsed_ms = self._active.elapsed_ms

        with self._lock:
            self._cycle_buf.append(elapsed_ms)
            self._cycle_count += 1
            count = self._cycle_count

        # Baseline recording
        if cfg.PERF_BENCHMARK_ENABLED:
            just_locked = self._baseline.record(elapsed_ms)
            if just_locked:
                pass  # logger already called inside _lock_baseline

        # Guard observation
        mem_critical = False
        if count % self._MEM_CHECK_INTERVAL_CYCLES == 0:
            mem_result = memory_manager.check()
            mem_critical = "CRITICAL_MEMORY" in " ".join(mem_result.get("alerts", []))

        guard_state = perf_guard.observe(elapsed_ms, memory_critical=mem_critical)

        # Alerting
        self._check_alerts(elapsed_ms, guard_state)

        # Dynamic logging
        self._maybe_log(elapsed_ms, symbol, guard_state)

        self._active = None
        return elapsed_ms

    # ── Alerting ──────────────────────────────────────────────────────────────

    def _check_alerts(self, elapsed_ms: float, guard_state: str) -> None:
        alerts: List[Dict[str, Any]] = []

        if elapsed_ms >= cfg.PERF_LATENCY_BREACH_MS:
            alerts.append({
                "type": "LATENCY_BREACH",
                "value_ms": round(elapsed_ms, 2),
                "threshold_ms": cfg.PERF_LATENCY_BREACH_MS,
                "ts": int(time.time() * 1000),
            })

        tq = _get_task_queue()
        if tq is not None:
            backlog = tq._queue.qsize() if tq._queue else 0
            if backlog >= cfg.PERF_QUEUE_BACKLOG_WARN:
                alerts.append({
                    "type": "QUEUE_BACKLOG",
                    "backlog": backlog,
                    "warn_threshold": cfg.PERF_QUEUE_BACKLOG_WARN,
                    "ts": int(time.time() * 1000),
                })

        if guard_state == STATE_SAFE_MODE and (
            not self._alerts or self._alerts[-1].get("type") != "SAFE_MODE_ACTIVE"
        ):
            alerts.append({
                "type": "SAFE_MODE_ACTIVE",
                "ts": int(time.time() * 1000),
            })

        for alert in alerts:
            with self._lock:
                self._alerts.append(alert)
            logger.warning(f"[FTD-031] ALERT: {alert}")

    # ── Logging ───────────────────────────────────────────────────────────────

    def _maybe_log(self, elapsed_ms: float, symbol: str, guard_state: str) -> None:
        mode = self._log_mode
        if mode == "dynamic":
            mode = "full" if elapsed_ms >= cfg.PERF_LATENCY_WARN_MS else "reduced"

        if mode == "full":
            logger.debug(
                f"[FTD-031] cycle symbol={symbol} elapsed={elapsed_ms:.2f}ms "
                f"guard={guard_state}"
            )
        # "reduced" → only log if breach
        elif elapsed_ms >= cfg.PERF_LATENCY_BREACH_MS:
            logger.warning(
                f"[FTD-031] cycle BREACH symbol={symbol} elapsed={elapsed_ms:.2f}ms "
                f"target={cfg.PERF_LATENCY_TARGET_MS}ms guard={guard_state}"
            )

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        """Full metrics dictionary — used by /api/perf-status."""
        with self._lock:
            buf = list(self._cycle_buf)
            count = self._cycle_count
            alerts = list(self._alerts)[-20:]

        cycle_stats: Dict[str, Any] = {"samples": len(buf)}
        if buf:
            sorted_buf = sorted(buf)
            n = len(sorted_buf)
            cycle_stats["mean_ms"] = round(sum(sorted_buf) / n, 3)
            cycle_stats["min_ms"] = round(sorted_buf[0], 3)
            cycle_stats["max_ms"] = round(sorted_buf[-1], 3)
            cycle_stats["p50_ms"] = round(median(sorted_buf), 3)
            if n >= 20:
                qs = quantiles(sorted_buf, n=100)
                cycle_stats["p95_ms"] = round(qs[94], 3)
                cycle_stats["p99_ms"] = round(qs[98], 3)
            else:
                cycle_stats["p95_ms"] = cycle_stats["max_ms"]
                cycle_stats["p99_ms"] = cycle_stats["max_ms"]
            cycle_stats["target_ms"] = cfg.PERF_LATENCY_TARGET_MS
            if cycle_stats.get("p99_ms", 0) > 0:
                cycle_stats["target_utilization_pct"] = round(
                    cycle_stats["p99_ms"] / cfg.PERF_LATENCY_TARGET_MS * 100, 1
                )

        tq = _get_task_queue()
        return {
            "enabled":       cfg.PERF_ENABLED,
            "uptime_min":    round((time.monotonic() - self._session_start) / 60, 1),
            "total_cycles":  count,
            "cycle_latency": cycle_stats,
            "guard":         perf_guard.stats(),
            "guard_history": perf_guard.history(5),
            "cache":         cache_manager.stats(),
            "rate_limiter":  rate_limiter.stats(),
            "memory":        memory_manager.stats(),
            "task_queue":    tq.stats() if tq else {},
            "module_latency": latency_tracker.snapshot(),
            "benchmark":     self._baseline.to_dict(),
            "recent_alerts": alerts,
        }

    def recent_alerts(self, n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._alerts)[-n:]

    # ── Background tasks ──────────────────────────────────────────────────────

    async def start_background_tasks(self) -> None:
        """Start periodic cache eviction + JSONL compaction trigger."""
        asyncio.create_task(self._evict_loop(), name="perf_evict_loop")
        logger.info("[FTD-031] PerfMonitor background tasks started")

    async def _evict_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(30)
                cache_manager.evict_all_expired()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"[FTD-031] evict_loop error: {exc}")


perf_monitor = PerfMonitor()

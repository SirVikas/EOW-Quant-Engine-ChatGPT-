"""
FTD-031 — Performance Optimization + Latency Control Layer

Exports:
    perf_monitor    — central metrics hub, on_cycle_start/end hooks
    latency_tracker — per-module ns timing context manager
    cache_manager   — TTL cache (pattern, validation, signal, config)
    task_queue      — async priority queue for batch jobs
    rate_limiter    — token-bucket for cycle/API/dashboard rate limiting
    memory_manager  — pattern cap, JSONL compaction, memory alerting
    perf_guard      — fail-safe state machine (NORMAL/DEGRADED/SAFE_MODE)
    PRIORITY_HIGH / PRIORITY_MEDIUM / PRIORITY_LOW
"""
from .perf_monitor   import perf_monitor
from .latency_tracker import latency_tracker
from .cache_manager  import cache_manager
from .async_task_queue import task_queue, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW
from .rate_limiter   import rate_limiter
from .memory_manager import memory_manager
from .perf_guard     import perf_guard

__all__ = [
    "perf_monitor",
    "latency_tracker",
    "cache_manager",
    "task_queue",
    "rate_limiter",
    "memory_manager",
    "perf_guard",
    "PRIORITY_HIGH",
    "PRIORITY_MEDIUM",
    "PRIORITY_LOW",
]

"""
PHOENIX OBSERVATORY-X — Report Scheduler  [OX-1B]

Manages automated, timely execution of all registered reports.

Design:
  - Each report definition carries a frequency (realtime | hourly | session |
    daily | weekly | on_demand).  The scheduler translates those labels into
    interval seconds and fires the corresponding API endpoint or generator.
  - Runs as a background asyncio task started from main.py lifespan.
  - Never raises to the caller — all errors are recorded in the health monitor.
  - on_demand reports are not auto-scheduled; they can be triggered via API.

Scheduling model:
  frequency     interval
  ─────────────────────
  realtime      not auto-scheduled (driven by engine ticks)
  hourly        3600 s
  session       1800 s  (every 30 min — approximates "per trading session")
  daily         86400 s
  weekly        604800 s
  on_demand     —
"""
from __future__ import annotations

import asyncio
import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Dict, List, Optional

from loguru import logger


# ── Constants ─────────────────────────────────────────────────────────────────

_FREQUENCY_INTERVALS: Dict[str, Optional[int]] = {
    "realtime":  None,
    "hourly":    3600,
    "session":   1800,
    "daily":     86400,
    "weekly":    604800,
    "on_demand": None,
}


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ScheduledJob:
    report_key: str
    frequency: str
    interval_secs: Optional[int]      # None = not auto-scheduled
    handler: Optional[Callable[[], Awaitable[None]]] = None  # async callable
    last_triggered: float = 0.0
    next_run: float = 0.0
    run_count: int = 0
    enabled: bool = True


# ── Scheduler ─────────────────────────────────────────────────────────────────

class ReportScheduler:
    """
    Background scheduler that fires registered report jobs at their
    configured intervals.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    # ── Registration ─────────────────────────────────────────────────────────

    def register_handler(
        self,
        report_key: str,
        frequency: str,
        handler: Callable[[], Awaitable[None]],
    ) -> None:
        """
        Attach an async handler to a report key.
        If the report key is already scheduled (from a previous registration),
        its handler is updated without resetting the run counter.
        """
        interval = _FREQUENCY_INTERVALS.get(frequency)
        with self._lock:
            existing = self._jobs.get(report_key)
            if existing:
                existing.handler = handler
                existing.interval_secs = interval
                existing.frequency = frequency
            else:
                self._jobs[report_key] = ScheduledJob(
                    report_key=report_key,
                    frequency=frequency,
                    interval_secs=interval,
                    handler=handler,
                    next_run=time.time(),  # eligible immediately
                )

    def enable(self, report_key: str) -> None:
        with self._lock:
            if report_key in self._jobs:
                self._jobs[report_key].enabled = True

    def disable(self, report_key: str) -> None:
        with self._lock:
            if report_key in self._jobs:
                self._jobs[report_key].enabled = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="observatory_scheduler")
        logger.info("[OBSERVATORY-X Scheduler] Started")

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[OBSERVATORY-X Scheduler] Stopped")

    # ── Manual Trigger ────────────────────────────────────────────────────────

    async def trigger(self, report_key: str) -> bool:
        """Manually trigger a report regardless of its schedule.  Returns True if fired."""
        with self._lock:
            job = self._jobs.get(report_key)
        if not job or not job.handler:
            return False
        await self._fire(job)
        return True

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        now = time.time()
        with self._lock:
            jobs = [
                {
                    "report_key":     j.report_key,
                    "frequency":      j.frequency,
                    "interval_secs":  j.interval_secs,
                    "enabled":        j.enabled,
                    "run_count":      j.run_count,
                    "last_triggered": j.last_triggered,
                    "next_run":       j.next_run,
                    "overdue_secs":   max(0.0, now - j.next_run) if j.interval_secs else 0.0,
                    "has_handler":    j.handler is not None,
                }
                for j in self._jobs.values()
            ]
        return {
            "running": self._running,
            "total_jobs": len(jobs),
            "enabled_jobs": sum(1 for j in jobs if j["enabled"]),
            "jobs_with_handlers": sum(1 for j in jobs if j["has_handler"]),
            "jobs": jobs,
        }

    # ── Internal Loop ─────────────────────────────────────────────────────────

    async def _loop(self) -> None:
        while self._running:
            now = time.time()
            with self._lock:
                due = [
                    j for j in self._jobs.values()
                    if j.enabled
                    and j.interval_secs is not None
                    and j.handler is not None
                    and now >= j.next_run
                ]
            for job in due:
                asyncio.create_task(self._fire(job), name=f"obs_{job.report_key}")
            await asyncio.sleep(30)   # check every 30 s — low overhead

    async def _fire(self, job: ScheduledJob) -> None:
        now = time.time()
        try:
            assert job.handler is not None
            await job.handler()
            with self._lock:
                job.last_triggered = now
                job.run_count += 1
                if job.interval_secs:
                    job.next_run = now + job.interval_secs
            logger.debug(f"[OBSERVATORY-X Scheduler] Fired: {job.report_key}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[OBSERVATORY-X Scheduler] Handler error [{job.report_key}]: {exc}")
            # Reschedule at a shortened retry window (10 % of normal interval)
            with self._lock:
                if job.interval_secs:
                    job.next_run = now + max(60, job.interval_secs // 10)


# Singleton
report_scheduler = ReportScheduler()

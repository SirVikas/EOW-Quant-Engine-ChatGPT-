"""
FTD-AIL-001: AIL Scheduler — asyncio-based periodic collector.
Runs collect_all() on schedule and triggers analysis pipeline.
"""
from __future__ import annotations
import asyncio
import time
from typing import Callable, Awaitable, Optional
from loguru import logger


class AILScheduler:
    def __init__(
        self,
        collect_fn: Callable,
        analyze_fn: Callable,
        interval_sec: float = 900.0,   # 15 min default
    ) -> None:
        self._collect_fn   = collect_fn
        self._analyze_fn   = analyze_fn
        self._interval_sec = interval_sec
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_run: Optional[float] = None
        self._run_count = 0

    def start(self) -> None:
        """Start the scheduler background task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"[AIL-SCHEDULER] Started | interval={self._interval_sec}s")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("[AIL-SCHEDULER] Stopped")

    async def force_run(self) -> dict:
        """Force an immediate collection + analysis cycle."""
        return await self._run_once()

    async def _loop(self) -> None:
        """Main scheduler loop — waits interval then runs."""
        await asyncio.sleep(60.0)  # initial grace period at boot
        while self._running:
            try:
                await self._run_once()
            except Exception as exc:
                logger.warning(f"[AIL-SCHEDULER] Cycle error: {exc}")
            await asyncio.sleep(self._interval_sec)

    async def _run_once(self) -> dict:
        self._last_run = time.time()
        self._run_count += 1
        snapshots = await asyncio.to_thread(self._collect_fn)
        # analyze_fn is async — call directly, NOT via to_thread, so it can await storage ops
        result = await self._analyze_fn(snapshots)
        logger.debug(
            f"[AIL-SCHEDULER] Cycle #{self._run_count} complete | "
            f"findings={result.get('new_findings', 0)}"
        )
        return result

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "last_run": self._last_run,
            "run_count": self._run_count,
            "interval_sec": self._interval_sec,
        }

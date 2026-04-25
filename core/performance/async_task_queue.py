"""
FTD-031 — Async Priority Task Queue

Routes non-critical (batch) work off the hot path so the real-time cycle
stays below PERF_LATENCY_TARGET_MS.

Priority levels (lower = higher priority):
    PRIORITY_HIGH   = 1   → validation, memory update
    PRIORITY_MEDIUM = 2   → dashboard, logging
    PRIORITY_LOW    = 3   → export, archiving

Batch modules (Q12): export_engine, deep_validation, learning_engine.

Usage:
    await task_queue.enqueue(my_coroutine(), priority=PRIORITY_LOW, name="export")
    await task_queue.start()        # call once at lifespan start
    await task_queue.shutdown()     # call at shutdown
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Coroutine, Dict, Optional

from loguru import logger

from config import cfg

PRIORITY_HIGH   = 1
PRIORITY_MEDIUM = 2
PRIORITY_LOW    = 3


@dataclass(order=True)
class _Task:
    priority: int
    seq: int = field(compare=True)
    name: str = field(compare=False, default="")
    coro: Any = field(compare=False, default=None)
    enqueued_at: float = field(compare=False, default_factory=time.monotonic)


class AsyncTaskQueue:
    """
    Bounded priority queue backed by asyncio workers.

    Metrics tracked: enqueued, completed, dropped, errors, queue_wait_ms.
    """

    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue = None  # type: ignore[assignment]
        self._seq = 0
        self._workers: list[asyncio.Task] = []
        self._running = False

        self._enqueued = 0
        self._completed = 0
        self._dropped = 0
        self._errors = 0
        self._total_wait_ms = 0.0

    async def start(self) -> None:
        if self._running:
            return
        self._queue = asyncio.PriorityQueue(maxsize=cfg.PERF_QUEUE_MAX_SIZE)
        self._running = True
        for i in range(cfg.PERF_QUEUE_WORKERS):
            t = asyncio.create_task(self._worker(i), name=f"perf_worker_{i}")
            self._workers.append(t)
        logger.info(
            f"[FTD-031] AsyncTaskQueue started: workers={cfg.PERF_QUEUE_WORKERS} "
            f"max_size={cfg.PERF_QUEUE_MAX_SIZE}"
        )

    async def shutdown(self) -> None:
        self._running = False
        if self._queue is not None:
            # Poison each worker
            for _ in self._workers:
                await self._queue.put(_Task(priority=0, seq=-1, name="_STOP_", coro=None))
        for t in self._workers:
            try:
                await asyncio.wait_for(t, timeout=3.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                t.cancel()
        self._workers.clear()
        logger.info("[FTD-031] AsyncTaskQueue shut down")

    async def enqueue(
        self,
        coro: Coroutine,
        priority: int = PRIORITY_MEDIUM,
        name: str = "",
    ) -> bool:
        if not self._running or self._queue is None:
            return False

        backlog = self._queue.qsize()
        if backlog >= cfg.PERF_QUEUE_BACKLOG_WARN:
            logger.warning(
                f"[FTD-031] Queue backlog={backlog} >= warn={cfg.PERF_QUEUE_BACKLOG_WARN} "
                f"task={name}"
            )

        self._seq += 1
        task = _Task(priority=priority, seq=self._seq, name=name, coro=coro)
        try:
            self._queue.put_nowait(task)
            self._enqueued += 1
            return True
        except asyncio.QueueFull:
            self._dropped += 1
            logger.warning(f"[FTD-031] Queue full — dropped task={name}")
            coro.close()
            return False

    async def _worker(self, worker_id: int) -> None:
        while True:
            try:
                task: _Task = await self._queue.get()
                if task.name == "_STOP_":
                    self._queue.task_done()
                    break

                wait_ms = (time.monotonic() - task.enqueued_at) * 1000.0
                self._total_wait_ms += wait_ms

                try:
                    await task.coro
                    self._completed += 1
                except Exception as exc:
                    self._errors += 1
                    logger.error(
                        f"[FTD-031] Worker {worker_id} task={task.name} error: {exc}"
                    )
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break

    def stats(self) -> Dict[str, Any]:
        completed = self._completed or 1
        return {
            "enqueued":     self._enqueued,
            "completed":    self._completed,
            "dropped":      self._dropped,
            "errors":       self._errors,
            "backlog":      self._queue.qsize() if self._queue else 0,
            "avg_wait_ms":  round(self._total_wait_ms / completed, 2),
        }


task_queue = AsyncTaskQueue()

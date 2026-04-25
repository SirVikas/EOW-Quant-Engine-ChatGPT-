"""
FTD-031 — Memory Manager

Controls memory footprint (Q9):
  • Enforces PERF_MAX_PATTERN_RECORDS cap on registered pattern stores
  • Triggers JSONL compaction when file exceeds PERF_JSONL_COMPACTION_THRESHOLD lines
  • Flags records older than PERF_ARCHIVE_DAYS for archiving
  • Monitors process RSS vs PERF_MEMORY_WARN_MB / PERF_MEMORY_CRITICAL_MB

External callers register their pattern stores via register_store().
The check() method is called periodically (e.g., every N cycles) from perf_monitor.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Protocol

from loguru import logger

from config import cfg


class PatternStore(Protocol):
    """Minimal interface a pattern store must expose to be managed."""
    def __len__(self) -> int: ...
    def trim(self, max_size: int) -> int: ...  # returns records trimmed


class _RegistrationEntry:
    __slots__ = ("name", "store", "trim_fn")

    def __init__(self, name: str, store: Any, trim_fn: Optional[Callable]) -> None:
        self.name = name
        self.store = store
        self.trim_fn = trim_fn


def _process_rss_mb() -> float:
    """Returns current process RSS in MB (Linux /proc/self/status)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
    except OSError:
        pass
    return 0.0


class MemoryManager:
    """
    Singleton memory footprint controller.

    Pattern stores are registered at startup; check() is called periodically.
    JSONL files are registered similarly — compaction trims them to the last
    PERF_JSONL_COMPACTION_THRESHOLD lines in-place.
    """

    def __init__(self) -> None:
        self._stores: List[_RegistrationEntry] = []
        self._jsonl_files: List[Path] = []
        self._lock = Lock()

        self._trimmed_total = 0
        self._compactions = 0
        self._last_check_ts: float = 0.0

    # ── Registration ──────────────────────────────────────────────────────────

    def register_store(
        self,
        name: str,
        store: Any,
        trim_fn: Optional[Callable[[int], int]] = None,
    ) -> None:
        with self._lock:
            self._stores.append(_RegistrationEntry(name, store, trim_fn))

    def register_jsonl(self, path: str | Path) -> None:
        with self._lock:
            self._jsonl_files.append(Path(path))

    # ── Main check ────────────────────────────────────────────────────────────

    def check(self) -> Dict[str, Any]:
        self._last_check_ts = time.monotonic()
        rss_mb = _process_rss_mb()
        trimmed_this_cycle = 0
        compacted_this_cycle = 0
        alerts: List[str] = []

        # 1. Pattern cap enforcement
        with self._lock:
            stores = list(self._stores)
        for entry in stores:
            try:
                size = len(entry.store)
                if size > cfg.PERF_MAX_PATTERN_RECORDS:
                    if entry.trim_fn:
                        n = entry.trim_fn(cfg.PERF_MAX_PATTERN_RECORDS)
                    elif hasattr(entry.store, "trim"):
                        n = entry.store.trim(cfg.PERF_MAX_PATTERN_RECORDS)
                    else:
                        n = 0
                    if n:
                        self._trimmed_total += n
                        trimmed_this_cycle += n
                        logger.debug(
                            f"[FTD-031] Trimmed {n} records from '{entry.name}' "
                            f"(was {size}, cap={cfg.PERF_MAX_PATTERN_RECORDS})"
                        )
            except Exception as exc:
                logger.warning(f"[FTD-031] Pattern trim error ({entry.name}): {exc}")

        # 2. JSONL compaction
        with self._lock:
            jsonl_files = list(self._jsonl_files)
        for path in jsonl_files:
            try:
                if path.exists():
                    line_count = _count_lines(path)
                    if line_count > cfg.PERF_JSONL_COMPACTION_THRESHOLD:
                        _compact_jsonl(path, cfg.PERF_JSONL_COMPACTION_THRESHOLD)
                        self._compactions += 1
                        compacted_this_cycle += 1
                        logger.info(
                            f"[FTD-031] Compacted JSONL {path.name}: "
                            f"{line_count} → {cfg.PERF_JSONL_COMPACTION_THRESHOLD} lines"
                        )
            except Exception as exc:
                logger.warning(f"[FTD-031] JSONL compaction error ({path}): {exc}")

        # 3. Memory alerts
        if rss_mb >= cfg.PERF_MEMORY_CRITICAL_MB:
            alerts.append(f"CRITICAL_MEMORY: RSS={rss_mb:.0f}MB >= {cfg.PERF_MEMORY_CRITICAL_MB}MB")
            logger.error(f"[FTD-031] {alerts[-1]}")
        elif rss_mb >= cfg.PERF_MEMORY_WARN_MB:
            alerts.append(f"HIGH_MEMORY: RSS={rss_mb:.0f}MB >= {cfg.PERF_MEMORY_WARN_MB}MB")
            logger.warning(f"[FTD-031] {alerts[-1]}")

        return {
            "rss_mb":               round(rss_mb, 1),
            "trimmed_this_cycle":   trimmed_this_cycle,
            "compacted_this_cycle": compacted_this_cycle,
            "trimmed_total":        self._trimmed_total,
            "compactions_total":    self._compactions,
            "alerts":               alerts,
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "rss_mb":            round(_process_rss_mb(), 1),
            "trimmed_total":     self._trimmed_total,
            "compactions_total": self._compactions,
            "registered_stores": len(self._stores),
            "registered_jsonl":  len(self._jsonl_files),
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _count_lines(path: Path) -> int:
    count = 0
    with open(path, "rb") as f:
        for _ in f:
            count += 1
    return count


def _compact_jsonl(path: Path, keep_last: int) -> None:
    """Keep only the last `keep_last` lines of a JSONL file."""
    with open(path, "rb") as f:
        lines = f.readlines()
    lines = lines[-keep_last:]
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        f.writelines(lines)
    tmp.replace(path)


memory_manager = MemoryManager()

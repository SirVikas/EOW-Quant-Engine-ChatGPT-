"""
EOW Quant Engine — Report Lifecycle Engine  (FTD-053-GAIA Phase 1)

Manages the full lifecycle of observability reports:
  - Atomic writes (temp-file + rename) — partial writes never corrupt live files
  - Directory hierarchy creation on demand
  - Rolling retention cleanup (max files, max age, max size)
  - Storage ceiling enforcement
  - Compressed + raw separation with distinct retention policies
  - Latest-file maintenance for dashboard / diagnostic reads

Design principles:
  • NEVER raises to caller — all methods return success flag or None
  • NEVER blocks trading engine — cleanup runs in bounded time
  • ATOMIC writes — temp + rename prevents partial-file reads
  • DIRECTORY-SAFE — creates missing directories silently
  • GOVERNANCE-FIRST — ceilings enforced before each write

Directory layout (all under PROJECT_ROOT/reports/observability/):
  raw/           — full telemetry blobs, short retention
  compressed/    — signal envelopes, long retention
  latest/        — single latest.json per category (always current)
  archive/       — age-off moved here before deletion (optional, disabled by default)

Usage:
  from core.observability.report_lifecycle_engine import report_lifecycle_engine

  ok = report_lifecycle_engine.write_compressed("rl_snapshot", compressed_dict)
  ok = report_lifecycle_engine.write_raw("rl_snapshot", raw_dict)
  data = report_lifecycle_engine.get_latest("rl_snapshot")
  pruned = report_lifecycle_engine.run_cleanup()
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from core.observability.intelligence_compressor import (
    RAW_MAX_FILES, RAW_MAX_AGE_HOURS, RAW_MAX_SIZE_MB,
    COMPRESSED_MAX_FILES, COMPRESSED_MAX_DAYS, COMPRESSED_MAX_SIZE_MB,
)


# ── Paths ─────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
OBS_ROOT      = _PROJECT_ROOT / "reports" / "observability"

RAW_DIR        = OBS_ROOT / "raw"
COMPRESSED_DIR = OBS_ROOT / "compressed"
LATEST_DIR     = OBS_ROOT / "latest"


# ── Tuning ────────────────────────────────────────────────────────────────────
# Max time allowed for a single cleanup pass before aborting (safety belt)
MAX_CLEANUP_SECS = 5.0

# Minimum free disk space to maintain (MB); writes refused if below this
MIN_FREE_DISK_MB = 100.0


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class WriteResult:
    success:  bool
    path:     Optional[Path] = None
    skipped:  bool           = False   # dedup skip
    error:    str            = ""


@dataclass
class CleanupResult:
    files_deleted: int   = 0
    bytes_freed:   int   = 0
    errors:        int   = 0
    elapsed_ms:    float = 0.0


@dataclass
class LifecycleStats:
    total_writes:       int   = 0
    total_raw_writes:   int   = 0
    total_comp_writes:  int   = 0
    total_dedup_skips:  int   = 0
    total_cleanup_runs: int   = 0
    total_files_pruned: int   = 0
    total_bytes_freed:  int   = 0
    last_cleanup_ts:    int   = 0
    last_write_ts:      int   = 0


class ReportLifecycleEngine:
    """
    Atomic-write, governed lifecycle manager for observability reports.
    Thread-safe via internal RLock.
    """

    MODULE  = "REPORT_LIFECYCLE"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._lock  = threading.RLock()
        self._stats = LifecycleStats()
        self._ensure_dirs()

    # ── Public write API ──────────────────────────────────────────────────────

    def write_compressed(
        self,
        category: str,
        data: Dict[str, Any],
        skip_dedup_check: bool = False,
    ) -> WriteResult:
        """
        Write a compressed intelligence snapshot.

        Uses checksum deduplication (skips write if identical within DEDUP_WINDOW).
        Enforces compressed retention ceiling before writing.
        Also updates latest/<category>.json atomically.
        """
        try:
            with self._lock:
                # Dedup check
                checksum = data.get("_checksum", "")
                if not skip_dedup_check and checksum:
                    from core.observability.intelligence_compressor import intelligence_compressor
                    if intelligence_compressor.is_duplicate(checksum):
                        self._stats.total_dedup_skips += 1
                        return WriteResult(success=True, skipped=True)

                # Storage ceiling check
                self._enforce_ceiling(COMPRESSED_DIR, COMPRESSED_MAX_SIZE_MB, COMPRESSED_MAX_FILES)

                ts  = int(time.time() * 1000)
                fn  = f"{category}_{ts}.json"
                dst = COMPRESSED_DIR / fn

                ok = self._write_atomic(dst, data)
                if ok:
                    # Update latest pointer
                    self._write_atomic(LATEST_DIR / f"{category}.json", data)
                    self._stats.total_comp_writes += 1
                    self._stats.total_writes      += 1
                    self._stats.last_write_ts      = ts
                    return WriteResult(success=True, path=dst)
                return WriteResult(success=False, error="atomic write failed")

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] write_compressed error: {exc}")
            return WriteResult(success=False, error=str(exc))

    def write_raw(
        self,
        category: str,
        data: Dict[str, Any],
    ) -> WriteResult:
        """
        Write a raw telemetry blob.
        Short retention — for diagnostic deep-dives only.
        Enforces raw retention ceiling before writing.
        """
        try:
            with self._lock:
                self._enforce_ceiling(RAW_DIR, RAW_MAX_SIZE_MB, RAW_MAX_FILES)

                ts  = int(time.time() * 1000)
                fn  = f"{category}_{ts}.json"
                dst = RAW_DIR / fn

                ok = self._write_atomic(dst, data)
                if ok:
                    self._stats.total_raw_writes += 1
                    self._stats.total_writes     += 1
                    self._stats.last_write_ts     = ts
                    return WriteResult(success=True, path=dst)
                return WriteResult(success=False, error="atomic write failed")

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] write_raw error: {exc}")
            return WriteResult(success=False, error=str(exc))

    def get_latest(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Read the latest compressed snapshot for a category.
        Returns None if not found or unreadable.
        """
        try:
            path = LATEST_DIR / f"{category}.json"
            if not path.exists():
                return None
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.debug(f"[{self.MODULE}] get_latest({category}) failed: {exc}")
            return None

    # ── Cleanup API ───────────────────────────────────────────────────────────

    def run_cleanup(self) -> CleanupResult:
        """
        Full retention cleanup pass across raw and compressed directories.
        Bounded by MAX_CLEANUP_SECS — aborts gracefully if too slow.
        Safe to call from background task or on-demand.
        """
        result = CleanupResult()
        t0 = time.monotonic()

        try:
            with self._lock:
                # Raw: 24h age cutoff
                raw_age_cutoff = time.time() - (RAW_MAX_AGE_HOURS * 3600)
                r1 = self._prune_by_age(RAW_DIR, raw_age_cutoff)
                result.files_deleted += r1[0]
                result.bytes_freed   += r1[1]
                result.errors        += r1[2]

                if time.monotonic() - t0 > MAX_CLEANUP_SECS:
                    logger.debug(f"[{self.MODULE}] cleanup time limit hit after raw prune")
                    self._finalize_cleanup(result, t0)
                    return result

                # Compressed: 30-day age cutoff
                comp_age_cutoff = time.time() - (COMPRESSED_MAX_DAYS * 86400)
                r2 = self._prune_by_age(COMPRESSED_DIR, comp_age_cutoff)
                result.files_deleted += r2[0]
                result.bytes_freed   += r2[1]
                result.errors        += r2[2]

                if time.monotonic() - t0 > MAX_CLEANUP_SECS:
                    logger.debug(f"[{self.MODULE}] cleanup time limit hit after compressed prune")
                    self._finalize_cleanup(result, t0)
                    return result

                # Ceiling enforcement
                self._enforce_ceiling(RAW_DIR, RAW_MAX_SIZE_MB, RAW_MAX_FILES)
                self._enforce_ceiling(COMPRESSED_DIR, COMPRESSED_MAX_SIZE_MB, COMPRESSED_MAX_FILES)

                self._finalize_cleanup(result, t0)
                return result

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] run_cleanup error: {exc}")
            result.errors += 1
            self._finalize_cleanup(result, t0)
            return result

    def status(self) -> Dict[str, Any]:
        """Returns lifecycle engine status — safe to call from any context."""
        try:
            s = self._stats
            raw_count  = _count_files(RAW_DIR)
            comp_count = _count_files(COMPRESSED_DIR)
            raw_mb     = _dir_size_mb(RAW_DIR)
            comp_mb    = _dir_size_mb(COMPRESSED_DIR)

            return {
                "module":             self.MODULE,
                "version":            self.VERSION,
                "stats": {
                    "total_writes":       s.total_writes,
                    "total_raw_writes":   s.total_raw_writes,
                    "total_comp_writes":  s.total_comp_writes,
                    "total_dedup_skips":  s.total_dedup_skips,
                    "total_cleanup_runs": s.total_cleanup_runs,
                    "total_files_pruned": s.total_files_pruned,
                    "last_cleanup_ts":    s.last_cleanup_ts,
                    "last_write_ts":      s.last_write_ts,
                },
                "storage": {
                    "raw_files":     raw_count,
                    "raw_mb":        round(raw_mb, 2),
                    "raw_ceiling_mb": RAW_MAX_SIZE_MB,
                    "comp_files":    comp_count,
                    "comp_mb":       round(comp_mb, 2),
                    "comp_ceiling_mb": COMPRESSED_MAX_SIZE_MB,
                },
                "paths": {
                    "raw":        str(RAW_DIR),
                    "compressed": str(COMPRESSED_DIR),
                    "latest":     str(LATEST_DIR),
                },
            }
        except Exception as exc:
            return {"module": self.MODULE, "error": str(exc)}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_dirs(self) -> None:
        """Create directory hierarchy silently."""
        for d in (RAW_DIR, COMPRESSED_DIR, LATEST_DIR):
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                logger.warning(f"[{self.MODULE}] mkdir {d} failed: {exc}")

    def _write_atomic(self, dst: Path, data: Dict[str, Any]) -> bool:
        """
        Atomic write using temp-file + os.replace.
        Guarantees dst is never left in a partial-write state.
        """
        try:
            # Ensure parent exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file in same directory (same filesystem → rename is atomic)
            fd, tmp_path = tempfile.mkstemp(
                dir=dst.parent,
                prefix=".tmp_",
                suffix=".json",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                os.replace(tmp_path, dst)   # atomic on POSIX
                return True
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception as exc:
            logger.debug(f"[{self.MODULE}] _write_atomic to {dst} failed: {exc}")
            return False

    def _prune_by_age(
        self,
        directory: Path,
        cutoff_ts: float,
    ) -> Tuple[int, int, int]:
        """
        Delete files older than cutoff_ts (epoch seconds).
        Returns (files_deleted, bytes_freed, errors).
        """
        deleted = freed = errors = 0
        if not directory.exists():
            return deleted, freed, errors

        for fp in sorted(directory.iterdir(), key=lambda p: p.stat().st_mtime):
            try:
                if fp.is_file() and fp.stat().st_mtime < cutoff_ts:
                    size = fp.stat().st_size
                    fp.unlink()
                    deleted += 1
                    freed   += size
            except Exception as exc:
                logger.debug(f"[{self.MODULE}] prune {fp}: {exc}")
                errors += 1

        return deleted, freed, errors

    def _enforce_ceiling(
        self,
        directory: Path,
        max_mb: float,
        max_files: int,
    ) -> None:
        """
        Remove oldest files until both file count and size are under ceiling.
        Runs synchronously — must be fast (files already pruned by age).
        """
        if not directory.exists():
            return
        try:
            files = sorted(
                (p for p in directory.iterdir() if p.is_file()),
                key=lambda p: p.stat().st_mtime,
            )
            # Count ceiling
            while len(files) >= max_files:
                oldest = files.pop(0)
                try:
                    oldest.unlink()
                    self._stats.total_files_pruned += 1
                except Exception:
                    pass

            # Size ceiling
            total_bytes = sum(p.stat().st_size for p in files if p.exists())
            max_bytes   = int(max_mb * 1024 * 1024)
            while total_bytes > max_bytes and files:
                oldest = files.pop(0)
                try:
                    size = oldest.stat().st_size
                    oldest.unlink()
                    total_bytes -= size
                    self._stats.total_files_pruned += 1
                except Exception:
                    pass
        except Exception as exc:
            logger.debug(f"[{self.MODULE}] _enforce_ceiling {directory}: {exc}")

    def _finalize_cleanup(self, result: CleanupResult, t0: float) -> None:
        result.elapsed_ms = round((time.monotonic() - t0) * 1000, 1)
        self._stats.total_cleanup_runs += 1
        self._stats.total_files_pruned += result.files_deleted
        self._stats.total_bytes_freed  += result.bytes_freed
        self._stats.last_cleanup_ts     = int(time.time() * 1000)


# ── File-system helpers ───────────────────────────────────────────────────────

def _count_files(directory: Path) -> int:
    try:
        return sum(1 for p in directory.iterdir() if p.is_file())
    except Exception:
        return 0


def _dir_size_mb(directory: Path) -> float:
    try:
        return sum(
            p.stat().st_size for p in directory.iterdir() if p.is_file()
        ) / (1024 * 1024)
    except Exception:
        return 0.0


# ── Module-level singleton ────────────────────────────────────────────────────
report_lifecycle_engine = ReportLifecycleEngine()

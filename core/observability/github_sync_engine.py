"""
EOW Quant Engine — GitHub Sync Engine  (FTD-053-GAIA Phase 3)

Smart-batched, dedup-governed intelligence synchronization bridge.
Accumulates compressed snapshots + anomaly events + delta reports into
a governed batch, then flushes a compact summary to a local sync-ready
file. The actual GitHub push is caller-supplied (adapter pattern) so the
engine has zero network dependencies and stays fully testable.

Design principles:
  • BATCH-FIRST    — accumulate; never push every snapshot individually
  • ANOMALY-FIRST  — CRITICAL anomaly bypasses time gate, syncs immediately
  • DEDUP-GATED    — identical payload checksum suppresses write + push
  • RATE-LIMITED   — max MAX_SYNCS_PER_HOUR syncs; cooling enforced
  • NON-BLOCKING   — sync failures never affect trading engine
  • ADAPTER-PATTERN — push mechanism is injected; engine is purely local
  • TOKEN-SAFE     — payload is the compressed summary, NOT raw telemetry

Flush triggers (in priority order):
  1. CRITICAL anomaly in batch                   → immediate flush
  2. HIGH anomaly count ≥ HIGH_FLUSH_THRESHOLD   → flush
  3. Batch size ≥ MAX_BATCH_SIZE                 → flush
  4. Time since last flush ≥ SYNC_INTERVAL_SECS  → flush
  5. force=True                                  → flush unconditionally

Suppression conditions (checked before any flush):
  A. Payload checksum == last synced checksum    → suppress (no change)
  B. Syncs in last hour ≥ MAX_SYNCS_PER_HOUR    → suppress (rate limit)
  C. Time since last sync < MIN_SYNC_COOLDOWN_SECS → suppress (cooling)

Sync payload (written atomically to SYNC_DIR):
  {
    "sync_ts":        int (ms),
    "sync_reason":    str,
    "payload_checksum": str,
    "session_summary":  {compressed snapshot fields},
    "anomaly_summary": {
      "worst_severity": str,
      "critical": [...descriptions],
      "high":     [...descriptions],
      "medium_count": int,
      "low_count":    int,
    },
    "delta_summary": {
      "significant_changes": [field, ...],
      "significance_score":  float,
    },
    "batch_stats": {
      "snapshots_queued":  int,
      "anomalies_queued":  int,
      "period_secs":       float,
      "suppressed_deltas": int,
    },
  }
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW


# ── Tuning constants ──────────────────────────────────────────────────────────

SYNC_INTERVAL_SECS    = 900       # 15 minutes between routine syncs
MIN_SYNC_COOLDOWN_SECS = 120      # never sync more often than every 2 minutes
MAX_BATCH_SIZE         = 20       # flush when batch accumulates this many snapshots
HIGH_FLUSH_THRESHOLD   = 3        # flush when this many HIGH anomalies accumulated
MAX_SYNCS_PER_HOUR     = 4        # hard rate cap
MAX_ANOMALIES_IN_PAYLOAD = 5      # per-severity cap for payload (token governance)

# Flush reason codes
REASON_CRITICAL     = "CRITICAL_ANOMALY"
REASON_HIGH_CLUSTER = "HIGH_ANOMALY_CLUSTER"
REASON_BATCH_FULL   = "BATCH_FULL"
REASON_TIME         = "TIME_THRESHOLD"
REASON_FORCE        = "FORCE"
REASON_SUPPRESSED   = "SUPPRESSED"
REASON_RATE_LIMITED = "RATE_LIMITED"
REASON_DEDUP        = "DEDUP_IDENTICAL"
REASON_COOLING      = "COOLING_PERIOD"

# Local sync file location
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNC_DIR      = _PROJECT_ROOT / "reports" / "observability" / "sync_queue"


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class SyncResult:
    flushed:          bool
    reason:           str
    payload_checksum: str   = ""
    batch_size:       int   = 0
    anomaly_count:    int   = 0
    path:             Optional[Path] = None
    error:            str   = ""


@dataclass
class _BatchEntry:
    compressed:   Dict[str, Any]
    anomalies:    List[Dict[str, Any]]
    delta_report: Optional[Dict[str, Any]]
    ts:           int


@dataclass
class SyncStats:
    total_queued:    int = 0
    total_flushed:   int = 0
    total_suppressed:int = 0
    total_errors:    int = 0
    last_sync_ts:    int = 0
    last_checksum:   str = ""
    sync_ts_history: List[int] = field(default_factory=list)  # last 60 sync timestamps


class GitHubSyncEngine:
    """
    Governed intelligence batch accumulator and sync coordinator.
    Thread-safe via internal RLock.
    Actual GitHub push is injected via set_push_adapter().
    """

    MODULE  = "GITHUB_SYNC_ENGINE"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._lock          = threading.RLock()
        self._batch:        List[_BatchEntry] = []
        self._stats         = SyncStats()
        self._batch_start_ts: int = int(time.time() * 1000)

        # Injected push adapter: callable(payload: Dict) -> bool
        # Default: no-op (local file write only)
        self._push_adapter: Optional[Callable[[Dict[str, Any]], bool]] = None

        SYNC_DIR.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_push_adapter(self, adapter: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Inject a push adapter. Called with the sync payload dict;
        should return True on success, False on failure.
        Never called if payload is suppressed.
        """
        with self._lock:
            self._push_adapter = adapter

    def queue_snapshot(
        self,
        compressed:   Dict[str, Any],
        delta_report: Optional[Dict[str, Any]] = None,
        anomalies:    Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Add a compressed snapshot (+ optional delta + anomalies) to the batch.
        Triggers an immediate flush if CRITICAL anomaly is present.
        Returns True if an automatic flush was triggered.
        """
        try:
            with self._lock:
                entry = _BatchEntry(
                    compressed=compressed,
                    anomalies=anomalies or [],
                    delta_report=delta_report,
                    ts=int(time.time() * 1000),
                )
                self._batch.append(entry)
                self._stats.total_queued += 1

                # Auto-flush on CRITICAL
                has_critical = any(
                    a.get("severity") == SEV_CRITICAL
                    for a in (anomalies or [])
                )
                if has_critical:
                    result = self._do_flush(REASON_CRITICAL)
                    return result.flushed

                # Auto-flush on HIGH cluster
                high_count = sum(
                    sum(1 for a in e.anomalies if a.get("severity") == SEV_HIGH)
                    for e in self._batch
                )
                if high_count >= HIGH_FLUSH_THRESHOLD:
                    result = self._do_flush(REASON_HIGH_CLUSTER)
                    return result.flushed

                # Auto-flush on batch full
                if len(self._batch) >= MAX_BATCH_SIZE:
                    result = self._do_flush(REASON_BATCH_FULL)
                    return result.flushed

                return False

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] queue_snapshot error: {exc}")
            return False

    def flush(self, force: bool = False) -> SyncResult:
        """
        Attempt a flush. Respects governance rules unless force=True.
        Safe to call from background task on a timer.
        """
        try:
            with self._lock:
                if not self._batch:
                    return SyncResult(flushed=False, reason="EMPTY_BATCH")

                reason = REASON_FORCE if force else REASON_TIME
                return self._do_flush(reason, bypass_governance=force)
        except Exception as exc:
            logger.warning(f"[{self.MODULE}] flush error: {exc}")
            return SyncResult(flushed=False, reason="ERROR", error=str(exc))

    def should_flush(self) -> bool:
        """
        Check if a time-based flush is due (for background task polling).
        Does NOT trigger the flush.
        """
        try:
            with self._lock:
                if not self._batch:
                    return False
                elapsed = (int(time.time() * 1000) - self._batch_start_ts) / 1000.0
                return elapsed >= SYNC_INTERVAL_SECS
        except Exception:
            return False

    def get_pending_payload(self) -> Optional[Dict[str, Any]]:
        """
        Build and return the current batch payload WITHOUT flushing.
        Returns None if batch is empty.
        Useful for inspection or manual push orchestration.
        """
        try:
            with self._lock:
                if not self._batch:
                    return None
                return self._build_payload(self._batch, reason="PREVIEW")
        except Exception as exc:
            logger.warning(f"[{self.MODULE}] get_pending_payload error: {exc}")
            return None

    def mark_synced(self, checksum: str) -> None:
        """
        Called by the push adapter after a successful GitHub push.
        Updates last-sync state so future dedup works correctly.
        """
        with self._lock:
            self._stats.last_checksum = checksum
            self._stats.last_sync_ts  = int(time.time() * 1000)
            ts_hist = self._stats.sync_ts_history
            ts_hist.append(self._stats.last_sync_ts)
            if len(ts_hist) > 60:
                ts_hist.pop(0)

    def status(self) -> Dict[str, Any]:
        """Engine health + sync statistics. Never raises."""
        try:
            with self._lock:
                s = self._stats
                now_ms = int(time.time() * 1000)
                secs_since_sync = (now_ms - s.last_sync_ts) / 1000.0 if s.last_sync_ts else None
                syncs_last_hour = self._syncs_in_last_hour()
                return {
                    "module":           self.MODULE,
                    "version":          self.VERSION,
                    "batch_size":       len(self._batch),
                    "syncs_last_hour":  syncs_last_hour,
                    "rate_limit":       MAX_SYNCS_PER_HOUR,
                    "secs_since_sync":  round(secs_since_sync, 0) if secs_since_sync else None,
                    "sync_interval":    SYNC_INTERVAL_SECS,
                    "should_flush":     self.should_flush(),
                    "stats": {
                        "total_queued":     s.total_queued,
                        "total_flushed":    s.total_flushed,
                        "total_suppressed": s.total_suppressed,
                        "total_errors":     s.total_errors,
                        "last_sync_ts":     s.last_sync_ts,
                        "last_checksum":    s.last_checksum,
                    },
                    "governance": {
                        "max_batch_size":      MAX_BATCH_SIZE,
                        "high_flush_threshold": HIGH_FLUSH_THRESHOLD,
                        "max_syncs_per_hour":  MAX_SYNCS_PER_HOUR,
                        "min_cooldown_secs":   MIN_SYNC_COOLDOWN_SECS,
                    },
                }
        except Exception as exc:
            return {"module": self.MODULE, "error": str(exc)}

    # ── Internal flush logic ──────────────────────────────────────────────────

    def _do_flush(
        self,
        reason: str,
        bypass_governance: bool = False,
    ) -> SyncResult:
        """
        Core flush implementation. Caller must hold self._lock.
        """
        if not self._batch:
            return SyncResult(flushed=False, reason="EMPTY_BATCH")

        now_ms  = int(time.time() * 1000)
        payload = self._build_payload(self._batch, reason)
        checksum = _checksum(payload)

        # ── Governance checks (skipped only for force) ─────────────────────
        if not bypass_governance:
            # Rate limit
            if self._syncs_in_last_hour() >= MAX_SYNCS_PER_HOUR:
                self._stats.total_suppressed += 1
                return SyncResult(flushed=False, reason=REASON_RATE_LIMITED,
                                  payload_checksum=checksum)

            # Cooling period
            if self._stats.last_sync_ts > 0:
                secs_since = (now_ms - self._stats.last_sync_ts) / 1000.0
                if secs_since < MIN_SYNC_COOLDOWN_SECS:
                    self._stats.total_suppressed += 1
                    return SyncResult(flushed=False, reason=REASON_COOLING,
                                      payload_checksum=checksum)

            # Dedup: identical payload
            if checksum == self._stats.last_checksum:
                self._stats.total_suppressed += 1
                return SyncResult(flushed=False, reason=REASON_DEDUP,
                                  payload_checksum=checksum)

        # ── Write payload atomically ───────────────────────────────────────
        out_path = self._write_sync_file(payload, checksum)

        # ── Invoke push adapter (if registered) ───────────────────────────
        if self._push_adapter is not None:
            try:
                self._push_adapter(payload)
            except Exception as exc:
                logger.warning(f"[{self.MODULE}] push adapter error: {exc}")
                self._stats.total_errors += 1
                # Don't fail the flush — local file is the source of truth

        # ── Update state ───────────────────────────────────────────────────
        batch_size    = len(self._batch)
        anomaly_count = sum(len(e.anomalies) for e in self._batch)

        self._stats.last_checksum  = checksum
        self._stats.last_sync_ts   = now_ms
        ts_hist = self._stats.sync_ts_history
        ts_hist.append(now_ms)
        if len(ts_hist) > 60:
            ts_hist.pop(0)
        self._stats.total_flushed += 1

        # Clear batch + reset timer
        self._batch.clear()
        self._batch_start_ts = now_ms

        logger.info(
            f"[{self.MODULE}] Flushed batch: reason={reason} "
            f"size={batch_size} anomalies={anomaly_count} checksum={checksum[:8]}"
        )

        return SyncResult(
            flushed=True,
            reason=reason,
            payload_checksum=checksum,
            batch_size=batch_size,
            anomaly_count=anomaly_count,
            path=out_path,
        )

    # ── Payload builder ───────────────────────────────────────────────────────

    def _build_payload(
        self,
        batch: List[_BatchEntry],
        reason: str,
    ) -> Dict[str, Any]:
        """
        Build the compact, token-efficient sync payload from the batch.
        Uses only the latest compressed snapshot for session_summary.
        Aggregates anomalies and delta across the full batch.
        """
        now_ms = int(time.time() * 1000)
        latest = batch[-1].compressed if batch else {}

        # Session summary: latest compressed snapshot (already ≤30 fields)
        session_summary = {
            k: v for k, v in latest.items()
            if not k.startswith("_")
        }

        # Anomaly summary: aggregate across batch, cap per severity
        all_anomalies: List[Dict[str, Any]] = []
        for entry in batch:
            all_anomalies.extend(entry.anomalies)

        worst = _worst_severity(all_anomalies)
        critical_descs = [
            a["description"] for a in all_anomalies
            if a.get("severity") == SEV_CRITICAL
        ][:MAX_ANOMALIES_IN_PAYLOAD]
        high_descs = [
            a["description"] for a in all_anomalies
            if a.get("severity") == SEV_HIGH
        ][:MAX_ANOMALIES_IN_PAYLOAD]

        anomaly_summary = {
            "worst_severity": worst,
            "critical":       critical_descs,
            "high":           high_descs,
            "medium_count":   sum(1 for a in all_anomalies if a.get("severity") == SEV_MEDIUM),
            "low_count":      sum(1 for a in all_anomalies if a.get("severity") == SEV_LOW),
            "total":          len(all_anomalies),
        }

        # Delta summary: highest-significance delta in batch
        best_delta   = max(
            (e.delta_report for e in batch if e.delta_report),
            key=lambda d: d.get("significance_score", 0),
            default=None,
        )
        delta_summary: Dict[str, Any] = {}
        if best_delta:
            delta_summary = {
                "significant_changes": list(best_delta.get("changed_fields", {}).keys()),
                "significance_score":  best_delta.get("significance_score", 0),
                "summary":             best_delta.get("summary", ""),
            }

        # Batch statistics
        period_ms = now_ms - (batch[0].ts if batch else now_ms)
        suppressed_deltas = sum(
            1 for e in batch
            if e.delta_report and not e.delta_report.get("has_meaningful_delta", True)
        )

        return {
            "sync_ts":        now_ms,
            "sync_reason":    reason,
            "session_summary":  session_summary,
            "anomaly_summary":  anomaly_summary,
            "delta_summary":    delta_summary,
            "batch_stats": {
                "snapshots_queued":  len(batch),
                "anomalies_queued":  len(all_anomalies),
                "period_secs":       round(period_ms / 1000.0, 1),
                "suppressed_deltas": suppressed_deltas,
            },
        }

    # ── File writer ───────────────────────────────────────────────────────────

    def _write_sync_file(
        self,
        payload: Dict[str, Any],
        checksum: str,
    ) -> Optional[Path]:
        """Write payload atomically to SYNC_DIR. Returns path or None on error."""
        try:
            from core.observability.report_lifecycle_engine import report_lifecycle_engine
            ts  = payload["sync_ts"]
            dst = SYNC_DIR / f"sync_{checksum[:8]}_{ts}.json"
            ok  = report_lifecycle_engine._write_atomic(dst, payload)
            if ok:
                # Also update latest pointer
                report_lifecycle_engine._write_atomic(SYNC_DIR / "latest_sync.json", payload)
                return dst
            return None
        except Exception as exc:
            logger.warning(f"[{self.MODULE}] _write_sync_file error: {exc}")
            return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _syncs_in_last_hour(self) -> int:
        cutoff = int(time.time() * 1000) - 3_600_000
        return sum(1 for ts in self._stats.sync_ts_history if ts >= cutoff)


# ── Module-level helpers ──────────────────────────────────────────────────────

def _checksum(payload: Dict[str, Any]) -> str:
    """
    Stable SHA-256 of the intelligence content only.
    Excludes volatile metadata (sync_ts, sync_reason, batch_stats)
    so that two flushes with identical data but different reasons/timing
    are correctly identified as duplicates.
    """
    try:
        content_keys = ("session_summary", "anomaly_summary", "delta_summary")
        clean = {k: payload[k] for k in content_keys if k in payload}
        serialized = json.dumps(clean, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    except Exception:
        return ""


_SEV_ORDER = {SEV_CRITICAL: 4, SEV_HIGH: 3, SEV_MEDIUM: 2, SEV_LOW: 1}


def _worst_severity(anomalies: List[Dict[str, Any]]) -> str:
    if not anomalies:
        return "NONE"
    return max(
        (a.get("severity", SEV_LOW) for a in anomalies),
        key=lambda s: _SEV_ORDER.get(s, 0),
        default="NONE",
    )


# ── Module-level singleton ────────────────────────────────────────────────────
github_sync_engine = GitHubSyncEngine()

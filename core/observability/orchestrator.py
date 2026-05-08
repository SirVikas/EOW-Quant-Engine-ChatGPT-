"""
EOW Quant Engine — Observability Orchestrator  (FTD-053-GAIA Phase 6)

Single integration point that runs the full observability pipeline:

  raw snapshot
    → [1] write_raw           (report_lifecycle_engine)
    → [2] compress            (intelligence_compressor)
    → [3] write_compressed    (report_lifecycle_engine, with dedup)
    → [4] delta_report        (delta_reporter)
    → [5] anomaly_scan        (anomaly_detector)
    → [6] ai_summary          (ai_summary_engine)
    → [7] strategic_feeds     (strategic_feed)
    → [8] emit_anomaly_event  (event_bus)
    → [9] escalation          (escalation_engine)
    → [10] auto_resolve       (escalation_engine)
    → [11] queue_snapshot     (github_sync_engine)
    → [12] flush_if_warranted (github_sync_engine)
    → [13] periodic_cleanup   (report_lifecycle_engine, every N ticks)

Design principles:
  • STEP-ISOLATED   — each pipeline step is individually try/except guarded;
                      failure in one step does not abort downstream steps
  • NON-THROWING    — tick() always returns, never propagates
  • READ-ONLY       — zero mutation of any trading engine state
  • THREAD-SAFE     — tick() protected by RLock; safe to call from asyncio.to_thread()
  • SINGLETON       — one orchestrator instance shared across the application
  • FIRE-AND-FORGET — caller does not need to inspect the TickResult

Wiring in main.py:
  from core.observability.orchestrator import obs_orchestrator
  from core.observability.snapshot_builder import build_raw_snapshot

  async def _obs_tick_loop():
      while True:
          await asyncio.sleep(OBS_TICK_INTERVAL_SECS)
          raw = build_raw_snapshot(rl_engine=rl_engine, pnl_calc=pnl_calc, ...)
          await asyncio.to_thread(obs_orchestrator.tick, raw)
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from core.observability.intelligence_compressor import intelligence_compressor
from core.observability.report_lifecycle_engine import report_lifecycle_engine
from core.observability.delta_reporter import delta_reporter
from core.observability.anomaly_detector import anomaly_detector
from core.observability.ai_summary_engine import ai_summary_engine
from core.observability.strategic_feed import strategic_feed
from core.observability.event_bus import event_bus
from core.observability.escalation_engine import escalation_engine
from core.observability.github_sync_engine import github_sync_engine


# ── Governance constants ──────────────────────────────────────────────────────

OBS_TICK_INTERVAL_SECS = 120   # recommended calling interval for the background loop
CLEANUP_EVERY_N_TICKS  = 15    # run report_lifecycle_engine cleanup every N ticks


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class TickResult:
    tick_id:           str
    ts:                int
    compressed:        bool
    deduped:           bool
    delta_score:       float
    anomaly_count:     int
    worst_severity:    str
    escalation_level:  Optional[str]    # None if no escalation fired
    queued_for_sync:   bool
    sync_flushed:      bool
    duration_ms:       int


@dataclass
class OrchestratorStats:
    total_ticks:       int = 0
    total_compressed:  int = 0
    total_deduped:     int = 0
    total_anomalies:   int = 0
    total_escalations: int = 0
    total_syncs:       int = 0
    total_errors:      int = 0
    last_tick_ts:      int = 0
    last_tick_ms:      int = 0     # duration of most recent tick


class ObservabilityOrchestrator:
    """
    Full FTD-053-GAIA pipeline coordinator.
    Call tick(raw_snapshot) from any thread or coroutine (via asyncio.to_thread).
    """

    MODULE  = "OBS_ORCHESTRATOR"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._lock       = threading.RLock()
        self._tick_count = 0
        self._stats      = OrchestratorStats()

    # ── Public API ────────────────────────────────────────────────────────────

    def tick(self, raw_snapshot: Dict[str, Any]) -> Optional[TickResult]:
        """
        Run one complete observability pipeline pass.

        raw_snapshot must be the dict produced by snapshot_builder.build_raw_snapshot().
        Returns TickResult on completion (even partial), None only on catastrophic failure.
        Never raises.
        """
        t0      = time.time()
        tick_id = uuid.uuid4().hex[:8]

        with self._lock:
            self._tick_count += 1
            current_tick = self._tick_count

        # Per-step accumulators
        compressed_snap:   Dict[str, Any]   = {}
        delta:             Dict[str, Any]   = {}
        anomalies:         List[Dict]       = []
        worst_severity:    str              = "NONE"
        escalation_level:  Optional[str]    = None
        deduped:           bool             = False
        compressed_ok:     bool             = False
        queued:            bool             = False
        flushed:           bool             = False

        # ── Step 1: Write raw snapshot ────────────────────────────────────────
        _step("write_raw", lambda: report_lifecycle_engine.write_raw(
            "intelligence", raw_snapshot
        ), self.MODULE)

        # ── Step 2: Compress ──────────────────────────────────────────────────
        compressed_snap = _step(
            "compress",
            lambda: intelligence_compressor.compress(raw_snapshot),
            self.MODULE,
        ) or {}

        # ── Step 3: Write compressed (handles dedup internally) ───────────────
        # Must pass the compressed snapshot (which contains _checksum) not the raw.
        wr = _step(
            "write_compressed",
            lambda: report_lifecycle_engine.write_compressed("intelligence", compressed_snap),
            self.MODULE,
        )
        if wr is not None:
            compressed_ok = wr.success
            deduped       = wr.skipped

        # ── Step 4: Delta report ──────────────────────────────────────────────
        if compressed_snap:
            delta = _step(
                "delta_report",
                lambda: delta_reporter.compute_delta(compressed_snap),
                self.MODULE,
            ) or {}

        # ── Step 5: Anomaly scan ──────────────────────────────────────────────
        if compressed_snap:
            anomalies = _step(
                "anomaly_scan",
                lambda: anomaly_detector.scan(compressed_snap, delta or None),
                self.MODULE,
            ) or []
            worst_severity = _step(
                "anomaly_summary",
                lambda: anomaly_detector.get_active_summary().get("worst_severity", "NONE"),
                self.MODULE,
            ) or "NONE"

        # ── Step 6: AI summary ────────────────────────────────────────────────
        _step(
            "ai_summary",
            lambda: ai_summary_engine.generate_summary(compressed_snap, delta or None, anomalies),
            self.MODULE,
        )

        # ── Step 7: Strategic feeds ───────────────────────────────────────────
        _step(
            "strategic_feeds",
            lambda: strategic_feed.refresh(compressed_snap, anomalies),
            self.MODULE,
        )

        # ── Step 8: Emit anomaly event ────────────────────────────────────────
        if anomalies:
            _step(
                "emit_anomaly",
                lambda: event_bus.emit_anomalies(anomalies, worst_severity, source=self.MODULE),
                self.MODULE,
            )

        # ── Step 9: Escalation evaluate ───────────────────────────────────────
        esc_record = _step(
            "escalation",
            lambda: escalation_engine.evaluate(anomalies, emit_event=True),
            self.MODULE,
        )
        if esc_record is not None:
            escalation_level = esc_record.level

        # ── Step 10: Auto-resolve stale escalations ───────────────────────────
        _step(
            "auto_resolve",
            lambda: escalation_engine.auto_resolve(
                {a.get("category", "") for a in anomalies}
            ),
            self.MODULE,
        )

        # ── Step 11: Queue for sync ───────────────────────────────────────────
        if compressed_snap:
            queued = _step(
                "queue_sync",
                lambda: github_sync_engine.queue_snapshot(
                    compressed_snap, delta or None, anomalies or None
                ),
                self.MODULE,
            ) or False

        # ── Step 12: Flush sync if warranted ──────────────────────────────────
        if _step("should_flush", lambda: github_sync_engine.should_flush(), self.MODULE):
            sync_result = _step(
                "sync_flush",
                lambda: github_sync_engine.flush(),
                self.MODULE,
            )
            if sync_result is not None and sync_result.flushed:
                flushed = True
                _step(
                    "emit_sync_ready",
                    lambda: event_bus.emit_sync_ready({
                        "reason":      sync_result.reason,
                        "checksum":    sync_result.payload_checksum,
                        "batch_size":  sync_result.batch_size,
                    }),
                    self.MODULE,
                )

        # ── Step 13: Periodic cleanup ─────────────────────────────────────────
        if current_tick % CLEANUP_EVERY_N_TICKS == 0:
            _step(
                "cleanup",
                lambda: report_lifecycle_engine.run_cleanup(),
                self.MODULE,
            )

        # ── Build result ──────────────────────────────────────────────────────
        duration_ms = int((time.time() - t0) * 1000)
        result = TickResult(
            tick_id          = tick_id,
            ts               = int(time.time() * 1000),
            compressed       = compressed_ok,
            deduped          = deduped,
            delta_score      = float(delta.get("significance_score", 0.0)),
            anomaly_count    = len(anomalies),
            worst_severity   = worst_severity,
            escalation_level = escalation_level,
            queued_for_sync  = queued,
            sync_flushed     = flushed,
            duration_ms      = duration_ms,
        )

        # ── Update stats ──────────────────────────────────────────────────────
        with self._lock:
            s = self._stats
            s.total_ticks      += 1
            s.last_tick_ts      = result.ts
            s.last_tick_ms      = duration_ms
            if compressed_ok:
                s.total_compressed += 1
            if deduped:
                s.total_deduped    += 1
            s.total_anomalies  += len(anomalies)
            if escalation_level:
                s.total_escalations += 1
            if flushed:
                s.total_syncs      += 1

        logger.debug(
            f"[{self.MODULE}] tick={tick_id} anomalies={len(anomalies)} "
            f"worst={worst_severity} esc={escalation_level} "
            f"sync={'FLUSHED' if flushed else 'queued' if queued else 'none'} "
            f"dt={duration_ms}ms"
        )

        return result

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            s = self._stats
            return {
                "module":            self.MODULE,
                "version":           self.VERSION,
                "total_ticks":       s.total_ticks,
                "total_compressed":  s.total_compressed,
                "total_deduped":     s.total_deduped,
                "total_anomalies":   s.total_anomalies,
                "total_escalations": s.total_escalations,
                "total_syncs":       s.total_syncs,
                "total_errors":      s.total_errors,
                "last_tick_ts":      s.last_tick_ts,
                "last_tick_ms":      s.last_tick_ms,
                "tick_interval_secs": OBS_TICK_INTERVAL_SECS,
                "cleanup_every_n_ticks": CLEANUP_EVERY_N_TICKS,
                # Component status
                "event_bus":          event_bus.status(),
                "escalation_active":  len(escalation_engine.get_active_escalations()),
                "sync_pending":       github_sync_engine.get_pending_payload() is not None,
            }


# ── Helper ────────────────────────────────────────────────────────────────────

def _step(name: str, fn, module: str):
    """Execute a pipeline step. Returns result or None on failure — never raises."""
    try:
        return fn()
    except Exception as exc:
        logger.debug(f"[{module}] step '{name}' error: {exc}")
        return None


# ── Module-level singleton ────────────────────────────────────────────────────
obs_orchestrator = ObservabilityOrchestrator()

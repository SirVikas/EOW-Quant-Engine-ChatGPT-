"""
EOW Quant Engine — Escalation Engine  (FTD-053-GAIA Phase 5)

Severity-driven escalation coordinator. Evaluates anomaly batches, creates
bounded escalation records, supports human acknowledgment, and triggers
event-bus escalation events that downstream subscribers (sync engine, loggers)
can act on — without the escalation engine itself knowing about GitHub or sync.

Design principles:
  • SEVERITY-GATED   — only HIGH/CRITICAL anomalies trigger escalations
  • DEDUP-BOUNDED    — same trigger within DEDUP_WINDOW_SECS is suppressed
  • HUMAN-OVERRIDE   — acknowledge(id) suppresses further escalation for that ID
  • AUTO-RESOLVE     — escalation marked resolved when triggering anomaly clears
  • NON-THROWING     — all public methods catch internally
  • HISTORY-BOUNDED  — max MAX_HISTORY escalation records retained
  • EVENT-COUPLED    — fires event_bus.emit_escalation() on new escalations
  • READ-ONLY        — zero mutation of trading engine state

Escalation levels:
  L1_LOG    — write to log only (1-2 HIGH anomalies)
  L2_RECORD — write escalation file + log (3+ HIGH anomalies)
  L3_SYNC   — trigger immediate sync + write file + log (any CRITICAL anomaly)

Escalation lifecycle:
  ACTIVE     → newly created
  ACKNOWLEDGED → human called acknowledge(); suppressed for ACK_SUPPRESS_SECS
  RESOLVED   → auto_resolve() cleared it (anomaly no longer active)

Deduplication:
  An escalation is suppressed if an identical trigger (same category+metric
  combination from anomalies) fired within DEDUP_WINDOW_SECS.
  Acknowledged escalations are suppressed for ACK_SUPPRESS_SECS regardless of dedup.

Escalation record structure:
  {
    "escalation_id": str,       # 8-char hex
    "level":         str,       # L1_LOG | L2_RECORD | L3_SYNC
    "severity":      str,       # CRITICAL | HIGH
    "trigger":       str,       # human-readable cause
    "description":   str,
    "anomaly_ids":   List[str],
    "anomaly_categories": List[str],
    "ts":            int,       # epoch ms
    "status":        str,       # ACTIVE | ACKNOWLEDGED | RESOLVED
    "ack_reason":    str,
    "resolved_ts":   int,
  }
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW


# ── Escalation levels ─────────────────────────────────────────────────────────

L1_LOG    = "L1_LOG"
L2_RECORD = "L2_RECORD"
L3_SYNC   = "L3_SYNC"

_LEVEL_ORDER = {L3_SYNC: 3, L2_RECORD: 2, L1_LOG: 1}

# ── Lifecycle states ──────────────────────────────────────────────────────────

STATUS_ACTIVE       = "ACTIVE"
STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
STATUS_RESOLVED     = "RESOLVED"

# ── Governance constants ──────────────────────────────────────────────────────

DEDUP_WINDOW_SECS   = 300     # 5 minutes: same trigger suppressed
ACK_SUPPRESS_SECS   = 300     # 5 minutes: ack suppresses re-escalation
HIGH_CLUSTER_THRESH = 3       # 3+ HIGH anomalies → L2_RECORD
MAX_HISTORY         = 100     # escalation records retained

# Output directory
_PROJECT_ROOT    = Path(__file__).resolve().parents[2]
ESCALATION_DIR   = _PROJECT_ROOT / "reports" / "observability" / "escalations"


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class EscalationRecord:
    escalation_id:      str
    level:              str
    severity:           str
    trigger:            str
    description:        str
    anomaly_ids:        List[str]
    anomaly_categories: List[str]
    ts:                 int
    status:             str       = STATUS_ACTIVE
    ack_reason:         str       = ""
    ack_ts:             int       = 0
    resolved_ts:        int       = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id":      self.escalation_id,
            "level":              self.level,
            "severity":           self.severity,
            "trigger":            self.trigger,
            "description":        self.description,
            "anomaly_ids":        self.anomaly_ids,
            "anomaly_categories": self.anomaly_categories,
            "ts":                 self.ts,
            "status":             self.status,
            "ack_reason":         self.ack_reason,
            "ack_ts":             self.ack_ts,
            "resolved_ts":        self.resolved_ts,
        }


@dataclass
class EscalationStats:
    total_evaluated:  int = 0
    total_escalated:  int = 0
    total_suppressed: int = 0
    total_acked:      int = 0
    total_resolved:   int = 0
    l1_count:         int = 0
    l2_count:         int = 0
    l3_count:         int = 0
    last_escalation_ts: int = 0


class EscalationEngine:
    """
    Severity-driven escalation coordinator.
    Emits escalation events through the event bus when new escalations fire.
    """

    MODULE  = "ESCALATION_ENGINE"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._history: List[EscalationRecord] = []
        self._stats    = EscalationStats()
        self._trigger_ts: Dict[str, int] = {}   # trigger_key → last_escalation_ts
        ESCALATION_DIR.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        anomalies: List[Dict[str, Any]],
        emit_event: bool = True,
    ) -> Optional[EscalationRecord]:
        """
        Evaluate an anomaly list and create an escalation if warranted.

        Returns the new EscalationRecord, or None if suppressed/not warranted.
        If emit_event=True, fires event_bus.emit_escalation() on new escalation.
        Never raises.
        """
        try:
            self._stats.total_evaluated += 1

            if not anomalies:
                return None

            # Classify anomalies by severity
            criticals = [a for a in anomalies if a.get("severity") == SEV_CRITICAL]
            highs     = [a for a in anomalies if a.get("severity") == SEV_HIGH]

            if not criticals and not highs:
                return None   # MEDIUM/LOW only — no escalation

            # Determine level and anchor anomalies
            if criticals:
                level    = L3_SYNC
                severity = SEV_CRITICAL
                anchors  = criticals
            elif len(highs) >= HIGH_CLUSTER_THRESH:
                level    = L2_RECORD
                severity = SEV_HIGH
                anchors  = highs
            else:
                level    = L1_LOG
                severity = SEV_HIGH
                anchors  = highs

            # Build trigger key (stable fingerprint of categories+metrics)
            trigger_key = _trigger_key(anchors)

            # Dedup check
            if self._is_deduped(trigger_key):
                self._stats.total_suppressed += 1
                logger.debug(
                    f"[{self.MODULE}] Escalation suppressed (dedup): {trigger_key[:16]}"
                )
                return None

            # Build record
            trigger_desc = _trigger_description(anchors, severity)
            description  = _build_description(anchors, level)
            esc_id       = _escalation_id(trigger_key, int(time.time() * 1000))

            record = EscalationRecord(
                escalation_id      = esc_id,
                level              = level,
                severity           = severity,
                trigger            = trigger_desc,
                description        = description,
                anomaly_ids        = [a.get("anomaly_id", "") for a in anchors],
                anomaly_categories = list({a.get("category", "") for a in anchors}),
                ts                 = int(time.time() * 1000),
            )

            # Persist and log
            self._store(record)
            self._write_record(record)
            self._log_escalation(record)

            # Update dedup tracker
            self._trigger_ts[trigger_key] = int(time.time() * 1000)

            # Emit event bus event
            if emit_event:
                self._emit(record)

            # Update stats
            self._stats.total_escalated     += 1
            self._stats.last_escalation_ts   = record.ts
            if level == L1_LOG:
                self._stats.l1_count += 1
            elif level == L2_RECORD:
                self._stats.l2_count += 1
            else:
                self._stats.l3_count += 1

            return record

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] evaluate error: {exc}")
            return None

    def acknowledge(self, escalation_id: str, reason: str = "") -> bool:
        """
        Human override: mark an escalation as acknowledged.
        Suppresses re-escalation for the same trigger for ACK_SUPPRESS_SECS.
        Returns True if found and acknowledged.
        """
        try:
            for rec in reversed(self._history):
                if rec.escalation_id == escalation_id:
                    if rec.status == STATUS_ACTIVE:
                        rec.status     = STATUS_ACKNOWLEDGED
                        rec.ack_reason = reason or "acknowledged"
                        rec.ack_ts     = int(time.time() * 1000)
                        self._stats.total_acked += 1
                        # Extend dedup window to ACK_SUPPRESS_SECS
                        tkey = _trigger_key_from_record(rec)
                        self._trigger_ts[tkey] = int(time.time() * 1000) + (
                            (ACK_SUPPRESS_SECS - DEDUP_WINDOW_SECS) * 1000
                        )
                        logger.info(
                            f"[{self.MODULE}] Escalation acknowledged: {escalation_id} | {reason}"
                        )
                        return True
            return False
        except Exception as exc:
            logger.warning(f"[{self.MODULE}] acknowledge error: {exc}")
            return False

    def auto_resolve(self, current_anomaly_categories: Set[str]) -> List[str]:
        """
        Mark active escalations as RESOLVED if their triggering anomaly categories
        are no longer present in the current anomaly set.
        Returns list of resolved escalation IDs.
        """
        resolved_ids: List[str] = []
        try:
            now_ms = int(time.time() * 1000)
            for rec in self._history:
                if rec.status != STATUS_ACTIVE:
                    continue
                # Resolved if none of the escalation's categories are still active
                still_active = any(
                    cat in current_anomaly_categories
                    for cat in rec.anomaly_categories
                )
                if not still_active:
                    rec.status      = STATUS_RESOLVED
                    rec.resolved_ts = now_ms
                    resolved_ids.append(rec.escalation_id)
                    self._stats.total_resolved += 1
                    logger.info(
                        f"[{self.MODULE}] Escalation auto-resolved: {rec.escalation_id}"
                    )
        except Exception as exc:
            logger.warning(f"[{self.MODULE}] auto_resolve error: {exc}")
        return resolved_ids

    def get_active_escalations(self) -> List[Dict[str, Any]]:
        """Return all ACTIVE escalation records as dicts."""
        return [r.to_dict() for r in self._history if r.status == STATUS_ACTIVE]

    def get_history(
        self,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return recent escalation history, optionally filtered by status."""
        records = reversed(self._history)
        if status:
            records = (r for r in records if r.status == status)  # type: ignore[assignment]
        return [r.to_dict() for r in list(records)[:limit]]

    def stats(self) -> Dict[str, Any]:
        s = self._stats
        return {
            "module":             self.MODULE,
            "version":            self.VERSION,
            "total_evaluated":    s.total_evaluated,
            "total_escalated":    s.total_escalated,
            "total_suppressed":   s.total_suppressed,
            "total_acked":        s.total_acked,
            "total_resolved":     s.total_resolved,
            "l1_count":           s.l1_count,
            "l2_count":           s.l2_count,
            "l3_count":           s.l3_count,
            "active_count":       len(self.get_active_escalations()),
            "last_escalation_ts": s.last_escalation_ts,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _is_deduped(self, trigger_key: str) -> bool:
        last_ts = self._trigger_ts.get(trigger_key, 0)
        if last_ts == 0:
            return False
        elapsed_ms = int(time.time() * 1000) - last_ts
        return elapsed_ms < (DEDUP_WINDOW_SECS * 1000)

    def _store(self, record: EscalationRecord) -> None:
        self._history.append(record)
        if len(self._history) > MAX_HISTORY:
            self._history = self._history[-MAX_HISTORY:]

    def _write_record(self, record: EscalationRecord) -> None:
        """Write escalation record atomically. L2/L3 only."""
        if record.level == L1_LOG:
            return
        try:
            from core.observability.report_lifecycle_engine import report_lifecycle_engine
            dst = ESCALATION_DIR / f"esc_{record.escalation_id}_{record.ts}.json"
            report_lifecycle_engine._write_atomic(dst, record.to_dict())
            # Update latest
            report_lifecycle_engine._write_atomic(
                ESCALATION_DIR / "latest_escalation.json",
                record.to_dict(),
            )
        except Exception as exc:
            logger.debug(f"[{self.MODULE}] _write_record error: {exc}")

    def _log_escalation(self, record: EscalationRecord) -> None:
        msg = (
            f"[{self.MODULE}] {record.level} | {record.severity} | "
            f"{record.trigger} | id={record.escalation_id}"
        )
        if record.level == L3_SYNC:
            logger.warning(msg)
        elif record.level == L2_RECORD:
            logger.info(msg)
        else:
            logger.debug(msg)

    def _emit(self, record: EscalationRecord) -> None:
        """Fire escalation event — import lazily to avoid circular imports."""
        try:
            from core.observability.event_bus import event_bus
            event_bus.emit_escalation(record.to_dict())
        except Exception as exc:
            logger.debug(f"[{self.MODULE}] event emit error: {exc}")


# ── Helper functions ──────────────────────────────────────────────────────────

def _trigger_key(anomalies: List[Dict[str, Any]]) -> str:
    """Stable fingerprint from sorted category+metric pairs."""
    pairs = sorted(
        f"{a.get('category','')}:{a.get('metric','')}"
        for a in anomalies
    )
    raw = "|".join(pairs)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _trigger_key_from_record(rec: EscalationRecord) -> str:
    """Reconstruct trigger key from a record's categories (approximate)."""
    raw = "|".join(sorted(rec.anomaly_categories))
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _trigger_description(anomalies: List[Dict[str, Any]], severity: str) -> str:
    cats = sorted({a.get("category", "UNKNOWN") for a in anomalies})
    return f"{severity}: {', '.join(cats)}"


def _build_description(anomalies: List[Dict[str, Any]], level: str) -> str:
    descs = [a.get("description", "") for a in anomalies[:3]]
    base  = " | ".join(d for d in descs if d)
    return f"[{level}] {base}" if base else f"[{level}] {len(anomalies)} anomaly(ies)"


def _escalation_id(trigger_key: str, ts_ms: int) -> str:
    minute = ts_ms // 60_000
    raw    = f"{trigger_key}:{minute}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]


# ── Module-level singleton ────────────────────────────────────────────────────
escalation_engine = EscalationEngine()

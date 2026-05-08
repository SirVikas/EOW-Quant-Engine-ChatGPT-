"""
EOW Quant Engine — Event Bus  (FTD-053-GAIA Phase 5)

Lightweight in-process pub/sub event bus for decoupled observability coordination.
Wires Phase 1-4 outputs into event-driven flows without creating hard module
dependencies between compression, anomaly detection, escalation, and sync.

Design principles:
  • SYNCHRONOUS    — handlers called in-process; no threads, no asyncio tasks
  • FIRE-AND-FORGET — publisher never receives handler return values
  • FAULT-ISOLATED — handler exceptions caught and logged; never propagate to publisher
  • BOUNDED        — max MAX_SUBSCRIBERS_PER_CHANNEL subscribers; max MAX_QUEUE_DEPTH events logged
  • THREAD-SAFE    — RLock guards all state mutations
  • NON-BLOCKING   — emit() completes in microseconds even if handlers are slow (bounded time)
  • GOVERNANCE     — per-channel event counters for observability

Named channels:
  CHANNEL_ANOMALY     — emitted when anomaly_detector.scan() returns events
  CHANNEL_ESCALATION  — emitted when escalation_engine fires a new escalation
  CHANNEL_SYNC_READY  — emitted when github_sync_engine flushes a batch
  CHANNEL_FEED_UPDATE — emitted when strategic_feed.refresh() completes
  CHANNEL_SUMMARY     — emitted when ai_summary_engine.generate_summary() completes

Event payload convention:
  Every payload is a plain Dict. Channel-specific schemas are documented per channel.
  A "_channel" and "_emit_ts" key are always injected by the bus.

Usage:
  from core.observability.event_bus import event_bus, CHANNEL_ANOMALY

  # Subscribe
  sub_id = event_bus.subscribe(CHANNEL_ANOMALY, my_handler)

  # Emit (from anomaly detection code)
  event_bus.emit(CHANNEL_ANOMALY, {"anomalies": anomaly_list, "worst": "CRITICAL"})

  # Unsubscribe
  event_bus.unsubscribe(sub_id)
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


# ── Channel names ─────────────────────────────────────────────────────────────

CHANNEL_ANOMALY     = "ANOMALY"
CHANNEL_ESCALATION  = "ESCALATION"
CHANNEL_SYNC_READY  = "SYNC_READY"
CHANNEL_FEED_UPDATE = "FEED_UPDATE"
CHANNEL_SUMMARY     = "SUMMARY"

ALL_CHANNELS = (
    CHANNEL_ANOMALY,
    CHANNEL_ESCALATION,
    CHANNEL_SYNC_READY,
    CHANNEL_FEED_UPDATE,
    CHANNEL_SUMMARY,
)

# ── Governance ────────────────────────────────────────────────────────────────

MAX_SUBSCRIBERS_PER_CHANNEL = 20
MAX_QUEUE_DEPTH             = 500    # recent event log entries kept in memory
MAX_HANDLER_LOG_ERRORS      = 50     # stop logging handler errors after this many


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Subscription:
    sub_id:  str
    channel: str
    handler: Callable[[Dict[str, Any]], None]
    ts:      int


@dataclass
class EventRecord:
    channel:       str
    payload_keys:  List[str]     # key names only (not values — avoid memory bloat)
    handler_count: int
    handler_errors:int
    ts:            int


@dataclass
class BusStats:
    total_emitted:      int = 0
    total_handler_calls:int = 0
    total_handler_errors:int = 0
    total_subscriptions:int = 0
    per_channel:        Dict[str, int] = field(default_factory=dict)


class EventBus:
    """
    In-process publish/subscribe event bus. Thread-safe, synchronous dispatch.
    """

    MODULE  = "EVENT_BUS"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._lock          = threading.RLock()
        self._subs:         Dict[str, Subscription] = {}          # sub_id → Subscription
        self._channel_subs: Dict[str, List[str]]    = {           # channel → [sub_ids]
            ch: [] for ch in ALL_CHANNELS
        }
        self._recent_events: List[EventRecord] = []
        self._stats          = BusStats()
        self._handler_error_count = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def subscribe(
        self,
        channel: str,
        handler: Callable[[Dict[str, Any]], None],
    ) -> str:
        """
        Register a handler for a named channel.
        Returns a subscription ID for later unsubscription.
        Raises ValueError if channel unknown or subscriber cap reached.
        """
        with self._lock:
            if channel not in ALL_CHANNELS:
                raise ValueError(f"Unknown channel: {channel!r}. Valid: {ALL_CHANNELS}")

            subs_for_channel = self._channel_subs[channel]
            if len(subs_for_channel) >= MAX_SUBSCRIBERS_PER_CHANNEL:
                raise ValueError(
                    f"Channel {channel!r} at subscriber cap ({MAX_SUBSCRIBERS_PER_CHANNEL})"
                )

            sub_id = uuid.uuid4().hex[:12]
            sub = Subscription(
                sub_id=sub_id,
                channel=channel,
                handler=handler,
                ts=int(time.time() * 1000),
            )
            self._subs[sub_id] = sub
            subs_for_channel.append(sub_id)
            self._stats.total_subscriptions += 1

            logger.debug(f"[{self.MODULE}] Subscribed {sub_id} to {channel}")
            return sub_id

    def unsubscribe(self, sub_id: str) -> bool:
        """
        Remove a subscription. Returns True if found and removed, False otherwise.
        """
        with self._lock:
            sub = self._subs.pop(sub_id, None)
            if sub is None:
                return False
            ch_list = self._channel_subs.get(sub.channel, [])
            if sub_id in ch_list:
                ch_list.remove(sub_id)
            logger.debug(f"[{self.MODULE}] Unsubscribed {sub_id} from {sub.channel}")
            return True

    def emit(
        self,
        channel: str,
        payload: Dict[str, Any],
    ) -> int:
        """
        Emit an event to all subscribers of the named channel.
        Injects _channel and _emit_ts into payload copy before dispatch.
        Returns number of handlers successfully called.
        Never raises — handler failures are caught and logged.
        """
        try:
            with self._lock:
                if channel not in ALL_CHANNELS:
                    logger.warning(f"[{self.MODULE}] emit to unknown channel {channel!r}")
                    return 0

                sub_ids  = list(self._channel_subs.get(channel, []))
                handlers = [
                    self._subs[sid].handler
                    for sid in sub_ids
                    if sid in self._subs
                ]

            if not handlers:
                return 0

            # Inject bus metadata without mutating caller's dict
            enriched = dict(payload)
            enriched["_channel"]  = channel
            enriched["_emit_ts"]  = int(time.time() * 1000)

            called = errors = 0
            for handler in handlers:
                try:
                    handler(enriched)
                    called += 1
                except Exception as exc:
                    errors += 1
                    self._handler_error_count += 1
                    if self._handler_error_count <= MAX_HANDLER_LOG_ERRORS:
                        logger.warning(
                            f"[{self.MODULE}] Handler error on {channel}: {exc}"
                        )

            with self._lock:
                self._stats.total_emitted       += 1
                self._stats.total_handler_calls += called
                self._stats.total_handler_errors += errors
                self._stats.per_channel[channel] = (
                    self._stats.per_channel.get(channel, 0) + 1
                )
                # Log recent event (keys only, not values)
                self._recent_events.append(EventRecord(
                    channel=channel,
                    payload_keys=list(payload.keys()),
                    handler_count=called,
                    handler_errors=errors,
                    ts=enriched["_emit_ts"],
                ))
                if len(self._recent_events) > MAX_QUEUE_DEPTH:
                    self._recent_events.pop(0)

            return called

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] emit error: {exc}")
            return 0

    def emit_anomalies(
        self,
        anomalies: List[Dict[str, Any]],
        worst_severity: str = "NONE",
        source: str = "",
    ) -> int:
        """
        Convenience wrapper: emit to CHANNEL_ANOMALY.
        """
        return self.emit(CHANNEL_ANOMALY, {
            "anomalies":      anomalies,
            "anomaly_count":  len(anomalies),
            "worst_severity": worst_severity,
            "source":         source,
        })

    def emit_escalation(self, escalation: Dict[str, Any]) -> int:
        """Convenience wrapper: emit to CHANNEL_ESCALATION."""
        return self.emit(CHANNEL_ESCALATION, escalation)

    def emit_sync_ready(self, sync_result: Dict[str, Any]) -> int:
        """Convenience wrapper: emit to CHANNEL_SYNC_READY."""
        return self.emit(CHANNEL_SYNC_READY, sync_result)

    def emit_feed_update(self, feed_snapshot: Dict[str, Any]) -> int:
        """Convenience wrapper: emit to CHANNEL_FEED_UPDATE."""
        return self.emit(CHANNEL_FEED_UPDATE, feed_snapshot)

    def emit_summary(self, summary: Dict[str, Any]) -> int:
        """Convenience wrapper: emit to CHANNEL_SUMMARY."""
        return self.emit(CHANNEL_SUMMARY, summary)

    # ── Introspection ─────────────────────────────────────────────────────────

    def subscriber_count(self, channel: str) -> int:
        with self._lock:
            return len(self._channel_subs.get(channel, []))

    def recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "channel":       e.channel,
                    "payload_keys":  e.payload_keys,
                    "handler_count": e.handler_count,
                    "handler_errors":e.handler_errors,
                    "ts":            e.ts,
                }
                for e in self._recent_events[-limit:]
            ]

    def status(self) -> Dict[str, Any]:
        """Full bus status — safe to call from any context."""
        try:
            with self._lock:
                s = self._stats
                return {
                    "module":               self.MODULE,
                    "version":              self.VERSION,
                    "channels":             list(ALL_CHANNELS),
                    "subscribers": {
                        ch: len(self._channel_subs.get(ch, []))
                        for ch in ALL_CHANNELS
                    },
                    "stats": {
                        "total_emitted":       s.total_emitted,
                        "total_handler_calls": s.total_handler_calls,
                        "total_handler_errors":s.total_handler_errors,
                        "total_subscriptions": s.total_subscriptions,
                        "per_channel":         dict(s.per_channel),
                    },
                    "recent_event_count": len(self._recent_events),
                    "handler_error_count":self._handler_error_count,
                }
        except Exception as exc:
            return {"module": self.MODULE, "error": str(exc)}


# ── Module-level singleton ────────────────────────────────────────────────────
event_bus = EventBus()

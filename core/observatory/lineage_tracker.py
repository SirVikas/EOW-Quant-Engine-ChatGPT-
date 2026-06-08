"""
PHOENIX OBSERVATORY-X — Event Lineage Tracker  [OX-2B]

Traces the complete causal chain for any PHOENIX event (trade, loss, regime
change, anomaly, escalation).  For a given event it answers:

  Signal → Regime → Risk Approval → Execution → Outcome

Each lineage record is an ordered list of LineageNode entries, one per causal
step.  Nodes carry:
  - step label and actor (which module/engine took the action)
  - timestamp of the step
  - any associated report key (links back to the registry)
  - free-form metadata (parameters, scores, reasons)

Design principles
─────────────────
  • Append-only per event_id — no mutation after recording
  • Thread-safe via RLock
  • Bounded in-memory buffer (MAX_EVENTS); oldest evicted when full
  • Any module can submit a lineage step; the tracker assembles the chain

Typical callers:
  - main.py tick handler (trade entry/exit)
  - risk_engine (approval / rejection)
  - regime_detector (regime change)
  - observability escalation_engine (escalation events)
  - loss attribution path
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


MAX_EVENTS = 500   # maximum events kept in memory


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class LineageNode:
    step: int                        # Ordinal position in the chain (0-based)
    label: str                       # Human-readable step name, e.g. "Signal Generated"
    actor: str                       # Module/engine responsible, e.g. "strategy_engine"
    timestamp: float                 # epoch
    report_key: Optional[str] = None # Registry key of the related report (if any)
    outcome: str = ""                # "ok" | "rejected" | "warning" | "loss" | ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventLineage:
    event_id: str
    event_type: str                  # trade | loss | regime_change | anomaly | escalation | custom
    created_at: float
    description: str = ""
    nodes: List[LineageNode] = field(default_factory=list)
    resolved: bool = False           # True when the event chain is complete
    final_outcome: str = ""          # e.g. "win" | "loss" | "blocked" | "escalated"


# ── Tracker ───────────────────────────────────────────────────────────────────

class EventLineageTracker:
    """
    Central lineage store.  Any part of PHOENIX can open a lineage event,
    append steps to it, and close it.  Observatory health endpoints expose
    the full lineage for forensic investigation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # Ordered so we can evict oldest on overflow
        self._events: OrderedDict[str, EventLineage] = OrderedDict()

    # ── Event Lifecycle ───────────────────────────────────────────────────────

    def open_event(
        self,
        event_id: str,
        event_type: str,
        description: str = "",
    ) -> EventLineage:
        """
        Start tracking a new event.  If event_id already exists, returns the
        existing event (idempotent open).
        """
        with self._lock:
            if event_id in self._events:
                return self._events[event_id]
            if len(self._events) >= MAX_EVENTS:
                # evict oldest
                self._events.popitem(last=False)
            evt = EventLineage(
                event_id=event_id,
                event_type=event_type,
                created_at=time.time(),
                description=description,
            )
            self._events[event_id] = evt
            return evt

    def append_step(
        self,
        event_id: str,
        label: str,
        actor: str,
        outcome: str = "",
        report_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append a causal step to an existing event lineage.
        If the event doesn't exist yet, it is auto-opened as type "custom".
        """
        with self._lock:
            if event_id not in self._events:
                self.open_event(event_id, "custom")
            evt = self._events[event_id]
            node = LineageNode(
                step=len(evt.nodes),
                label=label,
                actor=actor,
                timestamp=time.time(),
                outcome=outcome,
                report_key=report_key,
                metadata=metadata or {},
            )
            evt.nodes.append(node)

    def close_event(
        self,
        event_id: str,
        final_outcome: str = "",
    ) -> None:
        """Mark an event as resolved with a final outcome."""
        with self._lock:
            evt = self._events.get(event_id)
            if evt:
                evt.resolved = True
                evt.final_outcome = final_outcome

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_lineage(self, event_id: str) -> Optional[dict]:
        with self._lock:
            evt = self._events.get(event_id)
        if not evt:
            return None
        return self._serialise(evt)

    def recent(self, limit: int = 20, event_type: Optional[str] = None) -> List[dict]:
        with self._lock:
            evts = list(reversed(list(self._events.values())))
        if event_type:
            evts = [e for e in evts if e.event_type == event_type]
        return [self._serialise(e) for e in evts[:limit]]

    def losses(self, limit: int = 50) -> List[dict]:
        """Return lineage for loss events — key forensic view."""
        with self._lock:
            evts = [
                e for e in reversed(list(self._events.values()))
                if e.event_type in ("loss", "trade") and e.final_outcome == "loss"
            ]
        return [self._serialise(e) for e in evts[:limit]]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._events)
            by_type: Dict[str, int] = {}
            by_outcome: Dict[str, int] = {}
            open_count = 0
            for evt in self._events.values():
                by_type[evt.event_type] = by_type.get(evt.event_type, 0) + 1
                if evt.final_outcome:
                    by_outcome[evt.final_outcome] = by_outcome.get(evt.final_outcome, 0) + 1
                if not evt.resolved:
                    open_count += 1
        return {
            "total_events":    total,
            "open_events":     open_count,
            "by_type":         by_type,
            "by_final_outcome": by_outcome,
            "buffer_capacity": MAX_EVENTS,
            "buffer_pct_used": round(total / MAX_EVENTS * 100, 1),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _serialise(evt: EventLineage) -> dict:
        return {
            "event_id":      evt.event_id,
            "event_type":    evt.event_type,
            "created_at":    evt.created_at,
            "description":   evt.description,
            "resolved":      evt.resolved,
            "final_outcome": evt.final_outcome,
            "step_count":    len(evt.nodes),
            "nodes": [
                {
                    "step":       n.step,
                    "label":      n.label,
                    "actor":      n.actor,
                    "timestamp":  n.timestamp,
                    "outcome":    n.outcome,
                    "report_key": n.report_key,
                    "metadata":   n.metadata,
                }
                for n in evt.nodes
            ],
        }


# Singleton
event_lineage_tracker = EventLineageTracker()

"""
PHOENIX CORTEX — Governance Replay Engine  [CX-GAP-03]

Governance Explainability: the ability to reconstruct exactly why a decision
was made, when it was made, and what state the system was in at the time.

The Replay Engine records every governance decision event with its full context,
then provides timeline reconstruction on demand.

Decision types tracked:
  TRADE_BLOCKED          — pre-trade gate blocked an entry
  RECOMMENDATION_REJECTED — human rejected a recommendation
  OVERRIDE_DENIED        — override request was denied
  CONSTITUTIONAL_BLOCK   — article enforcement blocked an action
  SAFE_MODE_TRIGGERED    — safe mode activated
  INVESTIGATION_OPENED   — investigation started
  BLAME_ATTRIBUTED       — primary blame assigned
  WEIGHT_CHANGE_BLOCKED  — influence weight change blocked

Each event records: timestamp, actor, action attempted, decision, articles
cited, trust state at time of decision, and resolution.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

MAX_EVENTS = 2000


@dataclass
class GovernanceEvent:
    event_id: str
    event_type: str              # one of the types above
    actor: str                   # who/what triggered this event
    action_attempted: str        # what was being attempted
    decision: str                # BLOCKED | APPROVED | DENIED | TRIGGERED | OPENED | ATTRIBUTED
    decision_authority: str      # what made the decision (article, module, human)
    articles_cited: List[str]    # constitutional articles cited
    trust_score_at_time: float   # recommendation trust score if applicable
    context: Dict[str, Any]      # additional structured context
    reason: str                  # human-readable reason
    resolution: str              # what happened next
    timestamp: float = field(default_factory=time.time)


class GovernanceReplayEngine:
    """
    Records governance decisions and provides timeline reconstruction.
    Answers: "Why was trade #481 blocked?" or "Why was recommendation rejected?"
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: Deque[GovernanceEvent] = deque(maxlen=MAX_EVENTS)
        self._event_index: Dict[str, GovernanceEvent] = {}  # event_id → event

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(
        self,
        event_type: str,
        actor: str,
        action_attempted: str,
        decision: str,
        reason: str,
        decision_authority: str = "system",
        articles_cited: Optional[List[str]] = None,
        trust_score_at_time: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
        resolution: str = "",
    ) -> GovernanceEvent:
        event_id = f"GEV_{int(time.time() * 1000)}_{event_type[:6]}"
        evt = GovernanceEvent(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            action_attempted=action_attempted,
            decision=decision,
            decision_authority=decision_authority,
            articles_cited=articles_cited or [],
            trust_score_at_time=trust_score_at_time,
            context=context or {},
            reason=reason,
            resolution=resolution,
        )
        with self._lock:
            self._events.append(evt)
            self._event_index[event_id] = evt
        return evt

    # ── Replay ────────────────────────────────────────────────────────────────

    def replay_for_trade(self, trade_id: str, window_seconds: float = 300.0) -> List[dict]:
        """
        Reconstruct governance decisions that occurred around a specific trade.
        Searches for trade_id in event context fields.
        """
        with self._lock:
            events = list(self._events)
        matches = [
            e for e in events
            if str(trade_id) in str(e.context) or str(trade_id) in e.actor or str(trade_id) in e.action_attempted
        ]
        return [self._serialise(e) for e in sorted(matches, key=lambda x: x.timestamp)]

    def replay_for_recommendation(self, rec_id: str) -> List[dict]:
        with self._lock:
            events = list(self._events)
        matches = [
            e for e in events
            if str(rec_id) in str(e.context) or str(rec_id) in e.action_attempted
        ]
        return [self._serialise(e) for e in sorted(matches, key=lambda x: x.timestamp)]

    def replay_timeline(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[dict]:
        """General timeline replay with optional filters."""
        with self._lock:
            events = list(self._events)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if actor:
            events = [e for e in events if actor.lower() in e.actor.lower()]
        if since:
            events = [e for e in events if e.timestamp >= since]
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return [self._serialise(e) for e in events[:limit]]

    def get_event(self, event_id: str) -> Optional[dict]:
        with self._lock:
            e = self._event_index.get(event_id)
        return self._serialise(e) if e else None

    def summary(self) -> dict:
        with self._lock:
            events = list(self._events)
        by_type: Dict[str, int] = {}
        by_decision: Dict[str, int] = {}
        for e in events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
            by_decision[e.decision] = by_decision.get(e.decision, 0) + 1
        return {
            "total_events":   len(events),
            "by_type":        by_type,
            "by_decision":    by_decision,
            "max_capacity":   MAX_EVENTS,
            "oldest_event":   events[0].timestamp if events else None,
            "newest_event":   events[-1].timestamp if events else None,
        }

    @staticmethod
    def _serialise(e: GovernanceEvent) -> dict:
        return {
            "event_id":            e.event_id,
            "event_type":          e.event_type,
            "actor":               e.actor,
            "action_attempted":    e.action_attempted,
            "decision":            e.decision,
            "decision_authority":  e.decision_authority,
            "articles_cited":      e.articles_cited,
            "trust_score_at_time": e.trust_score_at_time,
            "reason":              e.reason,
            "resolution":          e.resolution,
            "context":             e.context,
            "timestamp":           e.timestamp,
        }


# Singleton
governance_replay_engine = GovernanceReplayEngine()

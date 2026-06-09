"""
PHOENIX Constitution — Change History
Records all constitutional events: validations, amendments, violations.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List
import uuid


@dataclass
class ConstitutionalEvent:
    event_id: str
    event_type: str  # VALIDATION/AMENDMENT_PROPOSED/AMENDMENT_APPLIED/VIOLATION_DETECTED
    article_id: str
    description: str
    actor: str
    timestamp: str


class ChangeHistory:
    def __init__(self):
        self._lock = threading.RLock()
        self._events: List[ConstitutionalEvent] = []

    def record(
        self,
        event_type: str,
        article_id: str,
        description: str,
        actor: str = "SYSTEM",
    ) -> dict:
        event = ConstitutionalEvent(
            event_id=f"CE-{uuid.uuid4().hex[:8].upper()}",
            event_type=event_type,
            article_id=article_id,
            description=description,
            actor=actor,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._events.append(event)
        return asdict(event)

    def violations(self, limit: int = 50) -> list:
        with self._lock:
            items = [e for e in self._events if e.event_type == "VIOLATION_DETECTED"]
        return [asdict(e) for e in items[-limit:]]

    def amendment_proposals(self) -> list:
        with self._lock:
            items = [e for e in self._events if e.event_type == "AMENDMENT_PROPOSED"]
        return [asdict(e) for e in items]

    def history_stats(self) -> dict:
        with self._lock:
            events = list(self._events)
        violations = [e for e in events if e.event_type == "VIOLATION_DETECTED"]
        amendments = [e for e in events if e.event_type == "AMENDMENT_PROPOSED"]
        last_v = violations[-1].timestamp if violations else None
        return {
            "total_events": len(events),
            "violations_count": len(violations),
            "amendments_proposed": len(amendments),
            "last_violation_at": last_v,
        }


change_history = ChangeHistory()

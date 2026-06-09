"""
PHOENIX CORTEX — Constitutional Change History  [CORTEX-CHANGE-HISTORY-01]

Records every constitutional event in chronological order:
  - Article additions / modifications
  - Amendment lifecycle events (PROPOSED → ENACTED)
  - Court rulings
  - Case law additions / overrulings
  - Simulation results (RECOMMEND / CAUTION / VETO)
  - Governance replay checkpoints

Provides full audit trail for any constitutional change at any point in time.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


MAX_HISTORY_EVENTS = 5000

CHANGE_TYPES = {
    "ARTICLE_ADDED",
    "ARTICLE_MODIFIED",
    "AMENDMENT_PROPOSED",
    "AMENDMENT_REVIEWED",
    "AMENDMENT_VOTED",
    "AMENDMENT_RATIFIED",
    "AMENDMENT_ENACTED",
    "AMENDMENT_REJECTED",
    "COURT_CASE_FILED",
    "COURT_RULING_ISSUED",
    "CASE_LAW_RECORDED",
    "CASE_LAW_OVERRULED",
    "SIMULATION_RUN",
    "VIOLATION_RECORDED",
    "PRECEDENT_CITED",
}


@dataclass
class ConstitutionalChangeEvent:
    event_id: str
    change_type: str
    subject_id: str          # article id, amendment id, case id, etc.
    summary: str
    actor: str               # "SYSTEM", "HUMAN:<name>", "AEG", etc.
    detail: dict = field(default_factory=dict)
    recorded_at: float = field(default_factory=time.time)


class ConstitutionalHistory:
    """
    Full audit log of all constitutional changes across CORTEX governance modules.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: List[ConstitutionalChangeEvent] = []
        self._seed_founding_events()

    def _seed_founding_events(self) -> None:
        founding = [
            ("ARTICLE_ADDED", "ARTICLE-001", "CONSTITUTION", "ARTICLE-001 (Risk Primacy) enacted at constitutional founding"),
            ("ARTICLE_ADDED", "ARTICLE-002", "CONSTITUTION", "ARTICLE-002 (Evidence Standard) enacted at constitutional founding"),
            ("ARTICLE_ADDED", "ARTICLE-003", "CONSTITUTION", "ARTICLE-003 (Counterfactual Requirement) enacted at constitutional founding"),
            ("ARTICLE_ADDED", "ARTICLE-004", "CONSTITUTION", "ARTICLE-004 (Scope Limitation) enacted at constitutional founding"),
            ("CASE_LAW_RECORDED", "CL-FOUNDING-001", "SYSTEM", "CL-FOUNDING-001 founding case law established"),
            ("COURT_CASE_FILED", "COURT-FOUNDING-001", "SYSTEM", "COURT-FOUNDING-001: ARTICLE-001 vs ARTICLE-004 scope delimitation — founding case"),
            ("COURT_RULING_ISSUED", "COURT-FOUNDING-001", "SYSTEM", "COURT-FOUNDING-001 resolved: ARTICLE-004 scope limits observatory, not governance"),
        ]
        for change_type, subject_id, actor, summary in founding:
            ev = ConstitutionalChangeEvent(
                event_id=f"CH-FOUNDING-{len(self._events)+1:03d}",
                change_type=change_type,
                subject_id=subject_id,
                summary=summary,
                actor=actor,
                recorded_at=time.time() - 86400 * 365,  # dated 1 year ago as founding
            )
            self._events.append(ev)

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(
        self,
        change_type: str,
        subject_id: str,
        summary: str,
        actor: str = "SYSTEM",
        detail: Optional[dict] = None,
    ) -> ConstitutionalChangeEvent:
        ev = ConstitutionalChangeEvent(
            event_id=f"CH-{change_type[:4]}-{int(time.time()*1000)}",
            change_type=change_type,
            subject_id=subject_id,
            summary=summary,
            actor=actor,
            detail=detail or {},
        )
        with self._lock:
            self._events.append(ev)
            if len(self._events) > MAX_HISTORY_EVENTS:
                self._events = self._events[-MAX_HISTORY_EVENTS:]
        return ev

    # ── Query ──────────────────────────────────────────────────────────────────

    def full_timeline(self, limit: int = 200) -> List[dict]:
        with self._lock:
            items = list(self._events)
        return [self._ser(e) for e in sorted(items, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    def for_subject(self, subject_id: str) -> List[dict]:
        with self._lock:
            items = [e for e in self._events if e.subject_id == subject_id]
        return [self._ser(e) for e in sorted(items, key=lambda x: x.recorded_at)]

    def by_type(self, change_type: str, limit: int = 50) -> List[dict]:
        with self._lock:
            items = [e for e in self._events if e.change_type == change_type]
        return [self._ser(e) for e in sorted(items, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    def since(self, days: int) -> List[dict]:
        cutoff = time.time() - days * 86400
        with self._lock:
            items = [e for e in self._events if e.recorded_at >= cutoff]
        return [self._ser(e) for e in sorted(items, key=lambda x: x.recorded_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._events)
            by_type: Dict[str, int] = {}
            for e in self._events:
                by_type[e.change_type] = by_type.get(e.change_type, 0) + 1
        return {
            "total_events":  total,
            "by_type":       by_type,
            "change_types":  sorted(CHANGE_TYPES),
        }

    @staticmethod
    def _ser(e: ConstitutionalChangeEvent) -> dict:
        return {
            "event_id":    e.event_id,
            "change_type": e.change_type,
            "subject_id":  e.subject_id,
            "summary":     e.summary,
            "actor":       e.actor,
            "detail":      e.detail,
            "recorded_at": e.recorded_at,
        }


# Singleton
constitutional_history = ConstitutionalHistory()

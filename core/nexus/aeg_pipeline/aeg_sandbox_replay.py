"""
PHOENIX AEG — Sandbox Replay Engine  [GAP-005]

Records the decision rationale for every pipeline stage transition:
  - Why was a recommendation promoted?
  - Why was it rejected / blocked?
  - Why was it demoted?

Enables institutional replay:
  - "Show me the full decision chain for rec_type REDUCE_POSITION_SIZE"
  - "What evidence was available when this was approved?"
  - "Was the decision consistent with the trust score at that time?"
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReplayEvent:
    event_id: str
    rec_id: str
    rec_type: str
    stage_from: str
    stage_to: str
    rationale: str
    trust_score_at_event: float
    sandbox_accuracy_at_event: float
    sandbox_samples_at_event: int
    decided_by: str          # "SYSTEM", "HUMAN:<name>"
    evidence_snapshot: dict = field(default_factory=dict)
    recorded_at: float = field(default_factory=time.time)


class AEGSandboxReplay:
    """
    Immutable audit trail of all AEG pipeline decision events.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: List[ReplayEvent] = []
        self._rec_index: Dict[str, List[int]] = {}

    def record(
        self,
        rec_id: str,
        rec_type: str,
        stage_from: str,
        stage_to: str,
        rationale: str,
        trust_score: float = 0.0,
        sandbox_accuracy: float = 0.0,
        sandbox_samples: int = 0,
        decided_by: str = "SYSTEM",
        evidence_snapshot: Optional[dict] = None,
    ) -> ReplayEvent:
        ev = ReplayEvent(
            event_id=f"RPL-{rec_type[:4]}-{int(time.time()*1000)}",
            rec_id=rec_id,
            rec_type=rec_type,
            stage_from=stage_from,
            stage_to=stage_to,
            rationale=rationale,
            trust_score_at_event=trust_score,
            sandbox_accuracy_at_event=sandbox_accuracy,
            sandbox_samples_at_event=sandbox_samples,
            decided_by=decided_by,
            evidence_snapshot=evidence_snapshot or {},
        )
        with self._lock:
            idx = len(self._events)
            self._events.append(ev)
            self._rec_index.setdefault(rec_id, []).append(idx)
        return ev

    def replay_for_rec(self, rec_id: str) -> List[dict]:
        with self._lock:
            indices = self._rec_index.get(rec_id, [])
            events = [self._events[i] for i in indices]
        return [self._ser(e) for e in sorted(events, key=lambda x: x.recorded_at)]

    def replay_for_rec_type(self, rec_type: str, limit: int = 50) -> List[dict]:
        with self._lock:
            events = [e for e in self._events if e.rec_type == rec_type]
        return [self._ser(e) for e in sorted(events, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    def promotion_decisions(self) -> List[dict]:
        with self._lock:
            events = [e for e in self._events if e.stage_to == "PROMOTED_TO_LIVE"]
        return [self._ser(e) for e in sorted(events, key=lambda x: x.recorded_at, reverse=True)]

    def demotion_decisions(self) -> List[dict]:
        with self._lock:
            events = [e for e in self._events if e.stage_to == "BLOCKED" or e.stage_to == "AEG_SANDBOX"]
        return [self._ser(e) for e in sorted(events, key=lambda x: x.recorded_at, reverse=True)]

    def decision_consistency_check(self, rec_id: str) -> dict:
        events = self.replay_for_rec(rec_id)
        if not events:
            return {"rec_id": rec_id, "consistent": None, "note": "No events found"}
        issues = []
        for ev in events:
            if ev["stage_to"] == "PROMOTED_TO_LIVE" and ev["trust_score_at_event"] < 50.0:
                issues.append(f"Promoted with trust score {ev['trust_score_at_event']:.1f} < 50 threshold")
            if ev["stage_to"] == "PROMOTED_TO_LIVE" and ev["sandbox_accuracy_at_event"] < 0.70:
                issues.append(f"Promoted with sandbox accuracy {ev['sandbox_accuracy_at_event']:.1%} < 70% threshold")
        return {
            "rec_id":     rec_id,
            "consistent": len(issues) == 0,
            "issues":     issues,
            "event_count": len(events),
        }

    def summary(self) -> dict:
        with self._lock:
            total = len(self._events)
            promotions = sum(1 for e in self._events if e.stage_to == "PROMOTED_TO_LIVE")
            blocks = sum(1 for e in self._events if e.stage_to == "BLOCKED")
        return {
            "total_events": total,
            "promotions":   promotions,
            "blocks":       blocks,
            "rec_types_tracked": len(set(e.rec_type for e in self._events)),
        }

    @staticmethod
    def _ser(e: ReplayEvent) -> dict:
        return {
            "event_id":                 e.event_id,
            "rec_id":                   e.rec_id,
            "rec_type":                 e.rec_type,
            "stage_from":               e.stage_from,
            "stage_to":                 e.stage_to,
            "rationale":                e.rationale,
            "trust_score_at_event":     e.trust_score_at_event,
            "sandbox_accuracy_at_event": e.sandbox_accuracy_at_event,
            "sandbox_samples_at_event": e.sandbox_samples_at_event,
            "decided_by":               e.decided_by,
            "evidence_snapshot":        e.evidence_snapshot,
            "recorded_at":              e.recorded_at,
        }


# Singleton
aeg_sandbox_replay = AEGSandboxReplay()

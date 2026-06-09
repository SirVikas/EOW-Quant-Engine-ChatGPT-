"""
PHOENIX Unified Trust Fabric — Trust Registry
Central trust score registry for all system subjects.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


def _compute_status(score: float, evidence: int) -> str:
    if score >= 0.75 and evidence >= 10:
        return "TRUSTED"
    elif score >= 0.5 or evidence >= 3:
        return "PROVISIONAL"
    return "UNVERIFIED"


@dataclass
class TrustEntry:
    trust_id: str
    subject_id: str
    subject_type: str  # RECOMMENDATION/ROOT_CAUSE/DECISION/LAYER/EVOLUTION/ECONOMIC_MODEL
    trust_score: float
    evidence_count: int
    last_updated: str
    status: str  # TRUSTED/PROVISIONAL/UNVERIFIED/REVOKED


class TrustRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._entries: Dict[str, TrustEntry] = {}  # key: subject_id

    def set_trust(
        self, subject_id: str, subject_type: str, trust_score: float, evidence_count: int
    ) -> dict:
        with self._lock:
            existing = self._entries.get(subject_id)
            if existing:
                existing.trust_score = trust_score
                existing.subject_type = subject_type
                existing.evidence_count = evidence_count
                existing.last_updated = datetime.now(timezone.utc).isoformat()
                existing.status = _compute_status(trust_score, evidence_count)
                return asdict(existing)
            entry = TrustEntry(
                trust_id=f"TR-{uuid.uuid4().hex[:8].upper()}",
                subject_id=subject_id,
                subject_type=subject_type,
                trust_score=trust_score,
                evidence_count=evidence_count,
                last_updated=datetime.now(timezone.utc).isoformat(),
                status=_compute_status(trust_score, evidence_count),
            )
            self._entries[subject_id] = entry
            return asdict(entry)

    def get_trust(self, subject_id: str) -> Optional[dict]:
        with self._lock:
            e = self._entries.get(subject_id)
        return asdict(e) if e else None

    def all_trust_entries(self, subject_type: str = None, status_filter: str = None) -> list:
        with self._lock:
            items = list(self._entries.values())
        if subject_type:
            items = [e for e in items if e.subject_type == subject_type]
        if status_filter:
            items = [e for e in items if e.status == status_filter]
        return [asdict(e) for e in items]

    def trust_summary(self) -> dict:
        with self._lock:
            items = list(self._entries.values())
        total = len(items)
        trusted = sum(1 for e in items if e.status == "TRUSTED")
        provisional = sum(1 for e in items if e.status == "PROVISIONAL")
        unverified = sum(1 for e in items if e.status == "UNVERIFIED")
        revoked = sum(1 for e in items if e.status == "REVOKED")
        avg_score = sum(e.trust_score for e in items) / total if total else 0.0
        return {
            "total": total,
            "trusted": trusted,
            "provisional": provisional,
            "unverified": unverified,
            "revoked": revoked,
            "avg_score": round(avg_score, 4),
        }


trust_registry = TrustRegistry()

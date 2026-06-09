"""
PHOENIX Epistemic Intelligence — Evidence Tracker
Tracks evidence quality and quantity per domain/claim.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _compute_status(count: int, quality: float) -> str:
    if count >= 20 and quality >= 0.7:
        return "WELL_EVIDENCED"
    elif count >= 5:
        return "PARTIALLY_EVIDENCED"
    elif count > 0:
        return "ASSUMED"
    return "UNKNOWN"


@dataclass
class EvidenceRecord:
    evidence_id: str
    domain: str
    claim: str
    evidence_count: int
    evidence_quality: float
    last_updated: str
    status: str


class EvidenceTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, EvidenceRecord] = {}  # key: domain::claim

    def _key(self, domain: str, claim: str) -> str:
        return f"{domain}::{claim}"

    def record_evidence(self, domain: str, claim: str, quality: float = 0.5) -> dict:
        key = self._key(domain, claim)
        with self._lock:
            rec = self._records.get(key)
            if rec:
                rec.evidence_count += 1
                rec.evidence_quality = (rec.evidence_quality + quality) / 2
                rec.last_updated = datetime.now(timezone.utc).isoformat()
                rec.status = _compute_status(rec.evidence_count, rec.evidence_quality)
            else:
                import uuid
                rec = EvidenceRecord(
                    evidence_id=f"EV-{uuid.uuid4().hex[:8].upper()}",
                    domain=domain,
                    claim=claim,
                    evidence_count=1,
                    evidence_quality=quality,
                    last_updated=datetime.now(timezone.utc).isoformat(),
                    status=_compute_status(1, quality),
                )
                self._records[key] = rec
        return asdict(rec)

    def get_evidence_status(self, domain: str, claim: str) -> Optional[dict]:
        key = self._key(domain, claim)
        with self._lock:
            rec = self._records.get(key)
        return asdict(rec) if rec else None

    def all_evidence(self, status_filter: str = None) -> list:
        with self._lock:
            items = list(self._records.values())
        if status_filter:
            items = [r for r in items if r.status == status_filter]
        return [asdict(r) for r in items]

    def evidence_coverage(self) -> dict:
        with self._lock:
            items = list(self._records.values())
        total = len(items)
        if total == 0:
            return {"total_claims": 0, "well_evidenced_pct": 0, "assumed_pct": 0, "unknown_pct": 0}
        well = sum(1 for r in items if r.status == "WELL_EVIDENCED")
        assumed = sum(1 for r in items if r.status in ("ASSUMED", "PARTIALLY_EVIDENCED"))
        unknown = sum(1 for r in items if r.status == "UNKNOWN")
        return {
            "total_claims": total,
            "well_evidenced_pct": round(well / total * 100, 2),
            "assumed_pct": round(assumed / total * 100, 2),
            "unknown_pct": round(unknown / total * 100, 2),
        }


evidence_tracker = EvidenceTracker()

"""
PHOENIX Unified Trust Fabric — Trust Decay Engine
Applies time-based decay to trust scores for subjects without recent evidence.
"""
from __future__ import annotations
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class DecayRecord:
    subject_id: str
    decay_rate_per_day: float
    last_decay_applied: str
    days_since_evidence: float


class TrustFabricDecayEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, DecayRecord] = {}

    def register_for_decay(self, subject_id: str, decay_rate_per_day: float = 0.01) -> dict:
        with self._lock:
            rec = DecayRecord(
                subject_id=subject_id,
                decay_rate_per_day=decay_rate_per_day,
                last_decay_applied=datetime.now(timezone.utc).isoformat(),
                days_since_evidence=0.0,
            )
            self._records[subject_id] = rec
            return asdict(rec)

    def apply_decay(self) -> dict:
        from core.trust_fabric.trust_registry import trust_registry
        from datetime import datetime as dt_cls

        now = datetime.now(timezone.utc)
        decayed = 0
        total_decay = 0.0

        with self._lock:
            records = list(self._records.values())

        for rec in records:
            last = dt_cls.fromisoformat(rec.last_decay_applied)
            days = (now - last).total_seconds() / 86400.0
            if days < 1:
                continue
            entry = trust_registry.get_trust(rec.subject_id)
            if entry:
                decay_amount = rec.decay_rate_per_day * days
                new_score = max(0.0, entry["trust_score"] - decay_amount)
                trust_registry.set_trust(
                    rec.subject_id,
                    entry["subject_type"],
                    new_score,
                    entry["evidence_count"],
                )
                total_decay += decay_amount
                decayed += 1
            with self._lock:
                rec.last_decay_applied = now.isoformat()
                rec.days_since_evidence += days

        return {
            "subjects_decayed": decayed,
            "total_decay_applied": round(total_decay, 6),
            "applied_at": now.isoformat(),
        }

    def decay_status(self, subject_id: str) -> dict:
        with self._lock:
            rec = self._records.get(subject_id)
        return asdict(rec) if rec else {"error": f"{subject_id} not registered for decay"}

    def all_decay_records(self) -> list:
        with self._lock:
            return [asdict(r) for r in self._records.values()]


trust_fabric_decay_engine = TrustFabricDecayEngine()

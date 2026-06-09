"""Knowledge Decay Engine — tracks how knowledge freshness degrades over time."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


def _compute_status(current_value: float) -> str:
    if current_value >= 0.8:
        return "FRESH"
    if current_value >= 0.5:
        return "AGING"
    if current_value >= 0.2:
        return "STALE"
    return "EXPIRED"


@dataclass
class DecayRecord:
    subject_id: str
    knowledge_type: str
    initial_value: float
    current_value: float
    decay_rate_per_day: float
    last_updated: str
    status: str


class KnowledgeDecayEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, DecayRecord] = {}

    def register(self, subject_id: str, knowledge_type: str,
                 initial_value: float = 1.0, decay_rate: float = 0.005) -> str:
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            record = DecayRecord(
                subject_id=subject_id,
                knowledge_type=knowledge_type,
                initial_value=initial_value,
                current_value=initial_value,
                decay_rate_per_day=decay_rate,
                last_updated=now,
                status=_compute_status(initial_value),
            )
            self._records[subject_id] = record
            return subject_id

    def apply_decay(self) -> dict:
        with self._lock:
            now = datetime.now(timezone.utc)
            decayed_count = 0
            expired_count = 0
            for record in self._records.values():
                last = datetime.fromisoformat(record.last_updated)
                elapsed_days = (now - last).total_seconds() / 86400.0
                if elapsed_days > 0:
                    record.current_value = max(0.0, record.current_value - record.decay_rate_per_day * elapsed_days)
                    record.last_updated = now.isoformat()
                    record.status = _compute_status(record.current_value)
                    decayed_count += 1
                    if record.status == "EXPIRED":
                        expired_count += 1
            return {"decayed_count": decayed_count, "expired_count": expired_count}

    def stale_knowledge(self) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._records.values()
                    if r.status in ("STALE", "EXPIRED")]

    def get_record(self, subject_id: str) -> Optional[dict]:
        with self._lock:
            r = self._records.get(subject_id)
            return asdict(r) if r else None

    def decay_stats(self) -> dict:
        with self._lock:
            counts = {"FRESH": 0, "AGING": 0, "STALE": 0, "EXPIRED": 0}
            for r in self._records.values():
                counts[r.status] = counts.get(r.status, 0) + 1
            return {
                "total": len(self._records),
                "fresh": counts["FRESH"],
                "aging": counts["AGING"],
                "stale": counts["STALE"],
                "expired": counts["EXPIRED"],
            }


knowledge_decay_engine = KnowledgeDecayEngine()

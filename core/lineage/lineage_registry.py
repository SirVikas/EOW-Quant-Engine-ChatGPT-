"""Lineage Registry — records before/after state changes for all subjects."""
import threading
import time
from dataclasses import dataclass


@dataclass
class LineageEntry:
    entry_id: str
    subject_id: str
    subject_type: str
    action: str
    actor: str
    before_state: dict
    after_state: dict
    timestamp: float


class LineageRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._entries: list[LineageEntry] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"LGY-{self._counter:03d}"

    def record(self, subject_id: str, subject_type: str, action: str, actor: str,
               before_state: dict = None, after_state: dict = None) -> str:
        with self._lock:
            eid = self._next_id()
            self._entries.append(LineageEntry(
                entry_id=eid,
                subject_id=subject_id,
                subject_type=subject_type,
                action=action,
                actor=actor,
                before_state=before_state or {},
                after_state=after_state or {},
                timestamp=time.time(),
            ))
            return eid

    def history_of(self, subject_id: str) -> list:
        with self._lock:
            entries = [e for e in self._entries if e.subject_id == subject_id]
            entries.sort(key=lambda x: x.timestamp)
            return [vars(e) for e in entries]

    def recent_changes(self, limit: int = 20) -> list:
        with self._lock:
            sorted_entries = sorted(self._entries, key=lambda x: x.timestamp, reverse=True)
            return [vars(e) for e in sorted_entries[:limit]]

    def lineage_stats(self) -> dict:
        with self._lock:
            total = len(self._entries)
            subject_counts: dict = {}
            for e in self._entries:
                subject_counts[e.subject_id] = subject_counts.get(e.subject_id, 0) + 1
            most_changed = max(subject_counts, key=subject_counts.get) if subject_counts else None
            return {
                "total_entries": total,
                "subjects_tracked": len(subject_counts),
                "most_changed_subject": most_changed,
            }


lineage_registry = LineageRegistry()

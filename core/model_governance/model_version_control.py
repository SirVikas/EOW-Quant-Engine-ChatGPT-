"""Model Version Control — tracks model version history."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class VersionRecord:
    version_record_id: str
    model_id: str
    version: str
    change_summary: str
    promoted_by: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ModelVersionControl:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[VersionRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"VER-{self._counter:03d}"

    def record_version(self, model_id: str, version: str, change_summary: str, promoted_by: str) -> VersionRecord:
        with self._lock:
            rec = VersionRecord(
                version_record_id=self._next_id(),
                model_id=model_id,
                version=version,
                change_summary=change_summary,
                promoted_by=promoted_by,
            )
            self._records.append(rec)
            return rec

    def version_history(self, model_id: str) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._records if r.model_id == model_id]


model_version_control = ModelVersionControl()

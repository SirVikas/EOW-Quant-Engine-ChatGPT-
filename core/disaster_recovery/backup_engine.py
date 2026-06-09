"""Disaster Recovery — Backup Engine."""
import threading, time, hashlib
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Backup:
    backup_id: str
    label: str
    snapshot_id: str
    backup_type: str
    size_estimate: int
    created_at: float
    checksum: str


class BackupEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._backups: List[Backup] = []
        self._counter = 0

    def create_backup(self, label: str, backup_type: str = "FULL") -> str:
        from core.lineage.snapshot_engine import snapshot_engine
        snapshot_id = snapshot_engine.capture(label, "MANUAL")
        ts = time.time()
        from datetime import datetime
        dt = datetime.utcfromtimestamp(ts)
        backup_id = f"BCK-{dt.strftime('%Y%m%d-%H%M%S')}"
        checksum = hashlib.sha256(f"{snapshot_id}{ts}".encode()).hexdigest()
        backup = Backup(
            backup_id=backup_id,
            label=label,
            snapshot_id=snapshot_id,
            backup_type=backup_type,
            size_estimate=1024,
            created_at=ts,
            checksum=checksum,
        )
        with self._lock:
            self._backups.append(backup)
        return backup_id

    def all_backups(self, limit: int = 20) -> List[dict]:
        with self._lock:
            backups = self._backups[-limit:]
        return [
            {
                "backup_id": b.backup_id,
                "label": b.label,
                "snapshot_id": b.snapshot_id,
                "backup_type": b.backup_type,
                "size_estimate": b.size_estimate,
                "created_at": b.created_at,
                "checksum": b.checksum,
            }
            for b in reversed(backups)
        ]

    def latest_backup(self) -> Optional[dict]:
        with self._lock:
            if not self._backups:
                return None
            b = self._backups[-1]
        return {
            "backup_id": b.backup_id,
            "label": b.label,
            "backup_type": b.backup_type,
            "created_at": b.created_at,
        }

    def backup_stats(self) -> dict:
        with self._lock:
            total = len(self._backups)
            latest_at = self._backups[-1].created_at if self._backups else None
            by_type: dict = {}
            for b in self._backups:
                by_type[b.backup_type] = by_type.get(b.backup_type, 0) + 1
        return {"total_backups": total, "latest_at": latest_at, "by_type": by_type}


backup_engine = BackupEngine()

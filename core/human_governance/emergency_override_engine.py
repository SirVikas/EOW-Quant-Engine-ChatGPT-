"""Emergency Override Engine — issues and tracks emergency human overrides."""
import threading
import time
from dataclasses import dataclass


@dataclass
class Override:
    override_id: str
    override_type: str  # PAUSE/STOP/ROLLBACK/FORCE_APPROVE/FORCE_REJECT
    issued_by: str
    target_subject: str
    reason: str
    issued_at: float
    revoked_at: float  # 0.0 = not revoked
    active: bool


class EmergencyOverrideEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._overrides: dict[str, Override] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"OVR-{self._counter:03d}"

    def issue_override(self, override_type: str, issued_by: str,
                        target_subject: str, reason: str) -> str:
        with self._lock:
            oid = self._next_id()
            self._overrides[oid] = Override(
                override_id=oid,
                override_type=override_type,
                issued_by=issued_by,
                target_subject=target_subject,
                reason=reason,
                issued_at=time.time(),
                revoked_at=0.0,
                active=True,
            )
            return oid

    def revoke(self, override_id: str, revoked_by: str) -> bool:
        with self._lock:
            o = self._overrides.get(override_id)
            if not o:
                return False
            o.active = False
            o.revoked_at = time.time()
            return True

    def active_overrides(self) -> list:
        with self._lock:
            return [vars(o) for o in self._overrides.values() if o.active]

    def override_log(self, limit: int = 50) -> list:
        with self._lock:
            items = sorted(self._overrides.values(), key=lambda x: x.issued_at, reverse=True)
            return [vars(o) for o in items[:limit]]

    def override_stats(self) -> dict:
        with self._lock:
            items = list(self._overrides.values())
            total = len(items)
            active = sum(1 for o in items if o.active)
            by_type: dict = {}
            for o in items:
                by_type[o.override_type] = by_type.get(o.override_type, 0) + 1
            return {
                "total_issued": total,
                "active": active,
                "revoked": total - active,
                "by_type": by_type,
            }


emergency_override_engine = EmergencyOverrideEngine()

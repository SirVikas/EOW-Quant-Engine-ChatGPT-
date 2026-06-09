"""Disaster Recovery — Failover Manager."""
import threading, time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FailoverEvent:
    event_id: str
    failed_layer: str
    failover_strategy: str
    triggered_by: str
    triggered_at: float
    resolved_at: Optional[float]
    status: str


class FailoverManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._events: List[FailoverEvent] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"FOE-{self._counter:03d}"

    def trigger_failover(self, failed_layer: str, failover_strategy: str, triggered_by: str) -> str:
        with self._lock:
            eid = self._next_id()
            event = FailoverEvent(
                event_id=eid,
                failed_layer=failed_layer,
                failover_strategy=failover_strategy,
                triggered_by=triggered_by,
                triggered_at=time.time(),
                resolved_at=None,
                status="ACTIVE",
            )
            self._events.append(event)
        try:
            from core.pccp.layer_registry import layer_registry
            layer_registry.update_health(failed_layer, "DEGRADED", f"Failover triggered: {failover_strategy}")
        except Exception:
            pass
        return eid

    def resolve_failover(self, event_id: str) -> bool:
        with self._lock:
            for ev in self._events:
                if ev.event_id == event_id:
                    ev.status = "RESOLVED"
                    ev.resolved_at = time.time()
                    return True
        return False

    def active_failovers(self) -> List[dict]:
        with self._lock:
            active = [ev for ev in self._events if ev.status == "ACTIVE"]
        return [
            {
                "event_id": ev.event_id,
                "failed_layer": ev.failed_layer,
                "failover_strategy": ev.failover_strategy,
                "triggered_by": ev.triggered_by,
                "triggered_at": ev.triggered_at,
                "status": ev.status,
            }
            for ev in active
        ]

    def failover_history(self, limit: int = 20) -> List[dict]:
        with self._lock:
            events = self._events[-limit:]
        return [
            {
                "event_id": ev.event_id,
                "failed_layer": ev.failed_layer,
                "failover_strategy": ev.failover_strategy,
                "triggered_by": ev.triggered_by,
                "triggered_at": ev.triggered_at,
                "resolved_at": ev.resolved_at,
                "status": ev.status,
            }
            for ev in reversed(events)
        ]

    def disaster_recovery_status(self) -> dict:
        with self._lock:
            active_count = sum(1 for ev in self._events if ev.status == "ACTIVE")
            total = len(self._events)
        try:
            from core.disaster_recovery.backup_engine import backup_engine
            last_backup = backup_engine.latest_backup()
        except Exception:
            last_backup = None
        try:
            from core.disaster_recovery.restore_engine import restore_engine
            stats = restore_engine.restore_stats()
            last_restore = stats.get("last_restore_at")
        except Exception:
            last_restore = None
        return {
            "active_failovers": active_count,
            "total_events": total,
            "last_backup": last_backup,
            "last_restore": last_restore,
            "generated_at": time.time(),
        }


failover_manager = FailoverManager()

"""Rollback Authority — issues and tracks human-authorized rollback orders."""
import threading
import time
from dataclasses import dataclass


@dataclass
class RollbackOrder:
    order_id: str
    issued_by: str
    target: str
    target_type: str
    reason: str
    urgency: str  # ROUTINE/URGENT/EMERGENCY
    status: str  # ISSUED/IN_PROGRESS/COMPLETED/FAILED
    issued_at: float


class RollbackAuthority:
    def __init__(self):
        self._lock = threading.RLock()
        self._orders: dict[str, RollbackOrder] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ROB-{self._counter:03d}"

    def issue_rollback(self, issued_by: str, target: str, target_type: str,
                        reason: str, urgency: str = "ROUTINE") -> str:
        with self._lock:
            oid = self._next_id()
            self._orders[oid] = RollbackOrder(
                order_id=oid,
                issued_by=issued_by,
                target=target,
                target_type=target_type,
                reason=reason,
                urgency=urgency,
                status="ISSUED",
                issued_at=time.time(),
            )

            # For EMERGENCY: also issue an override
            if urgency == "EMERGENCY":
                try:
                    from core.human_governance.emergency_override_engine import emergency_override_engine
                    emergency_override_engine.issue_override(
                        "ROLLBACK", issued_by, target,
                        f"EMERGENCY rollback order {oid}: {reason}"
                    )
                except Exception:
                    pass

            return oid

    def complete(self, order_id: str) -> bool:
        with self._lock:
            o = self._orders.get(order_id)
            if not o:
                return False
            o.status = "COMPLETED"
            return True

    def fail(self, order_id: str, failure_reason: str = "") -> bool:
        with self._lock:
            o = self._orders.get(order_id)
            if not o:
                return False
            o.status = "FAILED"
            return True

    def all_orders(self, status_filter: str = None) -> list:
        with self._lock:
            items = list(self._orders.values())
            if status_filter:
                items = [o for o in items if o.status == status_filter]
            return [vars(o) for o in items]

    def rollback_stats(self) -> dict:
        with self._lock:
            items = list(self._orders.values())
            by_status: dict = {}
            by_urgency: dict = {}
            by_type: dict = {}
            for o in items:
                by_status[o.status] = by_status.get(o.status, 0) + 1
                by_urgency[o.urgency] = by_urgency.get(o.urgency, 0) + 1
                by_type[o.target_type] = by_type.get(o.target_type, 0) + 1
            return {
                "total": len(items),
                "by_status": by_status,
                "by_urgency": by_urgency,
                "by_type": by_type,
            }


rollback_authority = RollbackAuthority()

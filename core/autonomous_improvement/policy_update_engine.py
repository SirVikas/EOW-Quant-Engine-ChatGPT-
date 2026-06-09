"""
PHOENIX Autonomous Improvement — Policy Update Engine
Proposes, approves, and applies policy updates driven by lessons learned.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class PolicyUpdate:
    update_id: str
    policy_name: str
    old_value: str
    new_value: str
    reason: str
    evidence_basis: str
    approved: bool
    applied: bool
    created_at: str
    applied_at: Optional[str]


class PolicyUpdateEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._updates: Dict[str, PolicyUpdate] = {}

    def propose_update(
        self,
        policy_name: str,
        old_value: str,
        new_value: str,
        reason: str,
        evidence_basis: str,
    ) -> dict:
        update_id = f"PU-{uuid.uuid4().hex[:8].upper()}"
        update = PolicyUpdate(
            update_id=update_id,
            policy_name=policy_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            evidence_basis=evidence_basis,
            approved=False,
            applied=False,
            created_at=datetime.now(timezone.utc).isoformat(),
            applied_at=None,
        )
        with self._lock:
            self._updates[update_id] = update
        return asdict(update)

    def approve(self, update_id: str) -> dict:
        with self._lock:
            u = self._updates.get(update_id)
            if u:
                u.approved = True
                return asdict(u)
        return {"error": f"{update_id} not found"}

    def apply(self, update_id: str) -> dict:
        with self._lock:
            u = self._updates.get(update_id)
            if u:
                u.applied = True
                u.applied_at = datetime.now(timezone.utc).isoformat()
                return asdict(u)
        return {"error": f"{update_id} not found"}

    def pending_updates(self) -> list:
        with self._lock:
            return [asdict(u) for u in self._updates.values() if u.approved and not u.applied]

    def update_history(self, limit: int = 50) -> list:
        with self._lock:
            items = list(self._updates.values())
        items.sort(key=lambda x: x.created_at, reverse=True)
        return [asdict(u) for u in items[:limit]]

    def policy_stats(self) -> dict:
        with self._lock:
            items = list(self._updates.values())
        total = len(items)
        approved = sum(1 for u in items if u.approved)
        applied = sum(1 for u in items if u.applied)
        pending = sum(1 for u in items if u.approved and not u.applied)
        return {
            "total_proposed": total,
            "approved": approved,
            "applied": applied,
            "pending_application": pending,
        }


policy_update_engine = PolicyUpdateEngine()

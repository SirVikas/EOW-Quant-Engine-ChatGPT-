"""
PHOENIX Autonomous Improvement — Behavior Update Engine
Tracks and manages behavior changes across system components.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
import uuid


@dataclass
class BehaviorChange:
    change_id: str
    component: str
    behavior_name: str
    old_behavior: str
    new_behavior: str
    trigger: str       # LESSON/PATTERN/OUTCOME/MANUAL
    confidence: float
    status: str        # PROPOSED/TESTED/APPROVED/ACTIVE/REVERTED
    created_at: str


class BehaviorUpdateEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._changes: Dict[str, BehaviorChange] = {}

    def propose_change(
        self,
        component: str,
        behavior_name: str,
        old_behavior: str,
        new_behavior: str,
        trigger: str,
        confidence: float,
    ) -> dict:
        change_id = f"BC-{uuid.uuid4().hex[:8].upper()}"
        change = BehaviorChange(
            change_id=change_id,
            component=component,
            behavior_name=behavior_name,
            old_behavior=old_behavior,
            new_behavior=new_behavior,
            trigger=trigger,
            confidence=confidence,
            status="PROPOSED",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._changes[change_id] = change
        return asdict(change)

    def _transition(self, change_id: str, new_status: str) -> dict:
        with self._lock:
            c = self._changes.get(change_id)
            if c:
                c.status = new_status
                return asdict(c)
        return {"error": f"{change_id} not found"}

    def test(self, change_id: str) -> dict:
        return self._transition(change_id, "TESTED")

    def approve(self, change_id: str) -> dict:
        return self._transition(change_id, "APPROVED")

    def activate(self, change_id: str) -> dict:
        return self._transition(change_id, "ACTIVE")

    def revert(self, change_id: str) -> dict:
        return self._transition(change_id, "REVERTED")

    def active_changes(self) -> list:
        with self._lock:
            return [asdict(c) for c in self._changes.values() if c.status == "ACTIVE"]

    def change_stats(self) -> dict:
        with self._lock:
            items = list(self._changes.values())
        by_status: Dict[str, int] = {}
        by_trigger: Dict[str, int] = {}
        by_component: Dict[str, int] = {}
        for c in items:
            by_status[c.status] = by_status.get(c.status, 0) + 1
            by_trigger[c.trigger] = by_trigger.get(c.trigger, 0) + 1
            by_component[c.component] = by_component.get(c.component, 0) + 1
        return {
            "total": len(items),
            "by_status": by_status,
            "by_trigger": by_trigger,
            "by_component": by_component,
        }


behavior_update_engine = BehaviorUpdateEngine()

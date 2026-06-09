"""
PHOENIX Evolution Governance — Evolution Rollback Engine
Handles rollback of deployed evolutions with full audit trail.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
import uuid


@dataclass
class Rollback:
    rollback_id: str
    evo_id: str
    reason: str
    rolled_back_by: str
    impact_before: str
    impact_after: str
    success: bool
    rolled_back_at: str


class EvolutionRollbackEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._rollbacks: Dict[str, Rollback] = {}

    def rollback(
        self,
        evo_id: str,
        reason: str,
        rolled_back_by: str,
        impact_before: str = "",
        impact_after: str = "",
    ) -> dict:
        from core.evolution_governance.evolution_registry import evolution_registry

        rollback_id = f"RBK-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc).isoformat()
        rb = Rollback(
            rollback_id=rollback_id,
            evo_id=evo_id,
            reason=reason,
            rolled_back_by=rolled_back_by,
            impact_before=impact_before,
            impact_after=impact_after,
            success=True,
            rolled_back_at=ts,
        )
        evolution_registry.update_status(evo_id, "ROLLED_BACK", rolled_back_at=ts)
        with self._lock:
            self._rollbacks[rollback_id] = rb
        return asdict(rb)

    def all_rollbacks(self) -> list:
        with self._lock:
            return [asdict(r) for r in self._rollbacks.values()]

    def rollback_stats(self) -> dict:
        with self._lock:
            items = list(self._rollbacks.values())
        total = len(items)
        successful = sum(1 for r in items if r.success)
        failed = total - successful
        reasons: Dict[str, int] = {}
        for r in items:
            reasons[r.reason] = reasons.get(r.reason, 0) + 1
        most_common = max(reasons, key=lambda k: reasons[k]) if reasons else None
        return {
            "total_rollbacks": total,
            "successful": successful,
            "failed": failed,
            "most_common_reason": most_common,
        }


evolution_rollback_engine = EvolutionRollbackEngine()

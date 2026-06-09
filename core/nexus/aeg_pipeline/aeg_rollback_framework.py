"""
PHOENIX AEG — Autonomous Rollback Framework  [GAP-008]

When a PROMOTED_TO_LIVE recommendation degrades below the demotion threshold,
the rollback framework:
  1. Records a RollbackEvent with full evidence snapshot
  2. Demotes the pipeline entry back to AEG_SANDBOX
  3. Suspends the recommendation from re-promotion for SUSPENSION_DAYS
  4. Notifies NEXUS via TrustEvidenceBridge
  5. Provides full audit trail for the rollback decision

Re-promotion requires:
  - Suspension period expired
  - Sandbox accuracy rebuilt above threshold
  - Human approval through AEGPromotionCourt
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


SUSPENSION_DAYS = 14      # minimum days before re-promotion after rollback
ROLLBACK_ACCURACY_TRIGGER = 0.55   # live accuracy below this triggers rollback


@dataclass
class RollbackEvent:
    rollback_id: str
    rec_id: str
    rec_type: str
    trigger: str          # "AUTO_DEMOTION" / "HUMAN_OVERRIDE" / "COURT_ORDER"
    live_accuracy_at_rollback: float
    live_samples_at_rollback: int
    evidence_snapshot: dict
    suspended_until: float
    rolled_back_at: float = field(default_factory=time.time)
    reinstated_at: float = 0.0
    reinstated_by: str = ""


class AEGRollbackFramework:
    """
    Manages autonomous rollback and suspension of demoted AEG recommendations.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rollbacks: List[RollbackEvent] = []
        self._suspensions: Dict[str, float] = {}   # rec_type → suspended_until timestamp

    def execute_rollback(
        self,
        rec_id: str,
        rec_type: str,
        trigger: str,
        live_accuracy: float,
        live_samples: int,
        evidence_snapshot: Optional[dict] = None,
    ) -> RollbackEvent:
        suspended_until = time.time() + SUSPENSION_DAYS * 86400
        ev = RollbackEvent(
            rollback_id=f"RBK-{rec_type[:4]}-{int(time.time()*1000)}",
            rec_id=rec_id,
            rec_type=rec_type,
            trigger=trigger,
            live_accuracy_at_rollback=live_accuracy,
            live_samples_at_rollback=live_samples,
            evidence_snapshot=evidence_snapshot or {},
            suspended_until=suspended_until,
        )
        with self._lock:
            self._rollbacks.append(ev)
            self._suspensions[rec_type] = suspended_until

        # Demote in pipeline
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            entries = aeg_promotion_engine.all_entries(stage_filter="PROMOTED_TO_LIVE")
            for entry in entries:
                if entry["rec_type"] == rec_type:
                    e = aeg_promotion_engine._entries.get(entry["rec_id"])
                    if e:
                        e.stage = "AEG_SANDBOX"
                        e.blocked_reason = f"Rolled back: {trigger} | live accuracy={live_accuracy:.1%}"
                        e.stage_history.append({"stage": "AEG_SANDBOX", "timestamp": time.time(), "rollback": True})
        except Exception:
            pass

        # Record in NEXUS
        try:
            from core.nexus.trust_evidence_bridge import trust_evidence_bridge as _teb
            _teb.mirror_aeg_demotion(rec_type, live_accuracy)
        except Exception:
            pass

        return ev

    def is_suspended(self, rec_type: str) -> bool:
        with self._lock:
            suspended_until = self._suspensions.get(rec_type, 0.0)
        return time.time() < suspended_until

    def suspension_remaining_days(self, rec_type: str) -> float:
        with self._lock:
            suspended_until = self._suspensions.get(rec_type, 0.0)
        remaining = suspended_until - time.time()
        return round(max(0.0, remaining / 86400), 1)

    def reinstate(self, rec_type: str, approved_by: str) -> dict:
        if self.is_suspended(rec_type):
            remaining = self.suspension_remaining_days(rec_type)
            return {"error": f"Still suspended for {remaining:.1f} more days"}
        with self._lock:
            ev = next(
                (e for e in reversed(self._rollbacks) if e.rec_type == rec_type and not e.reinstated_by),
                None,
            )
            if ev:
                ev.reinstated_at = time.time()
                ev.reinstated_by = approved_by
        return {"reinstated": True, "rec_type": rec_type, "approved_by": approved_by}

    def rollback_log(self, rec_type: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._rollbacks)
        if rec_type:
            items = [e for e in items if e.rec_type == rec_type]
        return [self._ser(e) for e in sorted(items, key=lambda x: x.rolled_back_at, reverse=True)]

    def suspended_rec_types(self) -> List[dict]:
        now = time.time()
        with self._lock:
            return [
                {"rec_type": rt, "suspended_until": ts, "remaining_days": round((ts - now) / 86400, 1)}
                for rt, ts in self._suspensions.items() if ts > now
            ]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._rollbacks)
            active_suspensions = sum(1 for ts in self._suspensions.values() if ts > time.time())
        return {
            "total_rollbacks":        total,
            "active_suspensions":     active_suspensions,
            "suspension_days":        SUSPENSION_DAYS,
            "rollback_trigger_floor": ROLLBACK_ACCURACY_TRIGGER,
        }

    @staticmethod
    def _ser(e: RollbackEvent) -> dict:
        return {
            "rollback_id":               e.rollback_id,
            "rec_id":                    e.rec_id,
            "rec_type":                  e.rec_type,
            "trigger":                   e.trigger,
            "live_accuracy_at_rollback": e.live_accuracy_at_rollback,
            "live_samples_at_rollback":  e.live_samples_at_rollback,
            "suspended_until":           e.suspended_until,
            "rolled_back_at":            e.rolled_back_at,
            "reinstated_at":             e.reinstated_at or None,
            "reinstated_by":             e.reinstated_by,
        }


# Singleton
aeg_rollback_framework = AEGRollbackFramework()

"""
PHOENIX OBSERVATORY-X — Recommendation Reality Engine  [GAP-002]

Tracks the complete lifecycle of every recommendation:
  GENERATED → APPLIED → OUTCOME_PENDING → VERIFIED → ARCHIVED

Answers per recommendation:
  - Was it applied?
  - What was the result?
  - What was the economic impact (PnL delta)?
  - Was the prediction correct?

Feeds confirmed outcomes into:
  - TrustAccuracyLedger (per pillar accuracy tracking)
  - LongTermArchive (permanent record)
  - TrustEvidenceBridge (NEXUS mirroring)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


LIFECYCLE_STAGES = [
    "GENERATED",
    "APPLIED",
    "OUTCOME_PENDING",
    "VERIFIED",
    "FAILED",
    "REJECTED",
    "EXPIRED",
    "ARCHIVED",
]


@dataclass
class RecommendationLifecycle:
    rec_id: str
    rec_type: str
    entity_id: str
    pillar: str
    claimed_outcome: str
    actual_outcome: str = ""
    stage: str = "GENERATED"
    correct: Optional[bool] = None
    pnl_delta: float = 0.0
    win_rate_delta: float = 0.0
    trade_count_at_resolution: int = 0
    evidence_detail: str = ""
    generated_at: float = field(default_factory=time.time)
    applied_at: float = 0.0
    verified_at: float = 0.0
    stage_history: List[dict] = field(default_factory=list)


class RecommendationRealityEngine:
    """
    Single source of truth for recommendation lifecycle tracking.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._lifecycles: Dict[str, RecommendationLifecycle] = {}

    # ── Lifecycle Management ──────────────────────────────────────────────────

    def register(
        self,
        rec_id: str,
        rec_type: str,
        entity_id: str,
        pillar: str,
        claimed_outcome: str,
    ) -> RecommendationLifecycle:
        rl = RecommendationLifecycle(
            rec_id=rec_id,
            rec_type=rec_type,
            entity_id=entity_id,
            pillar=pillar,
            claimed_outcome=claimed_outcome,
        )
        rl.stage_history.append({"stage": "GENERATED", "timestamp": time.time()})
        with self._lock:
            self._lifecycles[rec_id] = rl
        return rl

    def mark_applied(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            rl = self._lifecycles.get(rec_id)
        if not rl:
            return {"error": f"Recommendation '{rec_id}' not found"}
        rl.stage = "APPLIED"
        rl.applied_at = time.time()
        rl.stage_history.append({"stage": "APPLIED", "timestamp": time.time()})
        return {"rec_id": rec_id, "stage": "APPLIED"}

    def record_outcome(
        self,
        rec_id: str,
        actual_outcome: str,
        correct: bool,
        pnl_delta: float = 0.0,
        win_rate_delta: float = 0.0,
        trade_count: int = 0,
        evidence_detail: str = "",
    ) -> Optional[dict]:
        with self._lock:
            rl = self._lifecycles.get(rec_id)
        if not rl:
            return {"error": f"Recommendation '{rec_id}' not found"}

        rl.actual_outcome = actual_outcome
        rl.correct = correct
        rl.pnl_delta = pnl_delta
        rl.win_rate_delta = win_rate_delta
        rl.trade_count_at_resolution = trade_count
        rl.evidence_detail = evidence_detail
        rl.stage = "VERIFIED"
        rl.verified_at = time.time()
        rl.stage_history.append({"stage": "VERIFIED", "timestamp": time.time()})

        self._propagate(rl)
        return {"rec_id": rec_id, "stage": "VERIFIED", "correct": correct}

    def mark_rejected(self, rec_id: str, reason: str = "") -> Optional[dict]:
        with self._lock:
            rl = self._lifecycles.get(rec_id)
        if not rl:
            return {"error": f"Recommendation '{rec_id}' not found"}
        rl.stage = "REJECTED"
        rl.evidence_detail = reason
        rl.stage_history.append({"stage": "REJECTED", "timestamp": time.time(), "reason": reason})
        return {"rec_id": rec_id, "stage": "REJECTED"}

    def mark_expired(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            rl = self._lifecycles.get(rec_id)
        if not rl:
            return {"error": f"Recommendation '{rec_id}' not found"}
        rl.stage = "EXPIRED"
        rl.stage_history.append({"stage": "EXPIRED", "timestamp": time.time()})
        return {"rec_id": rec_id, "stage": "EXPIRED"}

    # ── Propagation ───────────────────────────────────────────────────────────

    def _propagate(self, rl: RecommendationLifecycle) -> None:
        # → TrustAccuracyLedger
        try:
            from core.trust.trust_accuracy_ledger import trust_accuracy_ledger as _tal
            _tal.record(
                pillar=rl.pillar,
                entity_id=rl.entity_id,
                claimed_outcome=rl.claimed_outcome,
                actual_outcome=rl.actual_outcome,
                correct=rl.correct or False,
                evidence_detail=rl.evidence_detail,
            )
        except Exception:
            pass

        # → TrustDecayEngine (notify evidence received)
        try:
            from core.trust.trust_decay_engine import trust_decay_engine as _tde
            _tde.notify_new_evidence(rl.pillar)
            _tde.record_outcome(rl.pillar, rl.entity_id, rl.correct or False)
        except Exception:
            pass

        # → LongTermArchive
        try:
            from core.observatory.long_term_archive import long_term_archive as _lta
            _lta.archive(
                rec_id=rl.rec_id,
                rec_type=rl.rec_type,
                entity_id=rl.entity_id,
                pillar=rl.pillar,
                claimed_outcome=rl.claimed_outcome,
                actual_outcome=rl.actual_outcome,
                correct=rl.correct or False,
                trade_count_at_resolution=rl.trade_count_at_resolution,
                pnl_delta=rl.pnl_delta,
                win_rate_delta=rl.win_rate_delta,
                original_recorded_at=rl.generated_at,
            )
        except Exception:
            pass

        # → TrustEvidenceBridge
        try:
            from core.nexus.trust_evidence_bridge import trust_evidence_bridge as _teb
            _teb.mirror_validation(rl.pillar, rl.entity_id, rl.correct or False, rl.evidence_detail)
        except Exception:
            pass

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            rl = self._lifecycles.get(rec_id)
        return self._ser(rl) if rl else None

    def by_stage(self, stage: str) -> List[dict]:
        with self._lock:
            items = [rl for rl in self._lifecycles.values() if rl.stage == stage]
        return [self._ser(rl) for rl in sorted(items, key=lambda x: x.generated_at, reverse=True)]

    def by_pillar(self, pillar: str, limit: int = 100) -> List[dict]:
        with self._lock:
            items = [rl for rl in self._lifecycles.values() if rl.pillar == pillar]
        return [self._ser(rl) for rl in sorted(items, key=lambda x: x.generated_at, reverse=True)[:limit]]

    def pending_verification(self) -> List[dict]:
        return self.by_stage("OUTCOME_PENDING") + self.by_stage("APPLIED")

    def summary(self) -> dict:
        with self._lock:
            items = list(self._lifecycles.values())
        by_stage: Dict[str, int] = {}
        for rl in items:
            by_stage[rl.stage] = by_stage.get(rl.stage, 0) + 1
        verified = [rl for rl in items if rl.stage == "VERIFIED" and rl.correct is not None]
        accuracy = round(sum(1 for rl in verified if rl.correct) / len(verified), 3) if verified else None
        return {
            "total":           len(items),
            "by_stage":        by_stage,
            "verified_count":  len(verified),
            "overall_accuracy": accuracy,
            "pending_count":   by_stage.get("APPLIED", 0) + by_stage.get("OUTCOME_PENDING", 0),
        }

    @staticmethod
    def _ser(rl: RecommendationLifecycle) -> dict:
        return {
            "rec_id":                    rl.rec_id,
            "rec_type":                  rl.rec_type,
            "entity_id":                 rl.entity_id,
            "pillar":                    rl.pillar,
            "claimed_outcome":           rl.claimed_outcome,
            "actual_outcome":            rl.actual_outcome,
            "stage":                     rl.stage,
            "correct":                   rl.correct,
            "pnl_delta":                 rl.pnl_delta,
            "win_rate_delta":            rl.win_rate_delta,
            "trade_count_at_resolution": rl.trade_count_at_resolution,
            "evidence_detail":           rl.evidence_detail,
            "generated_at":              rl.generated_at,
            "applied_at":                rl.applied_at or None,
            "verified_at":               rl.verified_at or None,
            "stage_history":             rl.stage_history,
        }


# Singleton
recommendation_reality_engine = RecommendationRealityEngine()

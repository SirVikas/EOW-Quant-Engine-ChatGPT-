"""
PHOENIX TRUST PROGRAM (PTP) — Trust Validation Registry

The PHOENIX Trust Program closes the final gap between:
  "System produces intelligence"
and
  "System has proven that intelligence is correct"

Five validation dimensions (Trust Pillars):
  1. RECOMMENDATION_ACCURACY  — % of recommendations that improved the target metric
  2. INVESTIGATION_ACCURACY   — % of investigations that identified the true root cause
  3. BLAME_ACCURACY           — % of blame attributions later confirmed by counterfactual
  4. COUNTERFACTUAL_ACCURACY  — % of counterfactuals validated against observed outcomes
  5. CONFLICT_ACCURACY        — % of conflict detections that were real (non-false-positive)

Trust Score (0–100) per pillar:
  = accuracy_rate × 60
  + evidence_weight × 20        (min(evidence_count / 50, 1.0))
  + stability_score × 20        (low variance over last 20 readings)

Trust Tier:
  90–100  INSTITUTIONAL   — can inform autonomous governance
  70–89   HIGH            — strong evidence, human oversight required
  50–69   MODERATE        — cautious use only
  30–49   LOW             — hypothesis level
  0–29    UNTRUSTED       — insufficient or contradictory evidence

At 60–90 days of operation with sufficient evidence:
  TRUST_EARNED milestone is declared per pillar.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


PILLARS = [
    "RECOMMENDATION_ACCURACY",
    "INVESTIGATION_ACCURACY",
    "BLAME_ACCURACY",
    "COUNTERFACTUAL_ACCURACY",
    "CONFLICT_ACCURACY",
]

TRUST_EARNED_THRESHOLD   = 70.0   # score needed to declare trust earned
TRUST_EARNED_MIN_EVIDENCE = 50     # minimum evidence items required


def _tier(score: float) -> str:
    if score >= 90: return "INSTITUTIONAL"
    if score >= 70: return "HIGH"
    if score >= 50: return "MODERATE"
    if score >= 30: return "LOW"
    return "UNTRUSTED"


@dataclass
class ValidationRecord:
    record_id: str
    pillar: str
    entity_id: str          # rec_id / investigation_id / blame_id / etc.
    claimed_outcome: str    # what the system claimed
    actual_outcome: str     # what actually happened
    correct: bool           # was the system right?
    evidence_detail: str    # supporting detail
    recorded_at: float = field(default_factory=time.time)


@dataclass
class PillarState:
    pillar: str
    total: int = 0
    correct: int = 0
    last_20: List[bool] = field(default_factory=list)
    first_record_at: float = 0.0
    trust_earned_at: float = 0.0

    @property
    def accuracy_rate(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.5

    @property
    def stability(self) -> float:
        if len(self.last_20) < 5:
            return 0.0
        rate = sum(self.last_20) / len(self.last_20)
        return 1.0 - abs(rate - self.accuracy_rate)

    def trust_score(self) -> float:
        acc      = self.accuracy_rate * 60
        evidence = min(self.total / TRUST_EARNED_MIN_EVIDENCE, 1.0) * 20
        stab     = self.stability * 20
        return round(min(100.0, max(0.0, acc + evidence + stab)), 1)

    @property
    def trust_earned(self) -> bool:
        return (
            self.trust_score() >= TRUST_EARNED_THRESHOLD
            and self.total >= TRUST_EARNED_MIN_EVIDENCE
        )


class TrustValidationRegistry:
    """
    Central registry for the PHOENIX Trust Program.
    Records evidence across all five trust pillars and computes institutional trust levels.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pillars: Dict[str, PillarState] = {p: PillarState(pillar=p) for p in PILLARS}
        self._records: List[ValidationRecord] = []

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_validation(
        self,
        pillar: str,
        entity_id: str,
        claimed_outcome: str,
        actual_outcome: str,
        correct: bool,
        evidence_detail: str = "",
    ) -> ValidationRecord:
        if pillar not in PILLARS:
            raise ValueError(f"Invalid pillar '{pillar}'. Must be one of {PILLARS}")

        record_id = f"TVR_{pillar[:4]}_{int(time.time() * 1000)}"
        rec = ValidationRecord(
            record_id=record_id,
            pillar=pillar,
            entity_id=entity_id,
            claimed_outcome=claimed_outcome,
            actual_outcome=actual_outcome,
            correct=correct,
            evidence_detail=evidence_detail,
        )

        with self._lock:
            self._records.append(rec)
            if len(self._records) > 5000:
                self._records = self._records[-5000:]

            state = self._pillars[pillar]
            if state.total == 0:
                state.first_record_at = time.time()
            state.total += 1
            if correct:
                state.correct += 1
            state.last_20.append(correct)
            if len(state.last_20) > 20:
                state.last_20.pop(0)

            # Check trust earned milestone
            if state.trust_earned and state.trust_earned_at == 0.0:
                state.trust_earned_at = time.time()
                self._record_trust_milestone(pillar, state)

        return rec

    # ── Query ─────────────────────────────────────────────────────────────────

    def pillar_status(self, pillar: str) -> dict:
        with self._lock:
            state = self._pillars.get(pillar)
        if not state:
            return {"error": f"Unknown pillar: {pillar}"}
        score = state.trust_score()
        return {
            "pillar":           state.pillar,
            "total_evidence":   state.total,
            "correct_count":    state.correct,
            "accuracy_rate":    round(state.accuracy_rate, 3),
            "stability":        round(state.stability, 3),
            "trust_score":      score,
            "trust_tier":       _tier(score),
            "trust_earned":     state.trust_earned,
            "trust_earned_at":  state.trust_earned_at or None,
            "first_record_at":  state.first_record_at or None,
            "evidence_needed":  max(0, TRUST_EARNED_MIN_EVIDENCE - state.total),
        }

    def all_pillars(self) -> List[dict]:
        return [self.pillar_status(p) for p in PILLARS]

    def overall_trust_health(self) -> dict:
        statuses = self.all_pillars()
        earned = [s for s in statuses if s.get("trust_earned")]
        high_plus = [s for s in statuses if _tier(s.get("trust_score", 0)) in ("HIGH", "INSTITUTIONAL")]
        avg_score = sum(s.get("trust_score", 0) for s in statuses) / len(statuses)
        return {
            "overall_trust_score": round(avg_score, 1),
            "overall_tier":        _tier(avg_score),
            "pillars_trust_earned": len(earned),
            "pillars_high_plus":   len(high_plus),
            "total_pillars":       len(PILLARS),
            "earned_pillars":      [s["pillar"] for s in earned],
            "program_maturity":    self._maturity_label(len(earned)),
            "pillar_detail":       statuses,
        }

    def records_for_pillar(self, pillar: str, limit: int = 50) -> List[dict]:
        with self._lock:
            recs = [r for r in self._records if r.pillar == pillar]
        return [self._ser_record(r) for r in sorted(recs, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _maturity_label(earned_count: int) -> str:
        if earned_count == 0:   return "EVIDENCE_ACCUMULATION"
        if earned_count <= 2:   return "PARTIAL_TRUST"
        if earned_count <= 4:   return "SUBSTANTIAL_TRUST"
        return "FULL_TRUST_EARNED"

    def _record_trust_milestone(self, pillar: str, state: PillarState) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[TRUST MILESTONE] {pillar} — Trust Earned",
                    content=(
                        f"Score: {state.trust_score()} | Evidence: {state.total} records | "
                        f"Accuracy: {state.accuracy_rate:.1%}"
                    ),
                    category="trust_milestone",
                    tags=["trust", "milestone", pillar.lower()],
                )
        except Exception:
            pass

    @staticmethod
    def _ser_record(r: ValidationRecord) -> dict:
        return {
            "record_id":      r.record_id,
            "pillar":         r.pillar,
            "entity_id":      r.entity_id,
            "claimed_outcome": r.claimed_outcome,
            "actual_outcome": r.actual_outcome,
            "correct":        r.correct,
            "evidence_detail": r.evidence_detail,
            "recorded_at":    r.recorded_at,
        }


# Singleton
trust_validation_registry = TrustValidationRegistry()

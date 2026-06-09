"""
PHOENIX TRUST PROGRAM — Trust Accuracy Ledger  [PTP-GAP-02]

The Trust Validation Registry tracks summary statistics.
The Accuracy Ledger tracks every individual claim and outcome.

For each pillar, the ledger answers:
  - Entity #47 said X would happen. Did it?
  - Over the last 30 days, how often was Investigation Accuracy correct?
  - In the 60-day window, did Blame Accuracy improve or degrade?

Validation Windows: 30 / 60 / 90 / 180 days  [PTP-GAP-01]

Each entity claim is:
  - Recorded with timestamp
  - Verified when actual outcome is known
  - Windowed for trend analysis
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


WINDOWS_DAYS = [30, 60, 90, 180]


@dataclass
class AccuracyClaim:
    claim_id: str
    pillar: str
    entity_id: str
    claimed_outcome: str
    actual_outcome: str
    correct: bool
    evidence_detail: str
    recorded_at: float = field(default_factory=time.time)
    verified_at: float = 0.0


class TrustAccuracyLedger:
    """
    Per-entity claim tracking with multi-window accuracy analysis.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._claims: List[AccuracyClaim] = []

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(
        self,
        pillar: str,
        entity_id: str,
        claimed_outcome: str,
        actual_outcome: str,
        correct: bool,
        evidence_detail: str = "",
    ) -> AccuracyClaim:
        claim_id = f"ACL_{pillar[:4]}_{int(time.time()*1000)}"
        c = AccuracyClaim(
            claim_id=claim_id,
            pillar=pillar,
            entity_id=entity_id,
            claimed_outcome=claimed_outcome,
            actual_outcome=actual_outcome,
            correct=correct,
            evidence_detail=evidence_detail,
            verified_at=time.time(),
        )
        with self._lock:
            self._claims.append(c)
            if len(self._claims) > 10000:
                self._claims = self._claims[-10000:]
        return c

    # ── Window Analysis ───────────────────────────────────────────────────────

    def window_accuracy(self, pillar: str, days: int) -> dict:
        cutoff = time.time() - days * 86400
        with self._lock:
            relevant = [c for c in self._claims if c.pillar == pillar and c.recorded_at >= cutoff]
        if not relevant:
            return {"pillar": pillar, "window_days": days, "count": 0, "accuracy": None, "note": "No data"}
        correct = sum(1 for c in relevant if c.correct)
        return {
            "pillar":      pillar,
            "window_days": days,
            "count":       len(relevant),
            "correct":     correct,
            "accuracy":    round(correct / len(relevant), 3),
            "trend":       self._trend(relevant),
        }

    def all_windows(self, pillar: str) -> List[dict]:
        return [self.window_accuracy(pillar, d) for d in WINDOWS_DAYS]

    def all_pillars_windows(self) -> dict:
        try:
            from core.trust.trust_validation_registry import PILLARS
        except Exception:
            PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        return {p: self.all_windows(p) for p in PILLARS}

    def entity_history(self, entity_id: str) -> List[dict]:
        with self._lock:
            items = [c for c in self._claims if c.entity_id == entity_id]
        return [self._ser(c) for c in sorted(items, key=lambda x: x.recorded_at, reverse=True)]

    def recent_claims(self, pillar: str, limit: int = 50) -> List[dict]:
        with self._lock:
            items = [c for c in self._claims if c.pillar == pillar]
        return [self._ser(c) for c in sorted(items, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _trend(claims: List[AccuracyClaim]) -> str:
        if len(claims) < 6:
            return "insufficient_data"
        mid = len(claims) // 2
        first_half = sum(1 for c in claims[:mid] if c.correct) / mid
        second_half = sum(1 for c in claims[mid:] if c.correct) / (len(claims) - mid)
        if second_half - first_half > 0.05:
            return "improving"
        if first_half - second_half > 0.05:
            return "degrading"
        return "stable"

    @staticmethod
    def _ser(c: AccuracyClaim) -> dict:
        return {
            "claim_id":       c.claim_id,
            "pillar":         c.pillar,
            "entity_id":      c.entity_id,
            "claimed_outcome": c.claimed_outcome,
            "actual_outcome": c.actual_outcome,
            "correct":        c.correct,
            "evidence_detail": c.evidence_detail,
            "recorded_at":    c.recorded_at,
        }


# Singleton
trust_accuracy_ledger = TrustAccuracyLedger()

"""
PHOENIX OBSERVATORY-X — Recommendation Trust Engine

A recommendation without a track record is an opinion.
The Trust Engine converts recommendations into evidence-based, scored advice.

Trust dimensions (five-factor model)
────────────────────────────────────
  1. Accuracy Rate        — % of past recommendations of this type that improved the metric
  2. Damage Score         — severity of harm when recommendation was wrong (0=harmless, 10=severe)
  3. False Positive Rate  — % of recommendations that flagged a non-existent problem
  4. False Negative Rate  — % of real problems that this rec type failed to surface
  5. Stability Score      — consistency of trust over time (avoids noise-driven trust swings)

Trust Score (0–100):
  = (accuracy_rate × 40)
  + ((1 - damage_score/10) × 20)
  + ((1 - fpr) × 20)
  + ((1 - fnr) × 10)
  + (stability × 10)

Trust tiers:
  90–100  INSTITUTIONAL   — can be auto-acted on (with human oversight)
  70–89   HIGH            — strong evidence base, act with monitoring
  50–69   MODERATE        — use cautiously, require human review
  30–49   LOW             — treat as hypothesis, not recommendation
  0–29    UNTRUSTED       — insufficient evidence or consistently wrong

Each recommendation type accumulates trust data as outcomes are recorded.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Tier Definitions ──────────────────────────────────────────────────────────

def _trust_tier(score: float) -> str:
    if score >= 90: return "INSTITUTIONAL"
    if score >= 70: return "HIGH"
    if score >= 50: return "MODERATE"
    if score >= 30: return "LOW"
    return "UNTRUSTED"


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class RecommendationOutcome:
    recommendation_id: str
    rec_type: str
    applied_at: float
    outcome: str           # "improved" | "no_change" | "worsened" | "unknown"
    metric_before: float   # target metric value before applying
    metric_after: float    # target metric value after monitoring window
    trades_monitored: int
    false_positive: bool   # problem didn't actually exist
    damage: float          # 0–10: how much harm caused by wrong recommendation


@dataclass
class RecTypeTrust:
    rec_type: str
    total_outcomes: int = 0
    improved_count: int = 0
    worsened_count: int = 0
    no_change_count: int = 0
    false_positive_count: int = 0
    false_negative_count: int = 0
    total_damage: float = 0.0
    last_updated: float = field(default_factory=time.time)

    @property
    def accuracy_rate(self) -> float:
        if self.total_outcomes == 0:
            return 0.5  # prior = 50% until evidence
        return self.improved_count / self.total_outcomes

    @property
    def fpr(self) -> float:
        if self.total_outcomes == 0:
            return 0.2
        return self.false_positive_count / max(1, self.total_outcomes)

    @property
    def fnr(self) -> float:
        """False Negative Rate: estimated as worsened / total (proxy)."""
        if self.total_outcomes == 0:
            return 0.2
        return self.worsened_count / max(1, self.total_outcomes)

    @property
    def avg_damage(self) -> float:
        if self.total_outcomes == 0:
            return 1.0   # moderate prior damage risk
        return self.total_damage / self.total_outcomes

    def trust_score(self) -> float:
        accuracy   = self.accuracy_rate * 40
        safety     = (1 - min(self.avg_damage / 10, 1)) * 20
        fpr_score  = (1 - self.fpr) * 20
        fnr_score  = (1 - self.fnr) * 10
        # Stability: penalise if fewer than 5 outcomes (low evidence)
        stability  = min(1.0, self.total_outcomes / 5) * 10
        return round(min(100.0, max(0.0, accuracy + safety + fpr_score + fnr_score + stability)), 1)


# ── Engine ────────────────────────────────────────────────────────────────────

class RecommendationTrustEngine:
    """
    Tracks recommendation accuracy and computes trust scores per recommendation type.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._type_trust: Dict[str, RecTypeTrust] = {}
        self._outcomes: List[RecommendationOutcome] = []
        self._bootstrap_priors()

    # ── Outcome Recording ─────────────────────────────────────────────────────

    def record_outcome(self, outcome: RecommendationOutcome) -> None:
        """Record the result of applying a recommendation."""
        with self._lock:
            trust = self._type_trust.setdefault(
                outcome.rec_type, RecTypeTrust(rec_type=outcome.rec_type)
            )
            trust.total_outcomes += 1
            if outcome.outcome == "improved":
                trust.improved_count += 1
            elif outcome.outcome == "worsened":
                trust.worsened_count += 1
            else:
                trust.no_change_count += 1
            if outcome.false_positive:
                trust.false_positive_count += 1
            trust.total_damage += outcome.damage
            trust.last_updated = time.time()
            self._outcomes.append(outcome)
            # Keep only last 500
            if len(self._outcomes) > 500:
                self._outcomes = self._outcomes[-500:]

    # ── Trust Query ───────────────────────────────────────────────────────────

    def trust_for_type(self, rec_type: str) -> dict:
        with self._lock:
            trust = self._type_trust.get(rec_type)
        if not trust:
            return {
                "rec_type":    rec_type,
                "trust_score": 30.0,   # default = LOW (untested)
                "trust_tier":  "LOW",
                "evidence_count": 0,
                "note": "No outcome data. Score is prior.",
            }
        score = trust.trust_score()
        return {
            "rec_type":          trust.rec_type,
            "trust_score":       score,
            "trust_tier":        _trust_tier(score),
            "evidence_count":    trust.total_outcomes,
            "accuracy_rate":     round(trust.accuracy_rate, 3),
            "false_positive_rate": round(trust.fpr, 3),
            "false_negative_rate": round(trust.fnr, 3),
            "avg_damage":        round(trust.avg_damage, 2),
            "last_updated":      trust.last_updated,
        }

    def trust_all(self) -> List[dict]:
        with self._lock:
            types = list(self._type_trust.keys())
        return sorted(
            [self.trust_for_type(t) for t in types],
            key=lambda x: x["trust_score"],
            reverse=True,
        )

    def annotate_recommendation(self, rec: dict) -> dict:
        """Add trust score and tier to a recommendation dict."""
        trust = self.trust_for_type(rec.get("rec_type", ""))
        return {
            **rec,
            "trust_score": trust["trust_score"],
            "trust_tier":  trust["trust_tier"],
            "evidence_count": trust["evidence_count"],
        }

    def summary(self) -> dict:
        with self._lock:
            total_types = len(self._type_trust)
            total_outcomes = len(self._outcomes)
        all_t = self.trust_all()
        institutional = [t for t in all_t if t["trust_tier"] == "INSTITUTIONAL"]
        untrusted     = [t for t in all_t if t["trust_tier"] == "UNTRUSTED"]
        return {
            "total_rec_types":      total_types,
            "total_outcomes":       total_outcomes,
            "institutional_types":  [t["rec_type"] for t in institutional],
            "untrusted_types":      [t["rec_type"] for t in untrusted],
            "overall_trust_health": "good" if len(untrusted) == 0 else "needs_data",
            "type_scores":          all_t,
        }

    # ── Bootstrap Priors ──────────────────────────────────────────────────────
    # Provide informed priors so the engine isn't completely blind from day 0.
    # These are overridden as real outcome data accumulates.

    def _bootstrap_priors(self) -> None:
        # Conservative priors for known rec types based on domain knowledge
        _PRIORS = [
            # (rec_type, improved, worsened, no_change, fp, damage)
            ("REDUCE_WEIGHT",        2, 0, 1, 0, 0.5),  # Low risk, usually helps
            ("DISABLE_WINDOW",       1, 1, 1, 1, 1.0),  # Moderate risk, can miss trades
            ("REVIEW_MODULE",        3, 0, 0, 0, 0.0),  # Very low risk (advisory only)
            ("FORCE_GOVERNANCE_RUN", 2, 0, 1, 0, 0.0),  # Essentially zero risk
            ("INVESTIGATE_DATA",     2, 0, 1, 0, 0.0),  # Zero risk
            ("NO_ACTION",            0, 0, 3, 0, 0.0),  # Passive
            ("REDUCE_EXPOSURE",      1, 1, 1, 0, 1.5),  # Can reduce profit
            ("INCREASE_THRESHOLD",   1, 1, 1, 1, 1.0),  # Can reduce trade count
        ]
        with self._lock:
            for rt, imp, wor, noc, fp, dmg in _PRIORS:
                total = imp + wor + noc
                t = RecTypeTrust(rec_type=rt, total_outcomes=total,
                                 improved_count=imp, worsened_count=wor,
                                 no_change_count=noc, false_positive_count=fp,
                                 total_damage=dmg * total)
                self._type_trust[rt] = t


# Singleton
recommendation_trust_engine = RecommendationTrustEngine()

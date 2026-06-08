"""
PHOENIX OBSERVATORY-X — Truth Layer

Institutional systems require three distinct states for any observation:

  OBSERVED   Data collected, report generated.
             "We know what happened."

  EXPLAINED  Root cause analysis complete, contributing factors identified.
             "We know why it happened."

  VERIFIED   A fix was applied and its effectiveness confirmed over N trades.
             "We know the problem is resolved."

The gap between OBSERVED and VERIFIED is where most institutional systems
fail — they observe and generate recommendations, but never close the loop.

Truth Lifecycle
───────────────
  OBSERVED
      ↓  (defect scan / inspector runs)
  EXPLAINED
      ↓  (recommendation applied + N trades monitored)
  VERIFIED     ← or →  REFUTED  (fix didn't work)
      ↓
  CLOSED

Every Observatory event (defect, investigation, recommendation) carries a
TruthState.  The Truth Layer tracks the evidence chain from observation to
verified resolution.

Evidence requirements:
  OBSERVED → EXPLAINED   : requires InvestigationReport with confidence ≥ 0.5
  EXPLAINED → VERIFIED   : requires post-fix monitoring of ≥ 50 trades showing
                           improvement ≥ 10% on the target metric
  EXPLAINED → REFUTED    : post-fix monitoring shows no improvement or regression
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ── Truth States ──────────────────────────────────────────────────────────────

class TruthState(str, Enum):
    OBSERVED  = "observed"
    EXPLAINED = "explained"
    VERIFIED  = "verified"
    REFUTED   = "refuted"
    CLOSED    = "closed"

_STATE_ORDER = {
    TruthState.OBSERVED:  0,
    TruthState.EXPLAINED: 1,
    TruthState.VERIFIED:  2,
    TruthState.REFUTED:   2,
    TruthState.CLOSED:    3,
}

# Minimum evidence requirements for state transitions
EXPLAINED_MIN_CONFIDENCE = 0.50   # investigation confidence to move OBSERVED→EXPLAINED
VERIFIED_MIN_TRADES      = 50     # post-fix trades required before declaring VERIFIED
VERIFIED_MIN_IMPROVEMENT = 0.10   # 10 % improvement on the target metric


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class EvidenceEntry:
    stage: str               # "observation" | "investigation" | "fix_applied" | "monitoring"
    description: str
    confidence: float        # 0–1
    source: str              # module / system that provided this evidence
    timestamp: float = field(default_factory=time.time)
    data: Dict = field(default_factory=dict)


@dataclass
class TruthRecord:
    truth_id: str
    subject: str             # what this truth record is about (defect_id, report_key, etc.)
    subject_type: str        # "defect" | "loss_cluster" | "report_anomaly" | "custom"
    state: TruthState
    created_at: float
    last_transition: float
    description: str
    evidence_chain: List[EvidenceEntry] = field(default_factory=list)
    investigation_id: Optional[str] = None
    recommendation_ids: List[str] = field(default_factory=list)
    post_fix_trades_monitored: int = 0
    post_fix_improvement_pct: Optional[float] = None
    resolved_at: Optional[float] = None
    transition_history: List[dict] = field(default_factory=list)


# ── Truth Layer ───────────────────────────────────────────────────────────────

class ObservatoryTruthLayer:
    """
    Tracks the evidence chain for every Observatory finding from
    initial observation through to verified resolution.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, TruthRecord] = {}

    # ── Record Lifecycle ──────────────────────────────────────────────────────

    def observe(
        self,
        subject: str,
        subject_type: str,
        description: str,
        source: str,
        confidence: float = 1.0,
        data: Optional[Dict] = None,
    ) -> TruthRecord:
        """Create a new OBSERVED truth record."""
        truth_id = f"TR_{subject_type.upper()}_{int(time.time())}_{subject[:20]}"
        now = time.time()
        rec = TruthRecord(
            truth_id=truth_id,
            subject=subject,
            subject_type=subject_type,
            state=TruthState.OBSERVED,
            created_at=now,
            last_transition=now,
            description=description,
        )
        rec.evidence_chain.append(EvidenceEntry(
            stage="observation",
            description=description,
            confidence=confidence,
            source=source,
            data=data or {},
        ))
        with self._lock:
            self._records[truth_id] = rec
        return rec

    def explain(
        self,
        truth_id: str,
        investigation_id: str,
        explanation: str,
        confidence: float,
        source: str = "phoenix_inspector",
        causes: Optional[List[dict]] = None,
    ) -> bool:
        """
        Transition OBSERVED → EXPLAINED.
        Requires confidence ≥ EXPLAINED_MIN_CONFIDENCE.
        Returns True if transition succeeded.
        """
        if confidence < EXPLAINED_MIN_CONFIDENCE:
            return False
        with self._lock:
            rec = self._records.get(truth_id)
            if not rec or rec.state != TruthState.OBSERVED:
                return False
            self._transition(rec, TruthState.EXPLAINED,
                             f"Investigation complete: {explanation}")
            rec.investigation_id = investigation_id
            rec.evidence_chain.append(EvidenceEntry(
                stage="investigation",
                description=explanation,
                confidence=confidence,
                source=source,
                data={"causes": causes or [], "investigation_id": investigation_id},
            ))
        return True

    def apply_fix(
        self,
        truth_id: str,
        fix_description: str,
        recommendation_id: str,
        source: str = "manual",
    ) -> bool:
        """Record that a fix has been applied. State remains EXPLAINED until verified."""
        with self._lock:
            rec = self._records.get(truth_id)
            if not rec or rec.state != TruthState.EXPLAINED:
                return False
            if recommendation_id not in rec.recommendation_ids:
                rec.recommendation_ids.append(recommendation_id)
            rec.evidence_chain.append(EvidenceEntry(
                stage="fix_applied",
                description=fix_description,
                confidence=0.5,   # fix applied but not yet confirmed
                source=source,
                data={"recommendation_id": recommendation_id},
            ))
        return True

    def record_monitoring(
        self,
        truth_id: str,
        trades_since_fix: int,
        improvement_pct: float,
        metric_name: str,
        source: str = "validation_tracker",
    ) -> str:
        """
        Record post-fix monitoring results.
        Returns new state string.
        Auto-transitions to VERIFIED or REFUTED when evidence threshold reached.
        """
        with self._lock:
            rec = self._records.get(truth_id)
            if not rec or rec.state not in (TruthState.EXPLAINED,):
                return rec.state.value if rec else "not_found"

            rec.post_fix_trades_monitored = trades_since_fix
            rec.post_fix_improvement_pct  = improvement_pct

            rec.evidence_chain.append(EvidenceEntry(
                stage="monitoring",
                description=(
                    f"{trades_since_fix} trades monitored post-fix. "
                    f"{metric_name} improvement: {improvement_pct:.1%}"
                ),
                confidence=min(1.0, trades_since_fix / VERIFIED_MIN_TRADES),
                source=source,
                data={
                    "trades": trades_since_fix,
                    "improvement_pct": improvement_pct,
                    "metric": metric_name,
                },
            ))

            if trades_since_fix >= VERIFIED_MIN_TRADES:
                if improvement_pct >= VERIFIED_MIN_IMPROVEMENT:
                    self._transition(rec, TruthState.VERIFIED,
                                     f"Verified: {improvement_pct:.1%} improvement over "
                                     f"{trades_since_fix} trades")
                    rec.resolved_at = time.time()
                else:
                    self._transition(rec, TruthState.REFUTED,
                                     f"Refuted: only {improvement_pct:.1%} improvement "
                                     f"({VERIFIED_MIN_IMPROVEMENT:.0%} required)")

            return rec.state.value

    def close(self, truth_id: str, reason: str = "") -> bool:
        with self._lock:
            rec = self._records.get(truth_id)
            if not rec:
                return False
            self._transition(rec, TruthState.CLOSED, reason or "Manually closed")
            rec.resolved_at = time.time()
        return True

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, truth_id: str) -> Optional[dict]:
        with self._lock:
            rec = self._records.get(truth_id)
        return self._serialise(rec) if rec else None

    def by_state(self, state: TruthState) -> List[dict]:
        with self._lock:
            records = [r for r in self._records.values() if r.state == state]
        return [self._serialise(r) for r in records]

    def summary(self) -> dict:
        with self._lock:
            by_state: Dict[str, int] = {}
            for r in self._records.values():
                by_state[r.state.value] = by_state.get(r.state.value, 0) + 1
        return {
            "total_records":         len(self._records),
            "by_state":              by_state,
            "observed_unexplained":  by_state.get("observed", 0),
            "explained_unverified":  by_state.get("explained", 0),
            "verified":              by_state.get("verified", 0),
            "refuted":               by_state.get("refuted", 0),
            "truth_gap": (
                by_state.get("observed", 0) + by_state.get("explained", 0)
            ),
            "thresholds": {
                "explained_min_confidence": EXPLAINED_MIN_CONFIDENCE,
                "verified_min_trades":      VERIFIED_MIN_TRADES,
                "verified_min_improvement": VERIFIED_MIN_IMPROVEMENT,
            },
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _transition(rec: TruthRecord, new_state: TruthState, reason: str) -> None:
        rec.transition_history.append({
            "from":      rec.state.value,
            "to":        new_state.value,
            "reason":    reason,
            "timestamp": time.time(),
        })
        rec.state = new_state
        rec.last_transition = time.time()

    @staticmethod
    def _serialise(rec: TruthRecord) -> dict:
        return {
            "truth_id":             rec.truth_id,
            "subject":              rec.subject,
            "subject_type":         rec.subject_type,
            "state":                rec.state.value,
            "description":          rec.description,
            "created_at":           rec.created_at,
            "last_transition":      rec.last_transition,
            "resolved_at":          rec.resolved_at,
            "investigation_id":     rec.investigation_id,
            "recommendation_ids":   rec.recommendation_ids,
            "post_fix_trades":      rec.post_fix_trades_monitored,
            "post_fix_improvement": rec.post_fix_improvement_pct,
            "evidence_chain": [
                {
                    "stage":       e.stage,
                    "description": e.description,
                    "confidence":  e.confidence,
                    "source":      e.source,
                    "timestamp":   e.timestamp,
                    "data":        e.data,
                }
                for e in rec.evidence_chain
            ],
            "transition_history": rec.transition_history,
        }


# Singleton
observatory_truth_layer = ObservatoryTruthLayer()

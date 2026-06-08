"""
PHOENIX OBSERVATORY-X — Recommendation Outcome Registry  [OX-GAP-01]

A recommendation without a measured outcome is still an opinion.
This registry closes the loop: when a recommendation is marked Applied,
we track live trade counts and compute metric deltas at checkpoints.

Lifecycle:
  Generated → Applied → Monitoring (30-trade checkpoint) → Final (100-trade) → Archived

At each checkpoint, win-rate delta and profit-factor delta are recorded.
Outcomes feed back into the RecommendationTrustEngine to build evidence.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


CHECKPOINT_30  = 30
CHECKPOINT_100 = 100


def _outcome_label(wr_delta: float, pf_delta: float) -> str:
    if wr_delta >= 0.03 or pf_delta >= 0.05:
        return "improved"
    if wr_delta <= -0.03 or pf_delta <= -0.05:
        return "worsened"
    return "no_change"


@dataclass
class OutcomeCheckpoint:
    at_trade_count: int
    wr_before: float
    wr_after: float
    pf_before: float
    pf_after: float
    label: str
    recorded_at: float = field(default_factory=time.time)


@dataclass
class TrackedRecommendation:
    rec_id: str
    rec_type: str
    title: str
    action: str
    investigation_id: str
    applied_at: float
    baseline_trade_count: int    # trade count at the moment of application
    baseline_wr: float           # win-rate at application
    baseline_pf: float           # profit-factor at application
    status: str = "monitoring"   # monitoring | checkpoint_30 | final | archived
    checkpoints: List[OutcomeCheckpoint] = field(default_factory=list)
    final_outcome: str = "unknown"   # improved | no_change | worsened | unknown


class RecommendationOutcomeRegistry:
    """
    Tracks applied recommendations through 30-trade and 100-trade outcome windows.
    Feeds confirmed outcomes into the RecommendationTrustEngine.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tracked: Dict[str, TrackedRecommendation] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def register_applied(
        self,
        rec_id: str,
        rec_type: str,
        title: str,
        action: str,
        investigation_id: str,
        current_trade_count: int,
        current_wr: float,
        current_pf: float,
    ) -> TrackedRecommendation:
        rec = TrackedRecommendation(
            rec_id=rec_id,
            rec_type=rec_type,
            title=title,
            action=action,
            investigation_id=investigation_id,
            applied_at=time.time(),
            baseline_trade_count=current_trade_count,
            baseline_wr=current_wr,
            baseline_pf=current_pf,
        )
        with self._lock:
            self._tracked[rec_id] = rec
        return rec

    # ── Checkpoint Update ─────────────────────────────────────────────────────

    def update_metrics(
        self,
        rec_id: str,
        current_trade_count: int,
        current_wr: float,
        current_pf: float,
    ) -> Optional[OutcomeCheckpoint]:
        """
        Call this periodically (e.g. after each trade) to update tracking.
        Returns a checkpoint dict when a milestone is crossed, else None.
        """
        with self._lock:
            rec = self._tracked.get(rec_id)
            if not rec or rec.status == "archived":
                return None

            elapsed = current_trade_count - rec.baseline_trade_count
            checkpoint = None

            if rec.status == "monitoring" and elapsed >= CHECKPOINT_30:
                label = _outcome_label(
                    current_wr - rec.baseline_wr,
                    current_pf - rec.baseline_pf,
                )
                cp = OutcomeCheckpoint(
                    at_trade_count=CHECKPOINT_30,
                    wr_before=rec.baseline_wr,
                    wr_after=current_wr,
                    pf_before=rec.baseline_pf,
                    pf_after=current_pf,
                    label=label,
                )
                rec.checkpoints.append(cp)
                rec.status = "checkpoint_30"
                checkpoint = cp

            if rec.status == "checkpoint_30" and elapsed >= CHECKPOINT_100:
                label = _outcome_label(
                    current_wr - rec.baseline_wr,
                    current_pf - rec.baseline_pf,
                )
                cp = OutcomeCheckpoint(
                    at_trade_count=CHECKPOINT_100,
                    wr_before=rec.baseline_wr,
                    wr_after=current_wr,
                    pf_before=rec.baseline_pf,
                    pf_after=current_pf,
                    label=label,
                )
                rec.checkpoints.append(cp)
                rec.final_outcome = label
                rec.status = "final"
                checkpoint = cp
                self._feed_trust_engine(rec)

        return checkpoint

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            rec = self._tracked.get(rec_id)
        return self._serialise(rec) if rec else None

    def all_tracked(self, status_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._tracked.values())
        if status_filter:
            items = [r for r in items if r.status == status_filter]
        return [self._serialise(r) for r in items]

    def summary(self) -> dict:
        with self._lock:
            all_r = list(self._tracked.values())
        counts = {}
        for r in all_r:
            counts[r.status] = counts.get(r.status, 0) + 1
        finals = [r for r in all_r if r.status == "final"]
        improved = sum(1 for r in finals if r.final_outcome == "improved")
        return {
            "total_tracked": len(all_r),
            "by_status": counts,
            "final_count": len(finals),
            "improved_count": improved,
            "improvement_rate": round(improved / max(1, len(finals)), 3),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _feed_trust_engine(self, rec: TrackedRecommendation) -> None:
        try:
            from core.observatory.trust_engine import (
                recommendation_trust_engine,
                RecommendationOutcome,
            )
            outcome = RecommendationOutcome(
                recommendation_id=rec.rec_id,
                rec_type=rec.rec_type,
                applied_at=rec.applied_at,
                outcome=rec.final_outcome,
                metric_before=rec.baseline_wr,
                metric_after=rec.checkpoints[-1].wr_after if rec.checkpoints else rec.baseline_wr,
                trades_monitored=CHECKPOINT_100,
                false_positive=rec.final_outcome == "no_change" and rec.checkpoints[0].label == "no_change",
                damage=2.0 if rec.final_outcome == "worsened" else 0.0,
            )
            recommendation_trust_engine.record_outcome(outcome)
        except Exception:
            pass

    @staticmethod
    def _serialise(rec: TrackedRecommendation) -> dict:
        return {
            "rec_id":               rec.rec_id,
            "rec_type":             rec.rec_type,
            "title":                rec.title,
            "action":               rec.action,
            "investigation_id":     rec.investigation_id,
            "applied_at":           rec.applied_at,
            "status":               rec.status,
            "final_outcome":        rec.final_outcome,
            "baseline_wr":          rec.baseline_wr,
            "baseline_pf":          rec.baseline_pf,
            "checkpoints": [
                {
                    "at_trade_count": cp.at_trade_count,
                    "wr_before":      cp.wr_before,
                    "wr_after":       cp.wr_after,
                    "pf_before":      cp.pf_before,
                    "pf_after":       cp.pf_after,
                    "wr_delta":       round(cp.wr_after - cp.wr_before, 4),
                    "pf_delta":       round(cp.pf_after - cp.pf_before, 4),
                    "label":          cp.label,
                    "recorded_at":    cp.recorded_at,
                }
                for cp in rec.checkpoints
            ],
        }


# Singleton
recommendation_outcome_registry = RecommendationOutcomeRegistry()

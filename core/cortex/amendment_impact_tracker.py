"""
PHOENIX CORTEX — Amendment Impact Tracker  [GAP-R7]

Tracks the observable impact of each constitutional amendment.

After an article is amended, the tracker monitors:
  - Did constitutional risk scores change?
  - Did conflict rates increase or decrease?
  - Did court ruling patterns shift?
  - Did governance stress test pass rates change?

Each amendment gets a before/after snapshot.
The tracker answers: "What actually improved or worsened after this change?"
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AmendmentImpactRecord:
    amendment_id: str
    article_id: str
    amendment_summary: str
    baseline_snapshot: dict   # captured BEFORE amendment
    post_snapshot: dict       # captured AFTER amendment (N days later)
    impact_delta: dict        # computed differences
    verdict: str = "PENDING"  # POSITIVE / NEUTRAL / NEGATIVE / PENDING
    tracked_since: float = field(default_factory=time.time)
    evaluated_at: float = 0.0


class AmendmentImpactTracker:
    """
    Before/after impact analysis for every constitutional amendment.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, AmendmentImpactRecord] = {}

    def _capture_snapshot(self, article_id: str) -> dict:
        snap: Dict = {"captured_at": time.time(), "article_id": article_id}
        try:
            from core.cortex.constitution import cortex_constitution
            risk = cortex_constitution.constitutional_risk_score({"type": "governance_action"})
            snap["risk_score"] = risk.get("total_score", 0)
            snap["risk_label"] = risk.get("risk_label", "UNKNOWN")
        except Exception:
            pass
        try:
            from core.cortex.governance_stress_test import governance_stress_test
            latest = governance_stress_test.latest_run()
            snap["stress_consistency"] = latest.get("consistency_score") if latest else None
        except Exception:
            pass
        try:
            from core.cortex.constitutional_court import constitutional_court
            summary = constitutional_court.summary()
            snap["total_court_cases"]  = summary.get("total_cases", 0)
            snap["approved_cases"]     = summary.get("approved", 0)
        except Exception:
            pass
        return snap

    def register_amendment(self, amendment_id: str, article_id: str, summary: str) -> AmendmentImpactRecord:
        baseline = self._capture_snapshot(article_id)
        record = AmendmentImpactRecord(
            amendment_id=amendment_id,
            article_id=article_id,
            amendment_summary=summary,
            baseline_snapshot=baseline,
            post_snapshot={},
            impact_delta={},
        )
        with self._lock:
            self._records[amendment_id] = record

        # Record in constitutional history
        try:
            from core.cortex.constitutional_history import constitutional_history
            constitutional_history.record(
                change_type="AMENDMENT_RATIFIED",
                subject_id=amendment_id,
                summary=f"Amendment impact tracking started: {summary}",
                actor="SYSTEM",
                detail={"baseline": baseline},
            )
        except Exception:
            pass

        return record

    def evaluate_impact(self, amendment_id: str) -> dict:
        with self._lock:
            record = self._records.get(amendment_id)
        if not record:
            return {"error": f"Amendment '{amendment_id}' not tracked"}

        post = self._capture_snapshot(record.article_id)
        record.post_snapshot = post
        record.evaluated_at = time.time()

        delta = {}
        for key in ("risk_score", "stress_consistency", "total_court_cases", "approved_cases"):
            before = record.baseline_snapshot.get(key)
            after  = post.get(key)
            if before is not None and after is not None:
                delta[key] = {"before": before, "after": after, "change": round(after - before, 3)}

        record.impact_delta = delta

        # Determine verdict
        risk_change = delta.get("risk_score", {}).get("change", 0)
        stress_change = delta.get("stress_consistency", {}).get("change", 0)
        if risk_change < 0 or stress_change > 0:
            record.verdict = "POSITIVE"
        elif risk_change > 5 or stress_change < -5:
            record.verdict = "NEGATIVE"
        else:
            record.verdict = "NEUTRAL"

        return self._ser(record)

    def all_records(self) -> List[dict]:
        with self._lock:
            items = list(self._records.values())
        return [self._ser(r) for r in sorted(items, key=lambda x: x.tracked_since, reverse=True)]

    def by_article(self, article_id: str) -> List[dict]:
        with self._lock:
            items = [r for r in self._records.values() if r.article_id == article_id]
        return [self._ser(r) for r in items]

    @staticmethod
    def _ser(r: AmendmentImpactRecord) -> dict:
        return {
            "amendment_id":      r.amendment_id,
            "article_id":        r.article_id,
            "amendment_summary": r.amendment_summary,
            "verdict":           r.verdict,
            "impact_delta":      r.impact_delta,
            "tracked_since":     r.tracked_since,
            "evaluated_at":      r.evaluated_at or None,
            "baseline_risk":     r.baseline_snapshot.get("risk_score"),
            "post_risk":         r.post_snapshot.get("risk_score"),
        }


# Singleton
amendment_impact_tracker = AmendmentImpactTracker()

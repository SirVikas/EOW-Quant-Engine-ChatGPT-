"""
PHOENIX AEG — Longitudinal Performance Tracker  [GAP-R5]

Tracks AEG recommendation performance over 30/60/90/180 day horizons
with historical survival analysis.

Unlike event-oriented tracking (individual outcomes), longitudinal tracking asks:
  - Is the 30-day accuracy IMPROVING or DEGRADING over time?
  - Did a rec_type's performance survive a 90-day horizon?
  - What is the half-life of a recommendation's predictive accuracy?

Analysis:
  - Rolling window accuracy (accuracy as of N days ago)
  - Cohort analysis (recommendations from same week — how did they age?)
  - Decay curve (accuracy at t=0, t=30, t=60, t=90, t=180)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

LONGITUDINAL_WINDOWS = [30, 60, 90, 180]


@dataclass
class LongitudinalRecord:
    rec_id: str
    rec_type: str
    correct: bool
    pnl_delta: float
    generated_at: float = field(default_factory=time.time)
    verified_at: float = field(default_factory=time.time)


class AEGLongitudinalTracker:
    """
    Historical survival analysis for AEG recommendation classes.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[LongitudinalRecord] = []

    def record(
        self,
        rec_id: str,
        rec_type: str,
        correct: bool,
        pnl_delta: float = 0.0,
        generated_at: Optional[float] = None,
    ) -> LongitudinalRecord:
        r = LongitudinalRecord(
            rec_id=rec_id,
            rec_type=rec_type,
            correct=correct,
            pnl_delta=pnl_delta,
            generated_at=generated_at or time.time(),
            verified_at=time.time(),
        )
        with self._lock:
            self._records.append(r)
            if len(self._records) > 100_000:
                self._records = self._records[-100_000:]
        return r

    def rolling_accuracy(self, rec_type: str, days: int) -> dict:
        cutoff = time.time() - days * 86400
        with self._lock:
            items = [r for r in self._records if r.rec_type == rec_type and r.verified_at >= cutoff]
        if not items:
            return {"rec_type": rec_type, "window_days": days, "count": 0, "accuracy": None}
        correct = sum(1 for r in items if r.correct)
        net_pnl = sum(r.pnl_delta for r in items)
        return {
            "rec_type":    rec_type,
            "window_days": days,
            "count":       len(items),
            "correct":     correct,
            "accuracy":    round(correct / len(items), 3),
            "net_pnl":     round(net_pnl, 4),
        }

    def all_windows_for_type(self, rec_type: str) -> List[dict]:
        return [self.rolling_accuracy(rec_type, d) for d in LONGITUDINAL_WINDOWS]

    def decay_curve(self, rec_type: str) -> dict:
        """
        Shows how accuracy DECAYS over time for older cohorts.
        Splits records into age buckets: 0-30d, 30-60d, 60-90d, 90-180d.
        """
        now = time.time()
        buckets = {
            "0-30d":   (0,          30 * 86400),
            "30-60d":  (30 * 86400, 60 * 86400),
            "60-90d":  (60 * 86400, 90 * 86400),
            "90-180d": (90 * 86400, 180 * 86400),
        }
        with self._lock:
            items = [r for r in self._records if r.rec_type == rec_type]

        curve = {}
        for label, (lo, hi) in buckets.items():
            cohort = [r for r in items if lo <= (now - r.verified_at) < hi]
            if cohort:
                correct = sum(1 for r in cohort if r.correct)
                curve[label] = {
                    "count":    len(cohort),
                    "accuracy": round(correct / len(cohort), 3),
                }
            else:
                curve[label] = {"count": 0, "accuracy": None}

        # Compute half-life (window where accuracy first drops below 50%)
        half_life = None
        for label, data in curve.items():
            if data["accuracy"] is not None and data["accuracy"] < 0.50:
                half_life = label
                break

        return {
            "rec_type":  rec_type,
            "decay_curve": curve,
            "half_life_bucket": half_life or "NOT_REACHED",
        }

    def survival_analysis(self, rec_type: str) -> dict:
        windows = self.all_windows_for_type(rec_type)
        decay = self.decay_curve(rec_type)

        # Does accuracy hold at 90 days?
        w90 = next((w for w in windows if w["window_days"] == 90), {})
        acc_90 = w90.get("accuracy")
        w30  = next((w for w in windows if w["window_days"] == 30), {})
        acc_30 = w30.get("accuracy")

        if acc_30 is not None and acc_90 is not None:
            degradation = round(acc_30 - acc_90, 3) if acc_30 else 0
            verdict = "STABLE" if degradation < 0.10 else ("DEGRADING" if degradation < 0.25 else "RAPID_DECAY")
        else:
            verdict = "INSUFFICIENT_DATA"

        return {
            "rec_type":        rec_type,
            "windows":         windows,
            "decay_curve":     decay["decay_curve"],
            "half_life_bucket": decay["half_life_bucket"],
            "degradation_30_to_90": (round(acc_30 - acc_90, 3) if acc_30 and acc_90 else None),
            "survival_verdict": verdict,
        }

    def all_types_survival(self) -> List[dict]:
        with self._lock:
            types = list(set(r.rec_type for r in self._records))
        return [self.survival_analysis(rt) for rt in types]

    def longitudinal_summary(self) -> dict:
        with self._lock:
            total = len(self._records)
        analyses = self.all_types_survival()
        stable = sum(1 for a in analyses if a["survival_verdict"] == "STABLE")
        return {
            "total_records":    total,
            "rec_types_tracked": len(analyses),
            "stable":           stable,
            "degrading":        sum(1 for a in analyses if a["survival_verdict"] == "DEGRADING"),
            "rapid_decay":      sum(1 for a in analyses if a["survival_verdict"] == "RAPID_DECAY"),
            "insufficient":     sum(1 for a in analyses if a["survival_verdict"] == "INSUFFICIENT_DATA"),
        }


# Singleton
aeg_longitudinal_tracker = AEGLongitudinalTracker()

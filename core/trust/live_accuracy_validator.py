"""
PHOENIX TRUST PROGRAM — Live Accuracy Validator  [GAP-001]

Produces validated accuracy reports for 30/60/90/180 day windows
across all five trust pillars, using the TrustAccuracyLedger as source.

Answers: "Is this pillar actually accurate over time?"
  - Per-window accuracy with trend direction
  - Minimum evidence thresholds per window
  - Confidence rating: PROVEN / ACCUMULATING / INSUFFICIENT
  - Cross-pillar comparison snapshot
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

WINDOWS_DAYS = [30, 60, 90, 180]
MIN_EVIDENCE_FOR_PROVEN = {30: 10, 60: 20, 90: 30, 180: 50}
ACCURACY_TIERS = [
    (0.85, "EXCELLENT"),
    (0.70, "GOOD"),
    (0.55, "FAIR"),
    (0.0,  "POOR"),
]


def _accuracy_tier(acc: Optional[float]) -> str:
    if acc is None:
        return "UNKNOWN"
    for threshold, label in ACCURACY_TIERS:
        if acc >= threshold:
            return label
    return "POOR"


def _confidence(count: int, days: int) -> str:
    required = MIN_EVIDENCE_FOR_PROVEN.get(days, 10)
    if count >= required:
        return "PROVEN"
    if count >= required // 2:
        return "ACCUMULATING"
    return "INSUFFICIENT"


class LiveAccuracyValidator:
    """
    Generates structured accuracy validation reports from the TrustAccuracyLedger.
    """

    def pillar_report(self, pillar: str) -> dict:
        from core.trust.trust_accuracy_ledger import trust_accuracy_ledger as _tal
        windows = []
        for days in WINDOWS_DAYS:
            w = _tal.window_accuracy(pillar, days)
            acc = w.get("accuracy")
            count = w.get("count", 0)
            windows.append({
                **w,
                "accuracy_tier": _accuracy_tier(acc),
                "confidence":    _confidence(count, days),
            })
        best_window = max(
            (w for w in windows if w.get("accuracy") is not None),
            key=lambda x: x.get("count", 0),
            default=None,
        )
        return {
            "pillar":      pillar,
            "windows":     windows,
            "best_accuracy": best_window.get("accuracy") if best_window else None,
            "best_window_days": best_window.get("window_days") if best_window else None,
            "overall_tier":    _accuracy_tier(best_window.get("accuracy") if best_window else None),
            "generated_at":    time.time(),
        }

    def all_pillars_report(self) -> dict:
        try:
            from core.trust.trust_validation_registry import PILLARS
        except Exception:
            PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        reports = {p: self.pillar_report(p) for p in PILLARS}
        proven = sum(
            1 for r in reports.values()
            if any(w["confidence"] == "PROVEN" for w in r["windows"])
        )
        return {
            "pillars":          reports,
            "total_pillars":    len(PILLARS),
            "proven_pillars":   proven,
            "accumulating":     len(PILLARS) - proven,
            "program_accuracy_health": "PROVEN" if proven == len(PILLARS) else (
                "ACCUMULATING" if proven > 0 else "INSUFFICIENT"
            ),
            "generated_at": time.time(),
        }

    def window_comparison(self, days: int) -> List[dict]:
        try:
            from core.trust.trust_validation_registry import PILLARS
        except Exception:
            PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        from core.trust.trust_accuracy_ledger import trust_accuracy_ledger as _tal
        results = []
        for p in PILLARS:
            w = _tal.window_accuracy(p, days)
            acc = w.get("accuracy")
            results.append({
                "pillar":        p,
                "window_days":   days,
                "accuracy":      acc,
                "count":         w.get("count", 0),
                "trend":         w.get("trend", "insufficient_data"),
                "accuracy_tier": _accuracy_tier(acc),
                "confidence":    _confidence(w.get("count", 0), days),
            })
        return sorted(results, key=lambda x: (x.get("accuracy") or 0), reverse=True)


# Singleton
live_accuracy_validator = LiveAccuracyValidator()

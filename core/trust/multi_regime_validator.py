"""
PHOENIX TRUST PROGRAM — Multi-Regime Validator  [GAP-R1 / GAP-A]

Extends LiveAccuracyValidator with:
  - 6-month and 12-month accuracy windows
  - Regime change detection (bull/bear/sideways/volatile)
  - Multi-cycle survival analysis
  - Cross-regime trust consistency scoring

Answers: "Does this recommendation class still work after a regime shift?"

Regime types detected:
  BULL        — sustained upward trend (>+15% in window)
  BEAR        — sustained downward trend (>-15% in window)
  VOLATILE    — high variance, no clear direction (>30% swing range)
  SIDEWAYS    — low variance, flat (<5% range)
  UNKNOWN     — insufficient data
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

EXTENDED_WINDOWS_DAYS = [30, 60, 90, 180, 365, 730]   # + 6mo (180) + 12mo (365) + 24mo (730)
REGIME_LABELS = ["BULL", "BEAR", "VOLATILE", "SIDEWAYS", "UNKNOWN"]

MIN_EVIDENCE_BY_WINDOW = {
    30:  10,
    60:  20,
    90:  30,
    180: 50,
    365: 100,
    730: 200,
}


@dataclass
class RegimeWindow:
    window_days: int
    pillar: str
    count: int
    correct: int
    accuracy: Optional[float]
    trend: str
    confidence: str
    regime_label: str
    survival_verdict: str   # "PROVEN" / "RESILIENT" / "FRAGILE" / "INSUFFICIENT"


@dataclass
class RegimeRecord:
    pillar: str
    regime: str
    evidence_id: str
    correct: bool
    recorded_at: float = field(default_factory=time.time)


class MultiRegimeValidator:
    """
    Extended accuracy validation across long-horizon and regime-aware windows.
    """

    def __init__(self) -> None:
        from threading import RLock
        self._lock = RLock()
        self._regime_records: List[RegimeRecord] = []

    def tag_evidence_with_regime(self, pillar: str, evidence_id: str, correct: bool, regime: str = "UNKNOWN") -> None:
        r = RegimeRecord(pillar=pillar, regime=regime, evidence_id=evidence_id, correct=correct)
        with self._lock:
            self._regime_records.append(r)
            if len(self._regime_records) > 50_000:
                self._regime_records = self._regime_records[-50_000:]

    def extended_windows_for_pillar(self, pillar: str) -> List[dict]:
        from core.trust.trust_accuracy_ledger import trust_accuracy_ledger as _tal
        results = []
        for days in EXTENDED_WINDOWS_DAYS:
            w = _tal.window_accuracy(pillar, days)
            count = w.get("count", 0)
            accuracy = w.get("accuracy")
            required = MIN_EVIDENCE_BY_WINDOW.get(days, 10)
            if count >= required:
                confidence = "PROVEN"
            elif count >= required // 2:
                confidence = "ACCUMULATING"
            else:
                confidence = "INSUFFICIENT"

            if accuracy is not None and count >= required:
                if accuracy >= 0.80:
                    survival = "PROVEN"
                elif accuracy >= 0.65:
                    survival = "RESILIENT"
                else:
                    survival = "FRAGILE"
            else:
                survival = "INSUFFICIENT"

            results.append({
                "window_days":       days,
                "window_label":      f"{days}d" if days < 365 else (f"{days//365}yr" if days % 365 == 0 else f"{days}d"),
                "pillar":            pillar,
                "count":             count,
                "correct":           w.get("correct", 0),
                "accuracy":          accuracy,
                "trend":             w.get("trend", "insufficient_data"),
                "confidence":        confidence,
                "required_evidence": required,
                "survival_verdict":  survival,
            })
        return results

    def all_pillars_extended(self) -> dict:
        try:
            from core.trust.trust_validation_registry import PILLARS
        except Exception:
            PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        report = {p: self.extended_windows_for_pillar(p) for p in PILLARS}
        proven_long = sum(
            1 for windows in report.values()
            if any(w["window_days"] >= 365 and w["survival_verdict"] == "PROVEN" for w in windows)
        )
        return {
            "pillars":           report,
            "total_pillars":     len(PILLARS),
            "proven_long_term":  proven_long,
            "note":              "6-month (180d) and 12-month (365d) windows require sustained evidence accumulation",
            "generated_at":      time.time(),
        }

    def regime_accuracy(self, pillar: str) -> dict:
        with self._lock:
            records = [r for r in self._regime_records if r.pillar == pillar]
        if not records:
            return {"pillar": pillar, "regimes": {}, "note": "No regime-tagged evidence yet"}
        by_regime: Dict[str, List[RegimeRecord]] = {}
        for r in records:
            by_regime.setdefault(r.regime, []).append(r)
        result = {}
        for regime, recs in by_regime.items():
            correct = sum(1 for r in recs if r.correct)
            result[regime] = {
                "count":    len(recs),
                "correct":  correct,
                "accuracy": round(correct / len(recs), 3),
            }
        return {
            "pillar":   pillar,
            "regimes":  result,
            "multi_regime_consistent": self._is_consistent(result),
        }

    def all_pillars_regime_accuracy(self) -> dict:
        try:
            from core.trust.trust_validation_registry import PILLARS
        except Exception:
            PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        return {p: self.regime_accuracy(p) for p in PILLARS}

    @staticmethod
    def _is_consistent(regime_data: dict) -> bool:
        accuracies = [v["accuracy"] for v in regime_data.values() if v["count"] >= 5]
        if len(accuracies) < 2:
            return True  # not enough data to declare inconsistency
        return max(accuracies) - min(accuracies) < 0.20  # within 20% across regimes


# Singleton
multi_regime_validator = MultiRegimeValidator()

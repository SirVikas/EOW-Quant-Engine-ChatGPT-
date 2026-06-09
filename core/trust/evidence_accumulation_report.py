"""
PHOENIX PTP — Evidence Accumulation Report  [GAP-EAP-01, GAP-EAP-02]

GAP-EAP-01: Multi-Regime Evidence Collection
  - Summarises how many evidence records exist per market regime
  - Identifies regime gaps (e.g. no BEAR market evidence yet)
  - Produces regime coverage score

GAP-EAP-02: Long-Term Evidence Collection / Trust Survival Report
  - Shows evidence density in each time window (30/60/90/180/365d)
  - Computes trust score stability over time (did it hold up?)
  - Identifies windows where trust would have survived vs collapsed
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

REGIMES = ["BULL", "BEAR", "SIDEWAYS", "VOLATILE", "UNKNOWN"]
SURVIVAL_WINDOWS = [30, 60, 90, 180, 365]
SURVIVAL_MIN_SCORE = 40.0     # trust score must stay above this to "survive"
SURVIVAL_MIN_EVIDENCE = 5     # minimum evidence per window to count


@dataclass
class RegimeCoverage:
    pillar: str
    regime: str
    evidence_count: int
    accuracy: Optional[float]
    coverage_label: str    # STRONG / ADEQUATE / SPARSE / NONE


@dataclass
class TrustSurvivalWindow:
    pillar: str
    window_days: int
    evidence_count: int
    avg_trust_score: float
    min_trust_score: float
    max_trust_score: float
    survived: bool           # stayed above SURVIVAL_MIN_SCORE throughout
    confidence: str          # HIGH / MEDIUM / LOW / INSUFFICIENT


class EvidenceAccumulationReport:
    """
    Multi-regime and long-term evidence accumulation reports for PTP.
    """

    # ── GAP-EAP-01: Multi-Regime Report ──────────────────────────────────────

    def multi_regime_report(self, pillar: Optional[str] = None) -> dict:
        try:
            from config import PTP_PILLARS
            pillars = [pillar] if pillar else PTP_PILLARS
        except Exception:
            pillars = [pillar] if pillar else [
                "RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY",
            ]

        all_coverage = []
        regime_totals: Dict[str, int] = {r: 0 for r in REGIMES}

        for p in pillars:
            for regime in REGIMES:
                try:
                    from core.trust.multi_regime_validator import multi_regime_validator as _mrv
                    by_regime = _mrv.regime_accuracy(p)
                    rdata = by_regime.get(regime, {})
                    count = rdata.get("evidence_count", 0)
                    acc   = rdata.get("accuracy")
                except Exception:
                    count = 0
                    acc   = None

                regime_totals[regime] += count
                label = ("STRONG" if count >= 30 else
                         "ADEQUATE" if count >= 10 else
                         "SPARSE" if count >= 1 else "NONE")
                all_coverage.append(RegimeCoverage(
                    pillar=p, regime=regime,
                    evidence_count=count, accuracy=acc,
                    coverage_label=label,
                ))

        # Regime gap analysis
        gaps = [r for r in REGIMES if regime_totals.get(r, 0) == 0 and r != "UNKNOWN"]
        coverage_score = sum(1 for r in ["BULL", "BEAR", "SIDEWAYS", "VOLATILE"]
                             if regime_totals.get(r, 0) >= 10) / 4 * 100

        return {
            "pillars_analysed":  len(pillars),
            "regime_totals":     regime_totals,
            "regime_gaps":       gaps,
            "coverage_score":    round(coverage_score, 1),
            "coverage_label":    ("FULL" if coverage_score >= 75 else
                                  "PARTIAL" if coverage_score >= 25 else "SPARSE"),
            "coverage_by_pillar_regime": [
                {
                    "pillar":          c.pillar,
                    "regime":          c.regime,
                    "evidence_count":  c.evidence_count,
                    "accuracy":        round(c.accuracy, 4) if c.accuracy is not None else None,
                    "coverage_label":  c.coverage_label,
                }
                for c in all_coverage
            ],
            "generated_at": time.time(),
        }

    # ── GAP-EAP-02: Trust Survival Report ────────────────────────────────────

    def trust_survival_report(self, pillar: Optional[str] = None) -> dict:
        try:
            from config import PTP_PILLARS
            pillars = [pillar] if pillar else PTP_PILLARS
        except Exception:
            pillars = [pillar] if pillar else [
                "RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY",
            ]

        all_windows = []
        now = time.time()

        for p in pillars:
            try:
                from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
                evidence = _tew.for_pillar(p)
            except Exception:
                evidence = []

            for days in SURVIVAL_WINDOWS:
                cutoff = now - days * 86400
                window_ev = [e for e in evidence if e.get("recorded_at", 0) >= cutoff]
                count = len(window_ev)

                if count < SURVIVAL_MIN_EVIDENCE:
                    all_windows.append(TrustSurvivalWindow(
                        pillar=p, window_days=days, evidence_count=count,
                        avg_trust_score=0.0, min_trust_score=0.0, max_trust_score=0.0,
                        survived=False, confidence="INSUFFICIENT",
                    ))
                    continue

                scores = [e.get("trust_score_at_recording", 50.0) for e in window_ev]
                avg = sum(scores) / len(scores)
                mn  = min(scores)
                mx  = max(scores)
                survived = mn >= SURVIVAL_MIN_SCORE
                confidence = ("HIGH" if count >= 30 else
                              "MEDIUM" if count >= 10 else "LOW")
                all_windows.append(TrustSurvivalWindow(
                    pillar=p, window_days=days, evidence_count=count,
                    avg_trust_score=round(avg, 2), min_trust_score=round(mn, 2),
                    max_trust_score=round(mx, 2), survived=survived,
                    confidence=confidence,
                ))

        survived_count = sum(1 for w in all_windows
                             if w.survived and w.confidence != "INSUFFICIENT")
        total_meaningful = sum(1 for w in all_windows if w.confidence != "INSUFFICIENT")
        survival_rate = survived_count / max(1, total_meaningful)

        return {
            "pillars_analysed":  len(pillars),
            "windows_analysed":  len(all_windows),
            "survival_rate":     round(survival_rate, 3),
            "survival_label":    ("PROVEN" if survival_rate >= 0.80 else
                                  "DEVELOPING" if survival_rate >= 0.40 else "INSUFFICIENT"),
            "windows": [
                {
                    "pillar":           w.pillar,
                    "window_days":      w.window_days,
                    "evidence_count":   w.evidence_count,
                    "avg_trust_score":  w.avg_trust_score,
                    "min_trust_score":  w.min_trust_score,
                    "max_trust_score":  w.max_trust_score,
                    "survived":         w.survived,
                    "confidence":       w.confidence,
                }
                for w in all_windows
            ],
            "generated_at": time.time(),
        }

    def full_accumulation_report(self) -> dict:
        return {
            "multi_regime":   self.multi_regime_report(),
            "trust_survival": self.trust_survival_report(),
            "generated_at":   time.time(),
        }


# Singleton
evidence_accumulation_report = EvidenceAccumulationReport()

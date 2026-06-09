"""
PHOENIX NEXUS — Institutional Health Index  [CLI-03]

Single score (0–100) measuring the health of the entire PHOENIX institution.

Component scores (each 0–100):
  NEXUS    — memory records, knowledge density
  OBSX     — recommendation accuracy, disease detections
  CORTEX   — governance consistency, amendment impact
  PTP      — trust scores, evidence density, calibration
  AEG      — readiness index, promotion success
  PCAO     — risk profile, decision support quality

Aggregation: weighted average
Final label: CRITICAL / DEGRADED / STABLE / HEALTHY / OPTIMAL
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


COMPONENT_WEIGHTS = {
    "NEXUS":   0.10,
    "OBSX":    0.15,
    "CORTEX":  0.15,
    "PTP":     0.25,
    "AEG":     0.20,
    "PCAO":    0.15,
}

HEALTH_LABELS = [
    (90, "OPTIMAL"),
    (75, "HEALTHY"),
    (55, "STABLE"),
    (35, "DEGRADED"),
    (0,  "CRITICAL"),
]


@dataclass
class HealthSnapshot:
    overall_score: float
    health_label: str
    component_scores: Dict[str, float]
    critical_components: List[str]
    warnings: List[str]
    computed_at: float = field(default_factory=time.time)


class InstitutionalHealthIndex:
    """
    Computes PHOENIX-wide institutional health from all layer metrics.
    """

    def _score_nexus(self) -> tuple[float, List[str]]:
        warnings = []
        try:
            from core.nexus.institutional_memory.imraf import imraf
            records = len(imraf._records) if hasattr(imraf, "_records") else 0
        except Exception:
            records = 0
        try:
            from core.ema.ema_engine import ema_engine
            facts = ema_engine.fact_count() if hasattr(ema_engine, "fact_count") else 10
        except Exception:
            facts = 10

        score = min(100, records * 0.5 + facts * 1.0)
        if records < 50:
            warnings.append(f"NEXUS: Only {records} IMRAF records")
        return round(score, 1), warnings

    def _score_obsx(self) -> tuple[float, List[str]]:
        warnings = []
        try:
            from core.observatory.long_term_archive import long_term_archive as _lta
            summ = _lta.summary()
            total = summ.get("total_archived", 0)
            score = min(100, total * 2.0)
        except Exception:
            score = 50.0
        if score < 40:
            warnings.append("OBSX: Low recommendation archive density")
        return round(score, 1), warnings

    def _score_cortex(self) -> tuple[float, List[str]]:
        warnings = []
        try:
            from core.cortex.governance_consistency_audit import governance_consistency_audit as _gca
            report = _gca.latest_report()
            if report:
                label = report.get("consistency_label", "MODERATE")
                label_score = {"HIGH": 90, "MODERATE": 65, "LOW": 35}.get(label, 50)
            else:
                label_score = 50
        except Exception:
            label_score = 50
        try:
            from core.cortex.governance_stress_test import governance_stress_test as _gst
            latest = _gst.latest_run()
            stress_score = latest.get("consistency_score", 70) if latest else 70
        except Exception:
            stress_score = 70
        score = (label_score + stress_score) / 2
        if score < 50:
            warnings.append("CORTEX: Governance consistency below threshold")
        return round(score, 1), warnings

    def _score_ptp(self) -> tuple[float, List[str]]:
        warnings = []
        try:
            from core.trust.trust_validation_registry import trust_validation_registry as _tvr
            try:
                from config import PTP_PILLARS
                pillars = PTP_PILLARS
            except Exception:
                pillars = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                           "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
            scores = []
            for p in pillars:
                s = _tvr.pillar_status(p)
                scores.append(s.get("trust_score", 0))
            avg_score = sum(scores) / max(1, len(scores))
        except Exception:
            avg_score = 30.0

        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            evidence_count = audit.get("total_evidence", 0)
            evidence_factor = min(1.0, evidence_count / 100.0)
        except Exception:
            evidence_factor = 0.3

        score = avg_score * 0.7 + evidence_factor * 100 * 0.3
        if avg_score < 40:
            warnings.append("PTP: Average trust score below 40")
        if evidence_factor < 0.3:
            warnings.append("PTP: Evidence density low")
        return round(score, 1), warnings

    def _score_aeg(self) -> tuple[float, List[str]]:
        warnings = []
        try:
            from core.nexus.aeg_pipeline.aeg_validation_program import aeg_validation_program as _avp
            readiness = _avp.autonomy_readiness_index()
            score = readiness.get("readiness_score", 20.0)
        except Exception:
            score = 20.0
        if score < 40:
            warnings.append(f"AEG: Readiness index {score:.0f}/100 — not yet promotion-ready")
        return round(score, 1), warnings

    def _score_pcao(self) -> tuple[float, List[str]]:
        warnings = []
        try:
            from core.pcao.risk_office import risk_office as _ro
            dashboard = _ro.risk_dashboard()
            critical = dashboard.get("critical_open", 0)
            high = dashboard.get("high_open", 0)
            risk_penalty = critical * 15 + high * 8
            score = max(0, 80 - risk_penalty)
        except Exception:
            score = 50.0
            critical = 0
        if critical > 0:
            warnings.append(f"PCAO: {critical} CRITICAL open risks")
        return round(score, 1), warnings

    def compute(self) -> HealthSnapshot:
        component_scores: Dict[str, float] = {}
        all_warnings: List[str] = []
        scorers = {
            "NEXUS": self._score_nexus,
            "OBSX":  self._score_obsx,
            "CORTEX": self._score_cortex,
            "PTP":   self._score_ptp,
            "AEG":   self._score_aeg,
            "PCAO":  self._score_pcao,
        }
        for layer, scorer in scorers.items():
            try:
                s, w = scorer()
                component_scores[layer] = s
                all_warnings.extend(w)
            except Exception:
                component_scores[layer] = 50.0

        overall = sum(component_scores[k] * COMPONENT_WEIGHTS[k]
                      for k in COMPONENT_WEIGHTS)
        overall = round(overall, 1)

        label = "CRITICAL"
        for threshold, lbl in HEALTH_LABELS:
            if overall >= threshold:
                label = lbl
                break

        critical_components = [k for k, v in component_scores.items() if v < 40]
        return HealthSnapshot(
            overall_score=overall,
            health_label=label,
            component_scores=component_scores,
            critical_components=critical_components,
            warnings=all_warnings,
        )

    def health_report(self) -> dict:
        snap = self.compute()
        return {
            "overall_score":       snap.overall_score,
            "health_label":        snap.health_label,
            "component_scores":    snap.component_scores,
            "component_weights":   COMPONENT_WEIGHTS,
            "critical_components": snap.critical_components,
            "warnings":            snap.warnings,
            "interpretation":      f"PHOENIX institutional health: {snap.overall_score:.1f}/100 — {snap.health_label}",
            "computed_at":         snap.computed_at,
        }

    def critical_components(self) -> List[dict]:
        snap = self.compute()
        return [
            {"component": c, "score": snap.component_scores.get(c, 0)}
            for c in snap.critical_components
        ]


# Singleton
institutional_health_index = InstitutionalHealthIndex()

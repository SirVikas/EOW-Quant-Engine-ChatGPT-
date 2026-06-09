"""
PHOENIX CORTEX — Governance Metrics  [GOV-01, GOV-02, GOV-03]

GOV-01: Constitutional Metrics     — Article usage, court usage, precedent usage
GOV-02: Governance Performance Score — Single governance effectiveness KPI (0–100)
GOV-03: Amendment Success Tracking  — Before/after measurement registry

Deliverable: Governance Metrics Dashboard + KPI Framework
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AmendmentOutcome:
    amendment_id: str
    title: str
    article_affected: str
    enacted_at: float
    before_risk_score: float
    after_risk_score: float
    risk_delta: float
    before_stress_score: float
    after_stress_score: float
    stress_delta: float
    outcome_label: str      # IMPROVED / NEUTRAL / DEGRADED
    measured_at: float = field(default_factory=time.time)


class GovernanceMetrics:
    """
    Governance measurement layer: metrics, KPIs, and amendment outcome tracking.
    """

    # ── GOV-01: Constitutional Metrics ────────────────────────────────────────

    def constitutional_metrics(self) -> dict:
        metrics: Dict[str, Any] = {}

        # Article usage: how many times each article cited in court cases / rulings
        try:
            from core.cortex.constitutional_court import constitutional_court as _cc
            cases = _cc.all_cases() if hasattr(_cc, "all_cases") else []
            article_usage: Dict[str, int] = {}
            for case in cases:
                article = case.get("article_id") or case.get("subject_id", "")
                if article.startswith("ARTICLE"):
                    article_usage[article] = article_usage.get(article, 0) + 1
            metrics["article_usage"] = article_usage
            metrics["total_court_cases"] = len(cases)
        except Exception:
            metrics["article_usage"] = {}
            metrics["total_court_cases"] = 0

        # Precedent usage: how many precedents reference each article
        try:
            from core.cortex.constitutional_precedents import constitutional_precedents as _cp
            all_prec = _cp.all_precedents() if hasattr(_cp, "all_precedents") else []
            prec_by_article: Dict[str, int] = {}
            for p in all_prec:
                article = p.get("article_id", "UNKNOWN")
                prec_by_article[article] = prec_by_article.get(article, 0) + 1
            metrics["precedent_usage"] = prec_by_article
            metrics["total_precedents"] = len(all_prec)
        except Exception:
            metrics["precedent_usage"] = {}
            metrics["total_precedents"] = 0

        # Amendment count
        try:
            from core.cortex.constitutional_history import constitutional_history as _ch
            history = _ch.by_type("AMENDMENT_ENACTED")
            metrics["amendments_enacted"] = len(history)
        except Exception:
            metrics["amendments_enacted"] = 0

        # Commentary coverage: articles with commentary
        try:
            from core.cortex.constitutional_commentary import constitutional_commentary as _cc2
            comms = _cc2.all_commentaries()
            metrics["articles_with_commentary"] = len(comms)
        except Exception:
            metrics["articles_with_commentary"] = 0

        metrics["generated_at"] = time.time()
        return metrics

    # ── GOV-02: Governance Performance Score ─────────────────────────────────

    def governance_kpi(self) -> dict:
        scores: Dict[str, float] = {}

        # Court consistency
        try:
            from core.cortex.governance_consistency_audit import governance_consistency_audit as _gca
            report = _gca.latest_report()
            if report:
                label = report.get("consistency_label", "MODERATE")
                scores["consistency"] = {"HIGH": 90, "MODERATE": 65, "LOW": 35}.get(label, 50)
            else:
                scores["consistency"] = 50
        except Exception:
            scores["consistency"] = 50

        # Stress test pass rate
        try:
            from core.cortex.governance_stress_test import governance_stress_test as _gst
            latest = _gst.latest_run()
            scores["stress_test"] = latest.get("consistency_score", 60) if latest else 60
        except Exception:
            scores["stress_test"] = 60

        # Amendment success rate
        try:
            outcomes = self._load_amendment_outcomes()
            improved = sum(1 for o in outcomes if o.outcome_label == "IMPROVED")
            total = len(outcomes)
            scores["amendment_success"] = (improved / max(1, total)) * 100 if total > 0 else 70
        except Exception:
            scores["amendment_success"] = 70

        # Evidence supremacy compliance
        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine as _ese
            summ = _ese.summary()
            total_checks = summ.get("total_checks", 1)
            permitted = summ.get("permitted", 0)
            blocked   = summ.get("blocked", 0)
            # High compliance = most actions were either correctly permitted or correctly blocked
            compliance_rate = (permitted + blocked) / max(1, total_checks)
            scores["ese_compliance"] = min(100, compliance_rate * 100)
        except Exception:
            scores["ese_compliance"] = 70

        # Court case resolution rate
        try:
            from core.cortex.constitutional_court import constitutional_court as _cc
            cases = _cc.all_cases() if hasattr(_cc, "all_cases") else []
            resolved = sum(1 for c in cases if c.get("status") in ("VERDICT_ISSUED", "CLOSED"))
            scores["case_resolution"] = (resolved / max(1, len(cases))) * 100 if cases else 75
        except Exception:
            scores["case_resolution"] = 75

        weights = {
            "consistency":        0.25,
            "stress_test":        0.20,
            "amendment_success":  0.20,
            "ese_compliance":     0.20,
            "case_resolution":    0.15,
        }
        overall = sum(scores.get(k, 50) * w for k, w in weights.items())
        overall = round(overall, 1)

        label = ("EXCELLENT" if overall >= 85 else "GOOD" if overall >= 70 else
                 "ADEQUATE" if overall >= 55 else "NEEDS_IMPROVEMENT")

        return {
            "governance_score":     overall,
            "governance_label":     label,
            "component_scores":     {k: round(v, 1) for k, v in scores.items()},
            "weights":              weights,
            "interpretation":       f"Governance effectiveness: {overall:.1f}/100 — {label}",
            "generated_at":         time.time(),
        }

    # ── GOV-03: Amendment Success Tracking ───────────────────────────────────

    def _load_amendment_outcomes(self) -> List[AmendmentOutcome]:
        outcomes = []
        try:
            from core.cortex.amendment_impact_tracker import amendment_impact_tracker as _ait
            impacts = _ait.all_impacts()
            for impact in impacts:
                if impact.get("verdict") in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
                    before = impact.get("before_snapshot", {})
                    after  = impact.get("after_snapshot", {})
                    risk_before = before.get("risk_score", 50)
                    risk_after  = after.get("risk_score", 50) if after else risk_before
                    stress_before = before.get("stress_consistency", 70)
                    stress_after  = after.get("stress_consistency", 70) if after else stress_before
                    label = "IMPROVED" if impact.get("verdict") == "POSITIVE" else (
                        "DEGRADED" if impact.get("verdict") == "NEGATIVE" else "NEUTRAL"
                    )
                    outcomes.append(AmendmentOutcome(
                        amendment_id=impact.get("amendment_id", ""),
                        title=impact.get("title", ""),
                        article_affected=impact.get("article_affected", ""),
                        enacted_at=impact.get("registered_at", time.time()),
                        before_risk_score=risk_before,
                        after_risk_score=risk_after,
                        risk_delta=risk_after - risk_before,
                        before_stress_score=stress_before,
                        after_stress_score=stress_after,
                        stress_delta=stress_after - stress_before,
                        outcome_label=label,
                    ))
        except Exception:
            pass
        return outcomes

    def amendment_outcome_registry(self) -> dict:
        outcomes = self._load_amendment_outcomes()
        improved = sum(1 for o in outcomes if o.outcome_label == "IMPROVED")
        neutral  = sum(1 for o in outcomes if o.outcome_label == "NEUTRAL")
        degraded = sum(1 for o in outcomes if o.outcome_label == "DEGRADED")
        return {
            "total_tracked":  len(outcomes),
            "improved":       improved,
            "neutral":        neutral,
            "degraded":       degraded,
            "success_rate":   round(improved / max(1, len(outcomes)), 3) if outcomes else None,
            "entries": [
                {
                    "amendment_id":   o.amendment_id,
                    "title":          o.title,
                    "article":        o.article_affected,
                    "risk_delta":     round(o.risk_delta, 1),
                    "stress_delta":   round(o.stress_delta, 1),
                    "outcome_label":  o.outcome_label,
                }
                for o in sorted(outcomes, key=lambda x: x.enacted_at, reverse=True)
            ],
            "generated_at": time.time(),
        }

    def governance_dashboard(self) -> dict:
        return {
            "constitutional_metrics": self.constitutional_metrics(),
            "governance_kpi":         self.governance_kpi(),
            "amendment_outcomes":     self.amendment_outcome_registry(),
        }


# Singleton
governance_metrics = GovernanceMetrics()

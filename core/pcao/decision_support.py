"""
PHOENIX PCAO — Executive Decision Support  [GAP-R10]

Answers: "What should we do next?"

The Decision Support Engine synthesizes intelligence from all layers
and produces a prioritized set of strategic recommendations with rationale.

Unlike the Risk Office (what can go wrong), Decision Support answers:
  - What is the highest-leverage action available right now?
  - What is blocking progress that can be unblocked?
  - What evidence is needed before the next promotion?
  - What is the most constrained subsystem?

Output format:
  - RECOMMENDATIONS: ordered list of specific actions
  - BLOCKERS: what must resolve before next milestone
  - OPPORTUNITIES: quick wins available now
"""
from __future__ import annotations

import time
from typing import Any, Dict, List


class DecisionSupport:
    """
    Synthesizes cross-layer intelligence into actionable strategic recommendations.
    """

    def generate_recommendations(self) -> dict:
        recommendations: List[dict] = []
        blockers: List[dict] = []
        opportunities: List[dict] = []
        context: Dict[str, Any] = {}

        self._check_trust_evidence(recommendations, blockers, opportunities, context)
        self._check_aeg_pipeline(recommendations, blockers, opportunities, context)
        self._check_pcao_objectives(recommendations, blockers, opportunities, context)
        self._check_risk_office(recommendations, blockers, opportunities, context)
        self._check_evidence_supremacy(recommendations, blockers, opportunities, context)

        return {
            "generated_at":    time.time(),
            "recommendations": sorted(recommendations, key=lambda x: x.get("urgency_score", 0), reverse=True)[:10],
            "blockers":        blockers[:5],
            "opportunities":   opportunities[:5],
            "top_action":      recommendations[0]["action"] if recommendations else "Continue evidence accumulation across all pillars",
            "context_snapshot": context,
        }

    def _check_trust_evidence(self, recs, blockers, opps, ctx) -> None:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            total = audit.get("total_evidence", 0)
            ctx["evidence_total"] = total
            if total < 100:
                blockers.append({
                    "blocker": "Trust evidence count low",
                    "detail":  f"Only {total} evidence records — need 100+ for PROVEN status",
                    "action":  "Record recommendation outcomes via /api/observatory/reality/<rec_id>/outcome",
                })
            if total >= 50:
                opps.append({
                    "opportunity": "First pillars approaching PROVEN status",
                    "action":      "Run /api/trust/accuracy/report to identify closest pillar",
                })
        except Exception:
            pass

        try:
            from core.trust.live_accuracy_validator import live_accuracy_validator
            report = live_accuracy_validator.all_pillars_report()
            proven = report.get("proven_pillars", 0)
            ctx["proven_pillars"] = proven
            if proven < 5:
                recs.append({
                    "action":        f"Accumulate validation evidence ({proven}/5 pillars PROVEN)",
                    "rationale":     "Trust Program cannot advance until pillars are proven",
                    "urgency_score": 8,
                    "layer":         "PTP",
                })
        except Exception:
            pass

    def _check_aeg_pipeline(self, recs, blockers, opps, ctx) -> None:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            summary = aeg_promotion_engine.summary()
            candidates = summary.get("promotion_candidates", 0)
            live = summary.get("live_recommendations", 0)
            ctx["aeg_candidates"] = candidates
            ctx["aeg_live"] = live
            if candidates > 0:
                opps.append({
                    "opportunity": f"{candidates} AEG promotion candidates awaiting review",
                    "action":      "Review at /api/nexus/aeg/oversight and approve/reject",
                })
            if live == 0:
                recs.append({
                    "action":        "Build sandbox evidence for AEG promotion",
                    "rationale":     "No live AEG recommendations yet",
                    "urgency_score": 6,
                    "layer":         "AEG",
                })
        except Exception:
            pass

        try:
            from core.nexus.aeg_pipeline.aeg_shadow_mode import aeg_shadow_mode
            shadow_summary = aeg_shadow_mode.summary()
            if shadow_summary.get("graduated_sessions", 0) == 0:
                recs.append({
                    "action":        "Start AEG shadow validation program",
                    "rationale":     "Shadow validation required before full AEG autonomy",
                    "urgency_score": 7,
                    "layer":         "AEG",
                })
        except Exception:
            pass

    def _check_pcao_objectives(self, recs, blockers, opps, ctx) -> None:
        try:
            from core.pcao.strategic_planner import strategic_planner
            sequence = strategic_planner.sequence_programs()
            top3 = sequence.get("top_3", [])
            for item in top3[:2]:
                recs.append({
                    "action":        item["title"],
                    "rationale":     item["rationale"],
                    "urgency_score": item["score"],
                    "layer":         item["subsystem"],
                })
        except Exception:
            pass

    def _check_risk_office(self, recs, blockers, opps, ctx) -> None:
        try:
            from core.pcao.risk_office import risk_office
            dashboard = risk_office.risk_dashboard()
            critical = dashboard.get("critical_open", 0)
            high = dashboard.get("high_open", 0)
            ctx["critical_risks"] = critical
            ctx["high_risks"] = high
            if critical > 0:
                recs.append({
                    "action":        f"Resolve {critical} CRITICAL open risk(s)",
                    "rationale":     "Critical risks threaten system stability",
                    "urgency_score": 10,
                    "layer":         "PCAO",
                })
            if high > 0:
                recs.append({
                    "action":        f"Address {high} HIGH severity risk(s) this sprint",
                    "rationale":     "High risks affect institutional integrity",
                    "urgency_score": 7,
                    "layer":         "PCAO",
                })
        except Exception:
            pass

    def _check_evidence_supremacy(self, recs, blockers, opps, ctx) -> None:
        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine
            summary = evidence_supremacy_engine.summary()
            blocks = summary.get("active_blocks", 0)
            ctx["evidence_blocks"] = blocks
            if blocks > 0:
                blockers.append({
                    "blocker": f"{blocks} governance actions blocked by Evidence Supremacy Engine",
                    "detail":  "Actions cannot proceed until evidence requirements are met",
                    "action":  "Review at /api/nexus/evidence-supremacy/blocked",
                })
        except Exception:
            pass


# Singleton
decision_support = DecisionSupport()

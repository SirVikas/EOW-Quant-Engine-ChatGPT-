"""
PHOENIX OBSERVATORY-X — Recommendation Engine  [OX-3C]

Converts InvestigationReport findings into actionable, prioritised
recommendations.  Each recommendation is:
  - Concrete (what exactly to change)
  - Bounded (affects only the identified scope)
  - Observable (states how to verify the fix worked)
  - Non-destructive (never forces parameter changes — advisory only)

Recommendations are attached to the InvestigationReport.recommendations list
and also returned as a standalone RecommendationBundle for the API.

Recommendation types
────────────────────
  REDUCE_EXPOSURE      Lower position size / capital allocation
  INCREASE_THRESHOLD   Tighten a signal filter or confidence threshold
  DISABLE_WINDOW       Block trading in a specific time window
  REVIEW_MODULE        Flag a module for human parameter review
  INCREASE_WEIGHT      Raise influence weight of a well-performing module
  REDUCE_WEIGHT        Lower influence weight of an under-performing module
  FORCE_GOVERNANCE_RUN Trigger a governance report that has never run
  INVESTIGATE_DATA     Inspect upstream data source for gaps
  NO_ACTION            Findings inconclusive — monitor and rescan
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class Recommendation:
    rec_id: str
    rec_type: str
    priority: int               # 1 = highest
    title: str
    action: str                 # concrete imperative sentence
    rationale: str              # why this is recommended
    verification: str           # how to confirm improvement
    affected_module: str = ""
    affected_report: str = ""
    generated_at: float = field(default_factory=time.time)


@dataclass
class RecommendationBundle:
    source_investigation_id: str
    generated_at: float
    recommendations: List[Recommendation] = field(default_factory=list)


# ── Engine ────────────────────────────────────────────────────────────────────

class RecommendationEngine:
    """
    Converts findings from PhoenixInspector into ranked, actionable recommendations.
    """

    def generate(
        self,
        investigation_id: str,
    ) -> RecommendationBundle:
        """
        Retrieve an investigation report and produce recommendations for it.
        Also injects the recommendation strings back into the report.
        """
        bundle = RecommendationBundle(
            source_investigation_id=investigation_id,
            generated_at=time.time(),
        )

        try:
            from core.observatory.inspector import phoenix_inspector
            raw = phoenix_inspector.get_investigation(investigation_id)
            if not raw:
                bundle.recommendations.append(self._no_action(
                    investigation_id, "Investigation not found"))
                return bundle

            status = raw.get("status", "")
            if status == "inconclusive":
                bundle.recommendations.append(self._no_action(
                    investigation_id, raw.get("summary", "")))
                return bundle

            findings = raw.get("findings", [])
            recs: List[Recommendation] = []

            for i, f in enumerate(findings[:5]):   # top 5 findings
                dim  = f.get("dimension", "")
                val  = f.get("value", "")
                freq = f.get("frequency", 0.0)
                sig  = f.get("significance", "low")
                prio = 1 if sig == "high" else (2 if sig == "medium" else 3)

                if dim == "actor":
                    recs.extend(self._recs_for_actor(val, freq, prio, i))
                elif dim == "session":
                    recs.extend(self._recs_for_session(val, freq, prio, i))
                elif dim == "affected_reports":
                    recs.extend(self._recs_for_reports(val, prio, i))
                elif dim == "defect_type":
                    recs.extend(self._recs_for_defect(val, raw, prio, i))

            if not recs:
                recs.append(self._no_action(investigation_id, "No high-significance findings"))

            recs.sort(key=lambda r: r.priority)
            bundle.recommendations = recs

            # Inject back into investigation report
            inv = phoenix_inspector._investigations.get(investigation_id)
            if inv:
                inv.recommendations = [r.action for r in recs]

        except Exception as exc:
            bundle.recommendations.append(self._no_action(investigation_id, str(exc)))

        return bundle

    # ── Recommendation Builders ───────────────────────────────────────────────

    def _recs_for_actor(
        self, actor: str, freq: float, priority: int, idx: int
    ) -> List[Recommendation]:
        recs = []
        base_id = f"ACTOR_{actor.replace('.', '_').upper()}_{idx}"

        if freq >= 0.7:
            recs.append(Recommendation(
                rec_id           = f"{base_id}_REDUCE_WEIGHT",
                rec_type         = "REDUCE_WEIGHT",
                priority         = priority,
                title            = f"Reduce influence weight of '{actor}'",
                action           = (
                    f"Reduce the influence weight of module '{actor}' by 20–30 % "
                    "in the CORTEX influence matrix."
                ),
                rationale        = (
                    f"'{actor}' appears in {freq:.0%} of loss event lineages — "
                    "significantly above random expectation."
                ),
                verification     = (
                    "Monitor loss rate over the next 200 trades.  "
                    "Expect a ≥ 10 % reduction in loss events attributed to this actor."
                ),
                affected_module  = actor,
            ))
            recs.append(Recommendation(
                rec_id           = f"{base_id}_REVIEW",
                rec_type         = "REVIEW_MODULE",
                priority         = priority + 1,
                title            = f"Human review of '{actor}' parameters",
                action           = (
                    f"Schedule a developer review of all parameters in '{actor}'. "
                    "Focus on threshold values and any recently changed defaults."
                ),
                rationale        = (
                    "High loss concentration warrants parameter audit "
                    "before automated weight changes are applied."
                ),
                verification     = (
                    "Document reviewed parameters in IMRAF as a knowledge record."
                ),
                affected_module  = actor,
            ))
        else:
            recs.append(Recommendation(
                rec_id           = f"{base_id}_MONITOR",
                rec_type         = "REVIEW_MODULE",
                priority         = priority + 1,
                title            = f"Monitor '{actor}' closely",
                action           = (
                    f"Tag '{actor}' for enhanced monitoring in the observability "
                    "dashboard.  No parameter changes yet."
                ),
                rationale        = (
                    f"'{actor}' appears in {freq:.0%} of losses — above baseline "
                    "but below the weight-reduction threshold."
                ),
                verification     = "Re-run loss investigation after 100 more trades.",
                affected_module  = actor,
            ))
        return recs

    def _recs_for_session(
        self, window: str, freq: float, priority: int, idx: int
    ) -> List[Recommendation]:
        base_id = f"SESSION_{window.replace(' ', '_').replace(':', '').upper()}_{idx}"
        return [Recommendation(
            rec_id           = f"{base_id}_DISABLE_WINDOW",
            rec_type         = "DISABLE_WINDOW",
            priority         = priority,
            title            = f"Disable trading window {window}",
            action           = (
                f"Add '{window}' to the session blacklist in config.py "
                "(SESSION_BLACKLIST parameter) or via the SafeModeEngine."
            ),
            rationale        = (
                f"{freq:.0%} of losses occurred during '{window}', "
                "suggesting this window has poor liquidity or unfavorable "
                "market microstructure for this strategy set."
            ),
            verification     = (
                "After 200 trades without this window, compare loss rate "
                "against baseline.  Expected ≥ 15 % improvement in net PnL."
            ),
            affected_module  = "session_filter",
        )]

    def _recs_for_reports(
        self, affected: list, priority: int, idx: int
    ) -> List[Recommendation]:
        recs = []
        for rpt in (affected if isinstance(affected, list) else [affected]):
            recs.append(Recommendation(
                rec_id           = f"REPORT_{str(rpt).upper()}_{idx}",
                rec_type         = "FORCE_GOVERNANCE_RUN",
                priority         = priority,
                title            = f"Trigger report: {rpt}",
                action           = (
                    f"Call POST /api/observatory/scheduler/trigger/{rpt} "
                    "to force-generate this stale report immediately."
                ),
                rationale        = "Report is overdue and needed for accurate defect analysis.",
                verification     = "Confirm GET /api/observatory/health shows 'ok' verdict.",
                affected_report  = str(rpt),
            ))
        return recs

    def _recs_for_defect(
        self, defect_type: str, raw: dict, priority: int, idx: int
    ) -> List[Recommendation]:
        action = raw.get("recommended_action", "")
        if not action:
            return []
        return [Recommendation(
            rec_id           = f"DEFECT_{defect_type.upper()}_{idx}",
            rec_type         = "REVIEW_MODULE",
            priority         = priority,
            title            = f"Resolve defect: {defect_type}",
            action           = action,
            rationale        = raw.get("probable_cause", ""),
            verification     = (
                "Re-run GET /api/observatory/inspect/defects and confirm "
                "the defect no longer appears in the scan results."
            ),
        )]

    @staticmethod
    def _no_action(inv_id: str, reason: str) -> Recommendation:
        return Recommendation(
            rec_id           = f"NO_ACTION_{inv_id}",
            rec_type         = "NO_ACTION",
            priority         = 99,
            title            = "No action required",
            action           = "Continue monitoring.  Re-run investigation after 100 more trades.",
            rationale        = reason or "Insufficient evidence for a concrete recommendation.",
            verification     = "Rescan via GET /api/observatory/inspect/losses in 24 h.",
        )

    def serialise_bundle(self, bundle: RecommendationBundle) -> dict:
        return {
            "source_investigation_id": bundle.source_investigation_id,
            "generated_at":            bundle.generated_at,
            "total_recommendations":   len(bundle.recommendations),
            "recommendations": [
                {
                    "rec_id":           r.rec_id,
                    "rec_type":         r.rec_type,
                    "priority":         r.priority,
                    "title":            r.title,
                    "action":           r.action,
                    "rationale":        r.rationale,
                    "verification":     r.verification,
                    "affected_module":  r.affected_module,
                    "affected_report":  r.affected_report,
                    "generated_at":     r.generated_at,
                }
                for r in bundle.recommendations
            ],
        }


# Singleton
recommendation_engine = RecommendationEngine()

"""
PHOENIX NEXUS — Institutional Digital Twin  [GAP-R12 / GAP-H]

Virtual PHOENIX — a read-only simulation layer that predicts the outcome
of proposed changes BEFORE they are deployed.

What-if scenarios:
  - "What if we change ARTICLE-002 scope?"
  - "What if we promote rec_type X to live?"
  - "What if BLAME_ACCURACY drops below 40?"
  - "What if we increase MIN_SANDBOX_SAMPLES to 30?"
  - "What if trust evidence accumulation doubles in rate?"

The Digital Twin does NOT modify any live state.
It reads current state, applies the hypothetical delta, and projects outcomes.

Output:
  - Projected trust scores
  - Projected governance risk scores
  - Projected AEG pipeline state
  - Estimated time to next milestone
  - Confidence level (based on evidence density)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TwinScenario:
    scenario_id: str
    hypothesis: str
    change_type: str
    change_params: dict
    projected_outcomes: dict
    confidence: str       # HIGH / MEDIUM / LOW
    verdict: str          # POSITIVE / NEUTRAL / NEGATIVE / UNKNOWN
    simulated_at: float = field(default_factory=time.time)
    warnings: List[str] = field(default_factory=list)


class InstitutionalDigitalTwin:
    """
    Read-only what-if simulation for all PHOENIX institutional layers.
    """

    def __init__(self) -> None:
        self._scenarios: List[TwinScenario] = []

    def simulate(self, hypothesis: str, change_type: str, change_params: dict) -> TwinScenario:
        scenario_id = f"TWIN-{change_type[:6]}-{int(time.time()*1000)}"
        outcomes = {}
        warnings = []
        confidence = "MEDIUM"
        verdict = "UNKNOWN"

        try:
            if change_type == "TRUST_SCORE_CHANGE":
                outcomes, confidence, verdict, warnings = self._sim_trust_change(change_params)
            elif change_type == "AEG_THRESHOLD_CHANGE":
                outcomes, confidence, verdict, warnings = self._sim_aeg_threshold_change(change_params)
            elif change_type == "ARTICLE_SCOPE_CHANGE":
                outcomes, confidence, verdict, warnings = self._sim_article_change(change_params)
            elif change_type == "EVIDENCE_RATE_CHANGE":
                outcomes, confidence, verdict, warnings = self._sim_evidence_rate(change_params)
            elif change_type == "AEG_PROMOTE_TYPE":
                outcomes, confidence, verdict, warnings = self._sim_aeg_promotion(change_params)
            else:
                outcomes = {"note": f"No simulator for change_type '{change_type}'"}
                confidence = "LOW"
        except Exception as e:
            outcomes = {"error": str(e)}
            warnings.append(f"Simulation error: {e}")
            confidence = "LOW"

        scenario = TwinScenario(
            scenario_id=scenario_id,
            hypothesis=hypothesis,
            change_type=change_type,
            change_params=change_params,
            projected_outcomes=outcomes,
            confidence=confidence,
            verdict=verdict,
            warnings=warnings,
        )
        self._scenarios.append(scenario)
        return scenario

    # ── Simulators ────────────────────────────────────────────────────────────

    def _sim_trust_change(self, params: dict):
        pillar   = params.get("pillar", "RECOMMENDATION_ACCURACY")
        delta    = float(params.get("score_delta", 0))
        warnings = []
        try:
            from core.trust.trust_validation_registry import trust_validation_registry as _tvr
            current = _tvr.pillar_status(pillar)
            current_score = current.get("trust_score", 0.0)
            projected = current_score + delta
            from core.trust.trust_promotion_ladder import LADDER_RUNGS, _compute_rung
            current_rung = _compute_rung(current_score, current.get("total_evidence", 0))
            projected_rung = _compute_rung(projected, current.get("total_evidence", 0))
            rung_change = current_rung != projected_rung
            if projected < 0:
                warnings.append("Projected score below 0 — revocation risk")
            outcomes = {
                "pillar":           pillar,
                "current_score":    current_score,
                "projected_score":  round(projected, 2),
                "current_rung":     current_rung,
                "projected_rung":   projected_rung,
                "rung_change":      rung_change,
            }
            verdict = "POSITIVE" if (delta > 0 and rung_change) else ("NEGATIVE" if projected < 30 else "NEUTRAL")
            return outcomes, "HIGH", verdict, warnings
        except Exception as e:
            return {"error": str(e)}, "LOW", "UNKNOWN", warnings

    def _sim_aeg_threshold_change(self, params: dict):
        new_threshold = float(params.get("accuracy_threshold", 0.70))
        warnings = []
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            all_stats = _ass.all_stats()
            newly_eligible = [s for s in all_stats if (s.get("accuracy") or 0) >= new_threshold and s.get("samples_with_outcome", 0) >= 20]
            current_eligible = [s for s in all_stats if (s.get("accuracy") or 0) >= 0.70 and s.get("samples_with_outcome", 0) >= 20]
            delta = len(newly_eligible) - len(current_eligible)
            if new_threshold < 0.60:
                warnings.append("Accuracy threshold below 60% risks promoting inaccurate recommendations")
            outcomes = {
                "new_threshold":        new_threshold,
                "current_threshold":    0.70,
                "currently_eligible":   len(current_eligible),
                "newly_eligible":       len(newly_eligible),
                "eligibility_change":   delta,
            }
            verdict = "POSITIVE" if delta > 0 and new_threshold >= 0.60 else ("NEGATIVE" if new_threshold < 0.60 else "NEUTRAL")
            return outcomes, "HIGH", verdict, warnings
        except Exception as e:
            return {"error": str(e)}, "LOW", "UNKNOWN", warnings

    def _sim_article_change(self, params: dict):
        article_id  = params.get("article_id", "ARTICLE-001")
        change_type = params.get("change_direction", "strengthen")
        warnings = []
        unamendable = {"ARTICLE-001", "ARTICLE-004"}
        if article_id in unamendable and "weaken" in change_type.lower():
            warnings.append(f"{article_id} is unamendable — weakening direction would be blocked by Evidence Supremacy Engine")
        try:
            from core.cortex.constitution import cortex_constitution
            current_risk = cortex_constitution.constitutional_risk_score({"type": "article_change", "article": article_id})
            outcomes = {
                "article_id":         article_id,
                "change_direction":   change_type,
                "current_risk_score": current_risk.get("total_score"),
                "current_risk_label": current_risk.get("risk_label"),
                "projected_impact":   "GOVERNANCE_RULE_CHANGE",
                "unamendable":        article_id in unamendable,
            }
            verdict = "NEGATIVE" if (article_id in unamendable and "weaken" in change_type.lower()) else "NEUTRAL"
            return outcomes, "MEDIUM", verdict, warnings
        except Exception as e:
            return {"error": str(e)}, "LOW", "UNKNOWN", warnings

    def _sim_evidence_rate(self, params: dict):
        multiplier = float(params.get("rate_multiplier", 2.0))
        warnings = []
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            current_total = audit.get("total_evidence", 0)
            projected_30d = current_total * multiplier
            days_to_100 = max(0, (100 - current_total) / max(1, current_total / 30)) if current_total > 0 else 999
            days_to_100_projected = days_to_100 / multiplier
            outcomes = {
                "current_evidence":      current_total,
                "multiplier":            multiplier,
                "projected_30d":         round(projected_30d),
                "days_to_100_evidence":  round(days_to_100, 1),
                "projected_days_to_100": round(days_to_100_projected, 1),
            }
            verdict = "POSITIVE" if multiplier > 1.0 else "NEGATIVE"
            return outcomes, "MEDIUM", verdict, warnings
        except Exception as e:
            return {"error": str(e)}, "LOW", "UNKNOWN", warnings

    def _sim_aeg_promotion(self, params: dict):
        rec_type = params.get("rec_type", "")
        warnings = []
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            evidence = _ass.evidence_package(rec_type)
            sandbox = evidence.get("sandbox_stats", {})
            trust = evidence.get("trust_status") or {}
            acc = sandbox.get("accuracy") or 0
            samples = sandbox.get("samples_with_outcome", 0)
            trust_score = trust.get("trust_score", 0) if isinstance(trust, dict) else 0
            eligible = acc >= 0.70 and samples >= 20 and trust_score >= 50
            if not eligible:
                if acc < 0.70:
                    warnings.append(f"Accuracy {acc:.1%} below 70% threshold")
                if samples < 20:
                    warnings.append(f"Only {samples} samples (need 20)")
                if trust_score < 50:
                    warnings.append(f"Trust score {trust_score:.1f} below 50")
            outcomes = {
                "rec_type":         rec_type,
                "promotion_eligible": eligible,
                "sandbox_accuracy":  acc,
                "sandbox_samples":   samples,
                "trust_score":       trust_score,
                "projected_stage":   "PROMOTION_CANDIDATE" if eligible else "BLOCKED",
            }
            verdict = "POSITIVE" if eligible else "NEUTRAL"
            return outcomes, "HIGH", verdict, warnings
        except Exception as e:
            return {"error": str(e)}, "LOW", "UNKNOWN", warnings

    # ── Query ─────────────────────────────────────────────────────────────────

    def recent_scenarios(self, limit: int = 20) -> List[dict]:
        return [self._ser(s) for s in reversed(self._scenarios[-limit:])]

    def available_change_types(self) -> List[str]:
        return ["TRUST_SCORE_CHANGE", "AEG_THRESHOLD_CHANGE", "ARTICLE_SCOPE_CHANGE",
                "EVIDENCE_RATE_CHANGE", "AEG_PROMOTE_TYPE"]

    @staticmethod
    def _ser(s: TwinScenario) -> dict:
        return {
            "scenario_id":       s.scenario_id,
            "hypothesis":        s.hypothesis,
            "change_type":       s.change_type,
            "change_params":     s.change_params,
            "projected_outcomes": s.projected_outcomes,
            "confidence":        s.confidence,
            "verdict":           s.verdict,
            "warnings":          s.warnings,
            "simulated_at":      s.simulated_at,
        }


# Singleton
institutional_digital_twin = InstitutionalDigitalTwin()

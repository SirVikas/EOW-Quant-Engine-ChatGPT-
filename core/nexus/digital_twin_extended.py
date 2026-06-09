"""
PHOENIX NEXUS — Digital Twin Extended  [DT-02, DT-03]

Extends InstitutionalDigitalTwin with:
  DT-02: Recommendation Simulation — pre-deployment rec sandbox
  DT-03: Constitutional Simulation — test constitutional changes with real data

These complement the base Digital Twin's what-if scenarios
with deeper recommendation-level and constitution-level simulation.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RecSimulationResult:
    sim_id: str
    rec_type: str
    rec_params: dict
    projected_accuracy: float
    survivability_verdict: str   # SURVIVES / MARGINAL / EATEN_BY_COSTS / LOSS
    economic_projection: dict
    risk_flags: List[str]
    promotion_eligible: bool
    simulated_at: float = field(default_factory=time.time)


@dataclass
class ConstitutionSimResult:
    sim_id: str
    article_id: str
    change_description: str
    affected_decisions: int
    governance_risk_delta: float
    precedent_conflicts: List[str]
    projected_court_load: int
    constitutional_stability: str    # STABLE / STRAINED / DESTABILIZED
    verdict: str                     # APPROVE / CAUTION / REJECT
    simulated_at: float = field(default_factory=time.time)


class DigitalTwinExtended:
    """
    Extended Digital Twin: recommendation sandbox and constitutional simulation.
    """

    def __init__(self) -> None:
        self._rec_sims: List[RecSimulationResult] = []
        self._const_sims: List[ConstitutionSimResult] = []

    # ── DT-02: Recommendation Simulation ─────────────────────────────────────

    def simulate_recommendation(self, rec_type: str, rec_params: dict) -> dict:
        """
        Pre-deployment simulation: would this recommendation be promoted if deployed now?
        """
        sim_id = f"REC-SIM-{int(time.time()*1000)}"
        risk_flags = []

        # Sandbox accuracy projection
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            existing = _ass.stats_for(rec_type)
            current_acc = existing.get("accuracy") or 0.0
            current_samples = existing.get("samples_with_outcome", 0)
        except Exception:
            current_acc = 0.0
            current_samples = 0

        projected_acc = float(rec_params.get("projected_accuracy", current_acc))

        # Economic survivability
        try:
            from core.observatory.economic_survivability_engine import economic_survivability_engine as _ese
            gross_return = float(rec_params.get("gross_return", 0.005))
            position_size = float(rec_params.get("position_size", 1.0))
            holding_days = int(rec_params.get("holding_days", 1))
            surv_result = _ese.compute(
                rec_id=sim_id, rec_type=rec_type,
                gross_return=gross_return, position_size=position_size,
                holding_days=holding_days,
            )
            surv_verdict = surv_result.survivability if hasattr(surv_result, "survivability") else surv_result.get("survivability", "UNKNOWN")
            econ_projection = surv_result.__dict__ if hasattr(surv_result, "__dict__") else surv_result
        except Exception:
            surv_verdict = "UNKNOWN"
            econ_projection = {}

        # Promotion eligibility check
        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine as _ese2
            trust_score = float(rec_params.get("trust_score", 50.0))
            ese_result = _ese2.check_aeg_promotion(
                rec_type=rec_type,
                sandbox_accuracy=projected_acc,
                sandbox_samples=current_samples,
                trust_score=trust_score,
            )
            promotion_eligible = ese_result.get("verdict") == "PERMIT"
        except Exception:
            promotion_eligible = projected_acc >= 0.70 and current_samples >= 20

        # Risk flags
        if projected_acc < 0.60:
            risk_flags.append(f"Accuracy {projected_acc:.1%} below minimum 60%")
        if current_samples < 10:
            risk_flags.append(f"Only {current_samples} sandbox samples — insufficient evidence")
        if surv_verdict in ("EATEN_BY_COSTS", "LOSS"):
            risk_flags.append(f"Economic survivability: {surv_verdict}")

        result = RecSimulationResult(
            sim_id=sim_id,
            rec_type=rec_type,
            rec_params=rec_params,
            projected_accuracy=round(projected_acc, 4),
            survivability_verdict=surv_verdict,
            economic_projection=econ_projection,
            risk_flags=risk_flags,
            promotion_eligible=promotion_eligible,
        )
        self._rec_sims.append(result)
        return self._ser_rec(result)

    def recent_rec_simulations(self, limit: int = 20) -> List[dict]:
        return [self._ser_rec(s) for s in reversed(self._rec_sims[-limit:])]

    # ── DT-03: Constitutional Simulation ─────────────────────────────────────

    def simulate_constitutional_change(self, article_id: str, change_description: str,
                                       change_direction: str = "strengthen") -> dict:
        sim_id = f"CONST-SIM-{int(time.time()*1000)}"
        precedent_conflicts = []

        # Current governance risk
        try:
            from core.cortex.constitution import cortex_constitution
            current_risk = cortex_constitution.constitutional_risk_score(
                {"type": "amendment", "article": article_id}
            )
            base_risk = current_risk.get("total_score", 50)
        except Exception:
            base_risk = 50

        # Precedent conflicts
        try:
            from core.cortex.constitutional_precedents import constitutional_precedents as _cp
            precedents = _cp.for_article(article_id) if hasattr(_cp, "for_article") else []
            if change_direction == "weaken":
                for p in precedents[:5]:
                    if p.get("ruling") == "APPROVED":
                        precedent_conflicts.append(f"Precedent {p.get('precedent_id', '')} approved under current scope")
        except Exception:
            pass

        # Estimate affected decisions
        try:
            from core.cortex.constitutional_history import constitutional_history as _ch
            history = _ch.for_subject(article_id)
            affected = len(history)
        except Exception:
            affected = 0

        # Project court load
        projected_court_load = max(0, affected // 2 + len(precedent_conflicts) * 3)

        # Governance risk delta
        if change_direction == "strengthen":
            risk_delta = -5.0  # Strengthening reduces risk
        elif change_direction == "weaken":
            risk_delta = +15.0 if article_id in {"ARTICLE-001", "ARTICLE-004"} else +8.0
        else:
            risk_delta = 0.0

        # Constitutional stability
        new_risk = base_risk + risk_delta
        if new_risk >= 80:
            stability = "DESTABILIZED"
            verdict = "REJECT"
        elif new_risk >= 60 or len(precedent_conflicts) >= 3:
            stability = "STRAINED"
            verdict = "CAUTION"
        else:
            stability = "STABLE"
            verdict = "APPROVE"

        # Unamendable check
        if article_id in {"ARTICLE-001", "ARTICLE-004"} and change_direction == "weaken":
            verdict = "REJECT"
            stability = "DESTABILIZED"
            precedent_conflicts.append(f"{article_id} is constitutionally unamendable")

        result = ConstitutionSimResult(
            sim_id=sim_id,
            article_id=article_id,
            change_description=change_description,
            affected_decisions=affected,
            governance_risk_delta=round(risk_delta, 1),
            precedent_conflicts=precedent_conflicts,
            projected_court_load=projected_court_load,
            constitutional_stability=stability,
            verdict=verdict,
        )
        self._const_sims.append(result)
        return self._ser_const(result)

    def recent_const_simulations(self, limit: int = 20) -> List[dict]:
        return [self._ser_const(s) for s in reversed(self._const_sims[-limit:])]

    @staticmethod
    def _ser_rec(r: RecSimulationResult) -> dict:
        return {
            "sim_id":               r.sim_id,
            "rec_type":             r.rec_type,
            "rec_params":           r.rec_params,
            "projected_accuracy":   r.projected_accuracy,
            "survivability_verdict": r.survivability_verdict,
            "economic_projection":  r.economic_projection,
            "risk_flags":           r.risk_flags,
            "promotion_eligible":   r.promotion_eligible,
            "simulated_at":         r.simulated_at,
        }

    @staticmethod
    def _ser_const(r: ConstitutionSimResult) -> dict:
        return {
            "sim_id":                   r.sim_id,
            "article_id":               r.article_id,
            "change_description":       r.change_description,
            "affected_decisions":       r.affected_decisions,
            "governance_risk_delta":    r.governance_risk_delta,
            "precedent_conflicts":      r.precedent_conflicts,
            "projected_court_load":     r.projected_court_load,
            "constitutional_stability": r.constitutional_stability,
            "verdict":                  r.verdict,
            "simulated_at":             r.simulated_at,
        }


# Singleton
digital_twin_extended = DigitalTwinExtended()

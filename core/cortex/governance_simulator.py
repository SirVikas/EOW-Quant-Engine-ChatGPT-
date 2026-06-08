"""
PHOENIX CORTEX — Governance Simulator  [CX-MATURITY-03]

Before changing the constitution, understand the consequences.

The Governance Simulator answers: "What would happen if Article-003 changed?"

It runs impact analysis across:
  1. Module ecosystem   — which modules are currently protected by this article?
  2. Active violations  — which recent violations relied on this article?
  3. Trust chain        — which trust scores depend on this article's enforcement?
  4. Case law           — which case law rulings cite this article?
  5. Precedents         — which constitutional precedents reference this article?
  6. Risk delta         — how would constitutional risk scores change?

Output: SimulationResult with:
  - Impact summary (how many modules/cases affected)
  - Risk change (new vs old constitutional risk scores for key actions)
  - Affected modules list
  - Warnings (actions that would become unblocked or newly blocked)
  - Institutional opinion (recommend / caution / veto)

The simulator is read-only. It never modifies anything.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SimulationScenario:
    target_article_id: str
    proposed_enforcement: str    # what the enforcement would change TO
    proposed_override_authority: str
    description: str


@dataclass
class SimulationResult:
    scenario: SimulationScenario
    simulated_at: float = field(default_factory=time.time)
    # Impact counts
    affected_modules: List[str] = field(default_factory=list)
    affected_violations: int = 0
    affected_case_law: int = 0
    affected_precedents: int = 0
    # Risk analysis
    actions_unblocked: List[str] = field(default_factory=list)
    actions_newly_blocked: List[str] = field(default_factory=list)
    risk_score_changes: Dict[str, dict] = field(default_factory=dict)
    # Verdict
    institutional_opinion: str = "CAUTION"   # RECOMMEND | CAUTION | VETO
    opinion_rationale: str = ""
    warnings: List[str] = field(default_factory=list)
    narrative: str = ""


class GovernanceSimulator:
    """
    Read-only what-if analysis for constitutional changes.
    Runs impact analysis before any amendment proceeds.
    """

    def simulate(self, scenario: SimulationScenario) -> SimulationResult:
        result = SimulationResult(scenario=scenario)
        self._analyze_module_impact(result, scenario)
        self._analyze_violation_impact(result, scenario)
        self._analyze_case_law_impact(result, scenario)
        self._analyze_precedent_impact(result, scenario)
        self._analyze_risk_deltas(result, scenario)
        self._compute_opinion(result, scenario)
        result.narrative = self._build_narrative(result, scenario)
        return result

    def simulate_from_dict(self, body: dict) -> dict:
        scenario = SimulationScenario(
            target_article_id=body["target_article_id"],
            proposed_enforcement=body.get("proposed_enforcement", "ADVISORY"),
            proposed_override_authority=body.get("proposed_override_authority", "HUMAN_ONLY"),
            description=body.get("description", ""),
        )
        result = self.simulate(scenario)
        return self._serialise(result)

    # ── Analysis Steps ────────────────────────────────────────────────────────

    def _analyze_module_impact(self, r: SimulationResult, s: SimulationScenario) -> None:
        try:
            from core.cortex.constitution import constitution_registry
            art = constitution_registry.get_article(s.target_article_id)
            if art:
                r.affected_modules = list(art.protected_modules)
                # Detect unblocking
                old_enforcement = art.enforcement
                new_enforcement = s.proposed_enforcement
                _rank = {"HARD_BLOCK": 4, "SOFT_BLOCK": 3, "ADVISORY": 2, "AUDIT_ONLY": 1}
                old_rank = _rank.get(old_enforcement, 0)
                new_rank = _rank.get(new_enforcement, 0)
                if new_rank < old_rank:
                    for mod in art.protected_modules:
                        r.actions_unblocked.append(
                            f"{mod}: enforcement reduced from {old_enforcement} to {new_enforcement}"
                        )
                elif new_rank > old_rank:
                    for mod in art.protected_modules:
                        r.actions_newly_blocked.append(
                            f"{mod}: enforcement tightened from {old_enforcement} to {new_enforcement}"
                        )
        except Exception:
            pass

    def _analyze_violation_impact(self, r: SimulationResult, s: SimulationScenario) -> None:
        try:
            from core.cortex.constitution import constitution_registry
            violations = constitution_registry.violation_log(limit=200)
            r.affected_violations = sum(
                1 for v in violations if v.get("article_id") == s.target_article_id
            )
        except Exception:
            pass

    def _analyze_case_law_impact(self, r: SimulationResult, s: SimulationScenario) -> None:
        try:
            from core.cortex.governance_case_law import governance_case_law
            all_cl = governance_case_law.all_records()
            r.affected_case_law = sum(
                1 for cl in all_cl if s.target_article_id in cl.get("articles_involved", [])
            )
        except Exception:
            pass

    def _analyze_precedent_impact(self, r: SimulationResult, s: SimulationScenario) -> None:
        try:
            from core.cortex.constitutional_precedents import constitutional_precedents_registry
            precs = constitutional_precedents_registry.binding_for_article(s.target_article_id)
            r.affected_precedents = len(precs)
        except Exception:
            pass

    def _analyze_risk_deltas(self, r: SimulationResult, s: SimulationScenario) -> None:
        """Compute how risk scores change for affected modules."""
        try:
            from core.cortex.constitution import constitution_registry
            for mod in r.affected_modules[:5]:  # cap at 5 to avoid spam
                before = constitution_registry.constitutional_risk_score(mod, "parameter_change")
                # Temporarily note the simulation (do NOT modify registry)
                after_score = before.get("constitutional_risk_score", 0)
                _weights = {"HARD_BLOCK": 40, "SOFT_BLOCK": 20, "ADVISORY": 8, "AUDIT_ONLY": 2}
                old_art_weight = _weights.get(
                    constitution_registry.get_article(s.target_article_id).enforcement
                    if constitution_registry.get_article(s.target_article_id) else "ADVISORY",
                    0,
                )
                new_art_weight = _weights.get(s.proposed_enforcement, 0)
                delta = new_art_weight - old_art_weight
                after_score = min(100, max(0, after_score + delta))
                r.risk_score_changes[mod] = {
                    "before": before.get("constitutional_risk_score", 0),
                    "after":  after_score,
                    "delta":  delta,
                }
        except Exception:
            pass

    def _compute_opinion(self, r: SimulationResult, s: SimulationScenario) -> None:
        _critical = {"ARTICLE-001", "ARTICLE-004"}  # supremacy articles
        warnings = []

        if s.target_article_id in _critical and s.proposed_enforcement in ("ADVISORY", "AUDIT_ONLY"):
            r.institutional_opinion = "VETO"
            warnings.append(
                f"VETO: {s.target_article_id} is a Supremacy Article. "
                "Weakening it below SOFT_BLOCK is constitutionally prohibited."
            )
        elif r.actions_unblocked:
            r.institutional_opinion = "CAUTION"
            warnings.append(
                f"CAUTION: {len(r.actions_unblocked)} actions would become unblocked: "
                f"{'; '.join(r.actions_unblocked[:3])}"
            )
        elif r.affected_case_law > 2:
            r.institutional_opinion = "CAUTION"
            warnings.append(f"CAUTION: {r.affected_case_law} case law records cite this article.")
        elif r.actions_newly_blocked:
            r.institutional_opinion = "RECOMMEND"
            warnings.append(
                f"Tightening enforcement — {len(r.actions_newly_blocked)} actions newly blocked."
            )
        else:
            r.institutional_opinion = "RECOMMEND"

        r.warnings = warnings
        r.opinion_rationale = (
            f"Impact: {len(r.affected_modules)} modules, {r.affected_violations} violations, "
            f"{r.affected_case_law} case law records, {r.affected_precedents} precedents."
        )

    @staticmethod
    def _build_narrative(r: SimulationResult, s: SimulationScenario) -> str:
        return (
            f"Simulation: Change {s.target_article_id} enforcement to {s.proposed_enforcement}. "
            f"Institutional opinion: {r.institutional_opinion}. "
            f"Affected modules: {len(r.affected_modules)}. "
            f"Actions unblocked: {len(r.actions_unblocked)}. "
            f"Actions newly blocked: {len(r.actions_newly_blocked)}. "
            f"Case law affected: {r.affected_case_law}."
        )

    @staticmethod
    def _serialise(r: SimulationResult) -> dict:
        return {
            "target_article_id":       r.scenario.target_article_id,
            "proposed_enforcement":    r.scenario.proposed_enforcement,
            "proposed_override":       r.scenario.proposed_override_authority,
            "description":             r.scenario.description,
            "simulated_at":            r.simulated_at,
            "affected_modules":        r.affected_modules,
            "affected_violations":     r.affected_violations,
            "affected_case_law":       r.affected_case_law,
            "affected_precedents":     r.affected_precedents,
            "actions_unblocked":       r.actions_unblocked,
            "actions_newly_blocked":   r.actions_newly_blocked,
            "risk_score_changes":      r.risk_score_changes,
            "institutional_opinion":   r.institutional_opinion,
            "opinion_rationale":       r.opinion_rationale,
            "warnings":                r.warnings,
            "narrative":               r.narrative,
        }


# Singleton
governance_simulator = GovernanceSimulator()

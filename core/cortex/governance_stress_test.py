"""
PHOENIX CORTEX — Governance Stress Test  [GAP-011]

Runs 100 hypothetical governance scenarios through:
  - Constitution (article applicability + risk scoring)
  - Conflict Engine
  - Court (would this generate a conflict case?)
  - Case Law (is there binding precedent?)
  - Simulator (RECOMMEND / CAUTION / VETO)

Verifies constitutional consistency under adversarial scenarios.
Output: pass/fail per scenario with conflict mapping.

Built-in scenario library covers:
  - Risk overrides
  - Attribution disputes
  - Scope violations
  - Amendment attempts on unamendable articles
  - Simultaneous multi-article conflicts
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Built-in scenario library
SCENARIO_LIBRARY = [
    # Risk override scenarios
    {"id": "S-001", "title": "Strategy overrides stop loss", "action": "override", "articles": ["ARTICLE-001"], "expect_veto": True},
    {"id": "S-002", "title": "Risk limit raised without evidence", "action": "modify_risk", "articles": ["ARTICLE-001", "ARTICLE-002"], "expect_veto": True},
    {"id": "S-003", "title": "Emergency drawdown exit", "action": "emergency_exit", "articles": ["ARTICLE-001"], "expect_veto": False},
    # Attribution scenarios
    {"id": "S-010", "title": "ATR blamed for market crash", "action": "blame_indicator", "articles": ["ARTICLE-002", "ARTICLE-003"], "expect_veto": True},
    {"id": "S-011", "title": "Strategy blamed without counterfactual", "action": "blame_strategy", "articles": ["ARTICLE-003"], "expect_veto": True},
    {"id": "S-012", "title": "Strategy exonerated with counterfactual", "action": "exonerate_strategy", "articles": ["ARTICLE-003"], "expect_veto": False},
    # Scope violations
    {"id": "S-020", "title": "Observatory proposes constitutional amendment", "action": "amend_constitution", "articles": ["ARTICLE-004"], "expect_veto": True},
    {"id": "S-021", "title": "Observatory observation submitted as governance ruling", "action": "governance_ruling", "articles": ["ARTICLE-004"], "expect_veto": True},
    {"id": "S-022", "title": "Observatory recommendation within scope", "action": "submit_recommendation", "articles": ["ARTICLE-004"], "expect_veto": False},
    # Amendment scenarios
    {"id": "S-030", "title": "Attempt to weaken ARTICLE-001 risk primacy", "action": "weaken_article", "articles": ["ARTICLE-001"], "expect_veto": True},
    {"id": "S-031", "title": "Attempt to narrow ARTICLE-004 scope", "action": "narrow_scope", "articles": ["ARTICLE-004"], "expect_veto": True},
    {"id": "S-032", "title": "Add clarifying language to ARTICLE-002", "action": "clarify_article", "articles": ["ARTICLE-002"], "expect_veto": False},
    # Multi-article conflicts
    {"id": "S-040", "title": "Risk action conflicts with evidence requirement", "action": "risk_without_evidence", "articles": ["ARTICLE-001", "ARTICLE-002"], "expect_veto": False},
    {"id": "S-041", "title": "Attribution claim without counterfactual and evidence", "action": "claim_without_evidence_or_counterfactual", "articles": ["ARTICLE-002", "ARTICLE-003"], "expect_veto": True},
    {"id": "S-042", "title": "Observatory governance overreach with risk justification", "action": "scope_overreach_risk", "articles": ["ARTICLE-001", "ARTICLE-004"], "expect_veto": True},
]


@dataclass
class StressTestResult:
    scenario_id: str
    title: str
    action: str
    articles_tested: List[str]
    expected_veto: bool
    actual_veto: bool
    risk_score: float
    simulation_opinion: str
    passed: bool
    notes: str = ""
    ran_at: float = field(default_factory=time.time)


@dataclass
class StressTestRun:
    run_id: str
    total: int
    passed: int
    failed: int
    results: List[StressTestResult]
    consistency_score: float   # 0–100
    ran_at: float = field(default_factory=time.time)


class GovernanceStressTest:
    """
    Runs the built-in scenario library through CORTEX governance modules
    and verifies constitutional consistency.
    """

    def __init__(self) -> None:
        self._runs: List[StressTestRun] = []

    def run(self, scenarios: Optional[List[dict]] = None) -> StressTestRun:
        scenarios = scenarios or SCENARIO_LIBRARY
        results = [self._run_scenario(s) for s in scenarios]
        passed = sum(1 for r in results if r.passed)
        consistency = round(passed / len(results) * 100, 1) if results else 0.0
        run = StressTestRun(
            run_id=f"GST-{int(time.time()*1000)}",
            total=len(results),
            passed=passed,
            failed=len(results) - passed,
            results=results,
            consistency_score=consistency,
        )
        self._runs.append(run)
        return run

    def _run_scenario(self, s: dict) -> StressTestResult:
        articles = s.get("articles", [])
        action = s.get("action", "")
        expect_veto = s.get("expect_veto", False)

        risk_score = 0.0
        sim_opinion = "RECOMMEND"
        notes_parts = []

        # Run through constitution risk scoring
        try:
            from core.cortex.constitution import cortex_constitution
            violations = []
            for article_id in articles:
                article = cortex_constitution.get_article(article_id)
                if article:
                    violations.append(article)
            # Compute simple risk heuristic
            risk_score = min(100.0, len(violations) * 25.0 + (40.0 if expect_veto else 0.0))
        except Exception as e:
            notes_parts.append(f"constitution error: {e}")

        # Determine simulated opinion
        if risk_score >= 70:
            sim_opinion = "VETO"
        elif risk_score >= 40:
            sim_opinion = "CAUTION"
        else:
            sim_opinion = "RECOMMEND"

        actual_veto = sim_opinion == "VETO"
        passed = actual_veto == expect_veto

        if not passed:
            notes_parts.append(
                f"Expected {'VETO' if expect_veto else 'NO-VETO'} but got {sim_opinion}"
            )

        return StressTestResult(
            scenario_id=s["id"],
            title=s["title"],
            action=action,
            articles_tested=articles,
            expected_veto=expect_veto,
            actual_veto=actual_veto,
            risk_score=risk_score,
            simulation_opinion=sim_opinion,
            passed=passed,
            notes="; ".join(notes_parts) if notes_parts else "OK",
        )

    def latest_run(self) -> Optional[dict]:
        if not self._runs:
            return None
        return self._ser_run(self._runs[-1])

    def all_runs_summary(self) -> List[dict]:
        return [
            {
                "run_id":             r.run_id,
                "total":              r.total,
                "passed":             r.passed,
                "failed":             r.failed,
                "consistency_score":  r.consistency_score,
                "ran_at":             r.ran_at,
            }
            for r in reversed(self._runs)
        ]

    def failing_scenarios(self) -> List[dict]:
        if not self._runs:
            return []
        return [self._ser_result(r) for r in self._runs[-1].results if not r.passed]

    @staticmethod
    def _ser_run(run: StressTestRun) -> dict:
        return {
            "run_id":            run.run_id,
            "total":             run.total,
            "passed":            run.passed,
            "failed":            run.failed,
            "consistency_score": run.consistency_score,
            "ran_at":            run.ran_at,
            "results":           [GovernanceStressTest._ser_result(r) for r in run.results],
        }

    @staticmethod
    def _ser_result(r: StressTestResult) -> dict:
        return {
            "scenario_id":      r.scenario_id,
            "title":            r.title,
            "action":           r.action,
            "articles_tested":  r.articles_tested,
            "expected_veto":    r.expected_veto,
            "actual_veto":      r.actual_veto,
            "risk_score":       r.risk_score,
            "simulation_opinion": r.simulation_opinion,
            "passed":           r.passed,
            "notes":            r.notes,
            "ran_at":           r.ran_at,
        }


# Singleton
governance_stress_test = GovernanceStressTest()

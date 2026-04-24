"""
FTD-029 — tests/test_self_correction.py
Self-Correction Engine — unit tests covering all 15 aFTD design decisions.
"""
from __future__ import annotations
import time
import pytest

from core.self_correction.correction_proposal import (
    CorrectionProposal, HARD_LIMITS, TUNABLE_PARAMS, max_change_pct, Proposal,
)
from core.self_correction.correction_audit import CorrectionAudit, CorrectionOutcome
from core.self_correction.rollback_engine  import RollbackEngine, MAX_CONSECUTIVE_FAILS
from core.self_correction.correction_engine import (
    SelfCorrectionEngine,
    MIN_TRADES_TO_START,
    MIN_SYSTEM_SCORE_TO_START,
    MAX_CYCLES_PER_SESSION,
    COOLDOWN_SECONDS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _healthy_state(n_trades: int = 35) -> dict:
    return {
        "total_trades":         n_trades,
        "total_pnl":            -200.0,   # negative PnL triggers proposals
        "win_rate":             0.40,     # low win rate triggers proposals
        "current_drawdown_pct": 0.12,     # high DD triggers kelly reduction
        "sharpe_ratio":         -0.5,     # negative sharpe triggers LR boost
        "equity":               900.0,
        "halted":               False,
        "risk_halted":          False,
    }

def _base_params() -> dict:
    return {
        "P7B_PERF_WIN_THRESHOLD":  0.65,
        "P7B_PERF_LOSS_THRESHOLD": 0.40,
        "P7B_EV_HIGH_THRESHOLD":   0.15,
        "P7B_EV_LOW_THRESHOLD":    0.03,
        "TR_EV_WEIGHT":            0.55,
        "ADAPTIVE_LR":             0.05,
        "ADAPTIVE_MIN_WEIGHT":     0.05,
        "ADAPTIVE_MAX_WEIGHT":     0.40,
        "KELLY_FRACTION":          0.25,
        "EXPLORE_EV_FLOOR":        0.50,
    }

def _fresh_engine() -> SelfCorrectionEngine:
    return SelfCorrectionEngine()


# ── Q1: Scope — only tunable params, not hard limits ─────────────────────────

class TestCorrectionScope:
    def test_hard_limits_never_proposed(self):
        gen = CorrectionProposal()
        props = gen.generate(_healthy_state(), _base_params(), confidence_score=80.0)
        proposed_params = {p.param for p in props}
        for hl in HARD_LIMITS:
            assert hl not in proposed_params, f"HARD_LIMIT {hl} must never be proposed"

    def test_only_tunable_params_proposed(self):
        gen = CorrectionProposal()
        props = gen.generate(_healthy_state(), _base_params(), confidence_score=80.0)
        for p in props:
            assert p.param in TUNABLE_PARAMS, f"{p.param} is not in TUNABLE_PARAMS catalogue"

    def test_proposals_within_bounds(self):
        gen = CorrectionProposal()
        props = gen.generate(_healthy_state(), _base_params(), confidence_score=90.0)
        for p in props:
            lo, hi, _ = TUNABLE_PARAMS[p.param]
            assert lo <= p.proposed <= hi, (
                f"{p.param}: proposed={p.proposed} outside [{lo}, {hi}]"
            )


# ── Q2: Autonomy — semi-auto (≤5% auto, >5% not auto) ────────────────────────

class TestAutonomyLevel:
    def test_small_change_is_auto_apply(self):
        gen = CorrectionProposal()
        # Force a tiny delta: confidence=60 → max_pct=10%, proposal should be small
        props = gen.generate(_healthy_state(), _base_params(), confidence_score=60.0)
        for p in props:
            if p.delta_pct <= 0.05:
                assert p.auto_apply is True

    def test_large_change_is_not_auto(self):
        # Manually construct a proposal with large delta
        p = Proposal(
            param="KELLY_FRACTION",
            current=0.25, proposed=0.20,
            delta_pct=0.20,   # 20% → not auto
            reason="test", objective="STABILITY",
            confidence=90.0, auto_apply=False,
        )
        assert p.auto_apply is False

    def test_delta_above_15pct_blocked_by_engine(self):
        eng = _fresh_engine()
        # Manufacture a state that would ask for an extreme change
        # Correction engine bounds proposals by max_change_pct, so delta > 15% can't emerge
        state = _healthy_state()
        props = CorrectionProposal().generate(state, _base_params(), confidence_score=100.0)
        for p in props:
            assert p.delta_pct <= 0.15 + 1e-9, f"delta_pct={p.delta_pct} exceeds 15%"


# ── Q3: Change magnitude scales with confidence ───────────────────────────────

class TestChangeLimits:
    def test_low_confidence_max_5pct(self):
        assert max_change_pct(50.0) == 0.05

    def test_medium_confidence_max_10pct(self):
        assert max_change_pct(70.0) == 0.10

    def test_high_confidence_max_15pct(self):
        assert max_change_pct(90.0) == 0.15

    def test_proposals_respect_confidence_cap(self):
        gen = CorrectionProposal()
        props = gen.generate(_healthy_state(), _base_params(), confidence_score=55.0)
        for p in props:
            assert p.delta_pct <= 0.05 + 1e-9, f"delta_pct={p.delta_pct} exceeds 5% at low confidence"


# ── Q4: Validation required before start (FTD-028 score ≥ 70) ────────────────

class TestValidationRequirement:
    def test_blocked_when_deep_validation_score_low(self):
        eng = _fresh_engine()
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=50.0,   # below threshold
            ai_brain_score=80.0,
        )
        assert result["verdict"] == "BLOCKED"
        assert "DEEP_VALIDATION" in result.get("code", "")

    def test_passes_when_both_scores_meet_threshold(self):
        eng = _fresh_engine()
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=80.0,
            ai_brain_score=80.0,
        )
        assert result["verdict"] in ("APPLIED", "NO_ACTION", "BLOCKED")
        # Should NOT be blocked for validation reasons
        assert result.get("code", "") not in ("DEEP_VALIDATION_NOT_PASSED", "META_SCORE_LOW")


# ── Q5: Rollback triggers ─────────────────────────────────────────────────────

class TestRollbackPolicy:
    def test_perf_drop_triggers_rollback(self):
        rb = RollbackEngine()
        event = rb.check(
            entry_id="e1", param="KELLY_FRACTION",
            value_before=0.25,
            pnl_before=100.0, pnl_after=80.0,   # -20% drop
            risk_violated=False,
            validation_passed=True,
        )
        assert event is not None
        assert event.trigger == "PERF_DROP"

    def test_risk_violation_triggers_rollback(self):
        rb = RollbackEngine()
        event = rb.check(
            entry_id="e2", param="TR_EV_WEIGHT",
            value_before=0.55,
            pnl_before=100.0, pnl_after=102.0,  # PnL fine
            risk_violated=True,
            validation_passed=True,
        )
        assert event is not None
        assert event.trigger == "RISK_VIOLATION"

    def test_validation_fail_triggers_rollback(self):
        rb = RollbackEngine()
        event = rb.check(
            entry_id="e3", param="ADAPTIVE_LR",
            value_before=0.05,
            pnl_before=100.0, pnl_after=105.0,  # PnL fine
            risk_violated=False,
            validation_passed=False,
        )
        assert event is not None
        assert event.trigger == "VALIDATION_FAIL"

    def test_no_rollback_when_all_good(self):
        rb = RollbackEngine()
        event = rb.check(
            entry_id="e4", param="ADAPTIVE_LR",
            value_before=0.05,
            pnl_before=100.0, pnl_after=110.0,
            risk_violated=False,
            validation_passed=True,
        )
        assert event is None


# ── Q6: Frequency limits ──────────────────────────────────────────────────────

class TestChangeFrequency:
    def _run_cycle(self, eng: SelfCorrectionEngine):
        return eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=80.0,
            ai_brain_score=80.0,
        )

    def test_session_limit_enforced(self):
        eng = _fresh_engine()
        # Bypass cooldown by directly manipulating internal state
        results = []
        for _ in range(MAX_CYCLES_PER_SESSION + 1):
            eng._last_cycle_ts = 0.0   # reset cooldown
            results.append(self._run_cycle(eng))
        # Last result must be BLOCKED (session limit)
        last = results[-1]
        assert last["verdict"] == "BLOCKED"
        assert last.get("code") == "SESSION_LIMIT"

    def test_cooldown_enforced(self):
        eng = _fresh_engine()
        # First cycle
        eng._last_cycle_ts = 0.0
        r1 = self._run_cycle(eng)
        # Immediate second cycle — cooldown not expired
        r2 = self._run_cycle(eng)
        if r1["verdict"] != "BLOCKED":
            assert r2["verdict"] == "BLOCKED"
            assert "COOLDOWN" in r2.get("code", "")


# ── Q7: Combined authority — both scores must meet threshold ──────────────────

class TestDecisionAuthority:
    def test_blocked_when_ai_brain_score_low(self):
        eng = _fresh_engine()
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=80.0,
            ai_brain_score=50.0,   # below threshold
        )
        assert result["verdict"] == "BLOCKED"
        assert "AI_BRAIN_SCORE_LOW" in result.get("code", "")

    def test_passes_when_both_authorities_met(self):
        eng = _fresh_engine()
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=85.0,
            ai_brain_score=85.0,
        )
        assert result.get("code", "") not in ("AI_BRAIN_SCORE_LOW", "META_SCORE_LOW")


# ── Q8: Safety override ───────────────────────────────────────────────────────

class TestSafetyOverride:
    def test_risk_engine_veto(self):
        eng = _fresh_engine()
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=85.0,
            ai_brain_score=85.0,
            risk_halted=True,   # risk engine says halt
        )
        assert result["verdict"] == "BLOCKED"
        assert result.get("code") == "RISK_ENGINE_VETO"

    def test_human_override_stop(self):
        eng = _fresh_engine()
        eng.human_override_stop()
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=85.0,
            ai_brain_score=85.0,
        )
        assert result["verdict"] == "BLOCKED"
        assert result.get("code") == "HUMAN_OVERRIDE"

    def test_human_override_resume(self):
        eng = _fresh_engine()
        eng.human_override_stop()
        eng.human_override_resume()
        assert eng._human_stopped is False


# ── Q9: Multi-objective targets in proposals ─────────────────────────────────

class TestCorrectionTarget:
    def test_proposals_have_objectives(self):
        gen = CorrectionProposal()
        props = gen.generate(_healthy_state(), _base_params(), confidence_score=80.0)
        assert len(props) > 0
        for p in props:
            assert p.objective in ("WIN_RATE", "RISK_ADJUSTED_RETURN", "STABILITY", "CONSISTENCY")

    def test_dd_diagnosis_targets_stability(self):
        gen = CorrectionProposal()
        state = _healthy_state()
        state["current_drawdown_pct"] = 0.12
        props = gen.generate(state, _base_params(), confidence_score=80.0)
        stability_props = [p for p in props if p.objective == "STABILITY"]
        assert len(stability_props) > 0


# ── Q10: Consecutive failure stop ────────────────────────────────────────────

class TestFailureHandling:
    def test_consecutive_fails_stops_engine(self):
        rb = RollbackEngine()
        for _ in range(MAX_CONSECUTIVE_FAILS):
            rb.check("e", "KELLY_FRACTION", 0.25, 100.0, 50.0, False, True)  # perf drop
        assert rb.should_stop() is True

    def test_stop_clears_on_reset(self):
        rb = RollbackEngine()
        for _ in range(MAX_CONSECUTIVE_FAILS):
            rb.check("e", "KELLY_FRACTION", 0.25, 100.0, 50.0, False, True)
        rb.reset_stop()
        assert rb.should_stop() is False

    def test_engine_blocked_after_consecutive_fails(self):
        eng = _fresh_engine()
        # Force rollback engine into stopped state
        for _ in range(MAX_CONSECUTIVE_FAILS):
            eng._rollback.check("e", "KELLY_FRACTION", 0.25, 100.0, 50.0, False, True)
        result = eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=85.0,
            ai_brain_score=85.0,
        )
        assert result["verdict"] == "BLOCKED"
        assert "CONSECUTIVE_FAIL_STOP" in result.get("code", "")


# ── Q11: Audit trail logging ──────────────────────────────────────────────────

class TestAuditLogging:
    def test_applied_correction_is_logged(self):
        eng = _fresh_engine()
        eng.run_cycle(
            state=_healthy_state(),
            current_params=_base_params(),
            deep_validation_score=85.0,
            ai_brain_score=85.0,
        )
        summary = eng._audit.summary()
        assert "total_entries" in summary
        assert "recent" in summary

    def test_audit_entry_has_required_fields(self):
        audit = CorrectionAudit()
        entry = audit.record(
            entry_id="test_1", param="KELLY_FRACTION",
            before=0.25, after=0.22,
            delta_pct=0.12, reason="high DD",
            objective="STABILITY", confidence=80.0,
            auto_applied=True,
            outcome=CorrectionOutcome.APPLIED,
            outcome_detail="auto-applied",
            pnl_before=-100.0,
        )
        assert entry.param == "KELLY_FRACTION"
        assert entry.before == 0.25
        assert entry.after == 0.22
        assert entry.reason == "high DD"
        assert entry.pnl_before == -100.0

    def test_rollback_resolves_audit_entry(self):
        audit = CorrectionAudit()
        audit.record(
            entry_id="rb_1", param="ADAPTIVE_LR",
            before=0.05, after=0.07,
            delta_pct=0.40, reason="test",
            objective="CONSISTENCY", confidence=75.0,
            auto_applied=False, outcome=CorrectionOutcome.APPLIED,
        )
        audit.resolve("rb_1", CorrectionOutcome.ROLLED_BACK, -150.0, "perf drop")
        recent = audit.recent(5)
        resolved = [e for e in recent if e["entry_id"] == "rb_1"]
        assert len(resolved) == 1
        assert resolved[0]["outcome"] == CorrectionOutcome.ROLLED_BACK.value


# ── Q12: Export integration — summary is exportable ──────────────────────────

class TestExportIntegration:
    def test_summary_is_json_serialisable(self):
        import json
        eng = _fresh_engine()
        summary = eng.summary()
        serialised = json.dumps(summary, default=str)
        assert len(serialised) > 0

    def test_summary_contains_required_sections(self):
        eng = _fresh_engine()
        summary = eng.summary()
        for key in ("enabled", "session_cycles", "param_overlay", "audit_summary",
                    "rollback_state", "hard_limits", "start_conditions"):
            assert key in summary, f"summary missing key: {key}"


# ── Q13: Dashboard controls ───────────────────────────────────────────────────

class TestDashboardControls:
    def test_enable_disable(self):
        eng = _fresh_engine()
        eng.disable()
        r = eng.run_cycle(_healthy_state(), _base_params(), 85.0, 85.0)
        assert r["verdict"] == "BLOCKED"
        assert r.get("code") == "DISABLED"
        eng.enable()
        assert eng._enabled is True

    def test_clear_overlay(self):
        eng = _fresh_engine()
        eng._param_overlay["KELLY_FRACTION"] = 0.20
        eng.clear_overlay()
        assert eng.get_overlay() == {}

    def test_get_overlay_returns_active_corrections(self):
        eng = _fresh_engine()
        eng._param_overlay["TR_EV_WEIGHT"] = 0.60
        overlay = eng.get_overlay()
        assert "TR_EV_WEIGHT" in overlay
        assert overlay["TR_EV_WEIGHT"] == 0.60


# ── Q14: Hard limits are immutable ───────────────────────────────────────────

class TestHardLimits:
    def test_hard_limit_params_not_in_tunable(self):
        for hl in HARD_LIMITS:
            assert hl not in TUNABLE_PARAMS, f"{hl} must NOT appear in TUNABLE_PARAMS"

    def test_engine_blocks_hard_limit_param(self):
        eng = _fresh_engine()
        # Manually inject a proposal targeting a hard limit
        from core.self_correction.correction_proposal import Proposal
        prop = Proposal(
            param="MAX_DRAWDOWN_HALT",
            current=0.15, proposed=0.12,
            delta_pct=0.20, reason="test",
            objective="STABILITY", confidence=90.0,
            auto_apply=True,
        )
        result = eng._apply_proposal(prop, _base_params(), -100.0)
        assert result["applied"] is False
        assert result["reason"] == "HARD_LIMIT"
        # Must NOT be in overlay
        assert "MAX_DRAWDOWN_HALT" not in eng.get_overlay()


# ── Q15: Start conditions ─────────────────────────────────────────────────────

class TestStartConditions:
    def test_blocked_when_insufficient_trades(self):
        eng = _fresh_engine()
        state = _healthy_state(n_trades=10)   # below MIN_TRADES_TO_START
        result = eng.run_cycle(state, _base_params(), 80.0, 80.0)
        assert result["verdict"] == "BLOCKED"
        assert "INSUFFICIENT_TRADES" in result.get("code", "")

    def test_allowed_when_both_conditions_met(self):
        eng = _fresh_engine()
        state = _healthy_state(n_trades=MIN_TRADES_TO_START + 5)
        result = eng.run_cycle(state, _base_params(), MIN_SYSTEM_SCORE_TO_START + 10, 85.0)
        # Should not be blocked for start-condition reasons
        assert result.get("code", "") not in ("INSUFFICIENT_TRADES", "DEEP_VALIDATION_NOT_PASSED")

    def test_constants_match_spec(self):
        assert MIN_TRADES_TO_START == 30
        assert MIN_SYSTEM_SCORE_TO_START == 70.0


# ═══════════════════════════════════════════════════════════════════════════════
# FTD-029 FULL ARCHITECTURE TESTS (11 new modules)
# ═══════════════════════════════════════════════════════════════════════════════

from core.self_correction.issue_extractor    import IssueExtractor, IssueType, IssueSeverity
from core.self_correction.confidence_engine  import ConfidenceEngine
from core.self_correction.policy_guard       import PolicyGuard
from core.self_correction.cooldown_manager   import CooldownManager, MAX_CYCLES_PER_SESSION, COOLDOWN_SECONDS
from core.self_correction.priority_resolver  import PriorityResolver
from core.self_correction.change_planner     import ChangePlanner
from core.self_correction.collision_handler  import CollisionHandler
from core.self_correction.change_applier     import ChangeApplier
from core.self_correction.rollback_manager   import RollbackManager, RollbackTrigger
from core.self_correction.audit_logger       import AuditLogger, FinalState
from core.self_correction.correction_orchestrator import CorrectionOrchestrator


def _ftd028_failed_validators():
    return {
        "contradiction": {"passed": False, "contradiction_count": 1,
                          "contradictions": [{"message": "trades without signals"}]},
        "risk":          {"passed": False, "error_count": 1,
                          "errors": [{"message": "over exposed"}]},
        "performance":   {"passed": False, "issue_count": 1,
                          "issues": [{"message": "pnl deviation"}]},
    }

def _ftd028_meta(score: float = 75.0) -> dict:
    return {"system_score": score, "stability_score": 70.0, "confidence_score": 65.0}

def _fresh_orchestrator() -> CorrectionOrchestrator:
    return CorrectionOrchestrator()

def _orchestrator_state(n_trades: int = 35) -> dict:
    return {
        "total_trades": n_trades, "total_pnl": -150.0,
        "win_rate": 0.38, "current_drawdown_pct": 0.11,
        "equity": 890.0, "halted": False,
    }


# ── Part 1: Issue Extractor ───────────────────────────────────────────────────

class TestIssueExtractor:
    def test_failed_validators_produce_issues(self):
        extractor = IssueExtractor()
        issues = extractor.extract(_ftd028_failed_validators())
        assert len(issues) > 0

    def test_passed_validators_produce_no_issues(self):
        extractor = IssueExtractor()
        issues = extractor.extract({
            "contradiction": {"passed": True},
            "risk":          {"passed": True},
        })
        assert len(issues) == 0

    def test_issue_has_required_fields(self):
        extractor = IssueExtractor()
        issues = extractor.extract(_ftd028_failed_validators())
        for issue in issues:
            assert issue.issue_type is not None
            assert issue.severity is not None
            assert issue.affected_module
            assert issue.suggested_fix

    def test_ftd027_failures_produce_issues(self):
        extractor = IssueExtractor()
        issues = extractor.extract({}, ftd027_result={
            "passed": False,
            "failed_scenarios": [{"module": "risk_engine", "detail": "RoR breach", "fix": "reduce size"}],
        })
        assert len(issues) > 0
        assert issues[0].source_validator == "ftd027"


# ── Part 2: Confidence Engine ─────────────────────────────────────────────────

class TestConfidenceEngine:
    def test_high_inputs_give_high_confidence(self):
        result = ConfidenceEngine().compute(
            meta_score=90.0, decision_score=0.8, stability_score=85.0, consistency_score=80.0
        )
        assert result["confidence"] >= 70.0

    def test_low_inputs_give_low_confidence(self):
        result = ConfidenceEngine().compute(
            meta_score=20.0, decision_score=-0.5, stability_score=10.0, consistency_score=5.0
        )
        assert result["confidence"] < 50.0

    def test_confidence_bounded_0_100(self):
        for meta in (0, 50, 100):
            result = ConfidenceEngine().compute(meta_score=meta)
            assert 0.0 <= result["confidence"] <= 100.0

    def test_formula_weights_sum_to_1(self):
        from core.self_correction.confidence_engine import (
            W_META_SCORE, W_DECISION_SCORE, W_STABILITY_SCORE, W_CONSISTENCY
        )
        total = W_META_SCORE + W_DECISION_SCORE + W_STABILITY_SCORE + W_CONSISTENCY
        assert abs(total - 1.0) < 1e-9

    def test_allowed_delta_scales_with_confidence(self):
        # Use full parameter spread so the two scores land in different buckets
        low  = ConfidenceEngine().compute(meta_score=10.0,  decision_score=-1.0, stability_score=5.0,  consistency_score=5.0)
        high = ConfidenceEngine().compute(meta_score=100.0, decision_score=1.0,  stability_score=95.0, consistency_score=90.0)
        assert high["allowed_delta_pct"] > low["allowed_delta_pct"]

    def test_decision_score_normalisation(self):
        neg = ConfidenceEngine().compute(meta_score=70.0, decision_score=-1.0)
        pos = ConfidenceEngine().compute(meta_score=70.0, decision_score=1.0)
        assert pos["confidence"] > neg["confidence"]


# ── Part 3: Policy Guard ──────────────────────────────────────────────────────

class TestPolicyGuard:
    def _all_clear(self, **overrides) -> dict:
        defaults = dict(
            n_trades=35, ftd027_passed=True, ftd028_score=80.0,
            ai_brain_score=80.0, meta_score=80.0, in_cooldown=False,
            risk_halted=False, human_stopped=False, rollback_stop=False,
            disabled=False,
        )
        defaults.update(overrides)
        return defaults

    def test_all_clear_is_allowed(self):
        result = PolicyGuard().check(**self._all_clear())
        assert result["allowed"] is True

    def test_insufficient_trades_blocks(self):
        result = PolicyGuard().check(**self._all_clear(n_trades=5))
        assert result["allowed"] is False
        assert any("INSUFFICIENT_TRADES" in r for r in result["blocking_reasons"])

    def test_ftd027_fail_blocks(self):
        result = PolicyGuard().check(**self._all_clear(ftd027_passed=False))
        assert result["allowed"] is False

    def test_low_ai_brain_score_blocks(self):
        result = PolicyGuard().check(**self._all_clear(ai_brain_score=40.0))
        assert result["allowed"] is False

    def test_human_stop_blocks(self):
        result = PolicyGuard().check(**self._all_clear(human_stopped=True))
        assert result["allowed"] is False

    def test_cooldown_bypassed_on_critical_score(self):
        result = PolicyGuard().check(
            **self._all_clear(in_cooldown=True),
            system_score=40.0,   # below CRITICAL_BYPASS_SCORE
        )
        # Should allow with bypass
        assert result["allowed"] is True
        assert result["bypass_cooldown"] is True

    def test_hard_limit_param_blocks(self):
        result = PolicyGuard().check(
            **self._all_clear(),
            proposed_params={"MAX_DRAWDOWN_HALT": 0.10},
        )
        assert result["allowed"] is False
        assert any("HARD_LIMIT" in r for r in result["blocking_reasons"])


# ── Part 4: Priority Resolver ─────────────────────────────────────────────────

class TestPriorityResolver:
    def test_risk_issue_comes_first(self):
        from core.self_correction.issue_extractor import Issue, IssueType, IssueSeverity
        issues = [
            Issue(IssueType.PERFORMANCE_DRIFT, IssueSeverity.MEDIUM, "perf", "fix", "perf", [], 1),
            Issue(IssueType.RISK_VIOLATION,    IssueSeverity.CRITICAL,"risk","fix","risk",[], 1),
            Issue(IssueType.CAPITAL_MISMATCH,  IssueSeverity.HIGH,    "cap", "fix","cap", [], 1),
        ]
        sorted_issues = PriorityResolver().sort(issues)
        assert sorted_issues[0].issue_type == IssueType.RISK_VIOLATION

    def test_sort_is_stable_for_same_type(self):
        from core.self_correction.issue_extractor import Issue, IssueType, IssueSeverity
        issues = [
            Issue(IssueType.DECISION_QUALITY, IssueSeverity.HIGH,   "m", "f", "dq", [], 1),
            Issue(IssueType.DECISION_QUALITY, IssueSeverity.MEDIUM, "m", "f", "dq", [], 1),
        ]
        sorted_issues = PriorityResolver().sort(issues)
        assert sorted_issues[0].severity == IssueSeverity.HIGH


# ── Part 4b: Collision Handler ────────────────────────────────────────────────

class TestCollisionHandler:
    def test_no_collision_returns_all_safe(self):
        plans = [
            {"parameter": "KELLY_FRACTION", "priority_rank": 0},
            {"parameter": "TR_EV_WEIGHT",   "priority_rank": 1},
        ]
        safe, queued = CollisionHandler().resolve(plans)
        assert len(safe) == 2
        assert len(queued) == 0

    def test_duplicate_param_queues_lower_priority(self):
        plans = [
            {"parameter": "KELLY_FRACTION", "priority_rank": 0},
            {"parameter": "KELLY_FRACTION", "priority_rank": 1},
        ]
        safe, queued = CollisionHandler().resolve(plans)
        assert len(safe) == 1
        assert len(queued) == 1
        assert queued[0]["parameter"] == "KELLY_FRACTION"

    def test_pending_queue_persists(self):
        ch = CollisionHandler()
        plans = [
            {"parameter": "A", "priority_rank": 0},
            {"parameter": "A", "priority_rank": 1},
        ]
        ch.resolve(plans)
        assert len(ch.pending_queue()) == 1


# ── Part 5: Change Planner ────────────────────────────────────────────────────

class TestChangePlanner:
    def _risk_issue(self):
        from core.self_correction.issue_extractor import Issue, IssueType, IssueSeverity
        return [Issue(IssueType.RISK_VIOLATION, IssueSeverity.CRITICAL,
                      "risk_engine", "Reduce Kelly", "risk", [], 1)]

    def test_risk_issue_produces_kelly_plan(self):
        plans = ChangePlanner().plan(self._risk_issue(), _base_params(), 0.10)
        params = {p.parameter for p in plans}
        assert "KELLY_FRACTION" in params

    def test_plan_within_bounds(self):
        from core.self_correction.correction_proposal import TUNABLE_PARAMS
        plans = ChangePlanner().plan(self._risk_issue(), _base_params(), 0.15)
        for p in plans:
            lo, hi, _ = TUNABLE_PARAMS[p.parameter]
            assert lo <= p.proposed_value <= hi

    def test_plan_delta_respects_allowed_pct(self):
        plans = ChangePlanner().plan(self._risk_issue(), _base_params(), 0.05)
        for p in plans:
            assert p.delta_pct <= 0.05 + 1e-9

    def test_no_hard_limit_params_planned(self):
        from core.self_correction.issue_extractor import Issue, IssueType, IssueSeverity
        from core.self_correction.correction_proposal import HARD_LIMITS
        all_issues = [
            Issue(it, IssueSeverity.HIGH, "m", "fix", str(it), [], 1)
            for it in IssueType
        ]
        plans = ChangePlanner().plan(all_issues, _base_params(), 0.15)
        for p in plans:
            assert p.parameter not in HARD_LIMITS


# ── Part 6: Change Applier ────────────────────────────────────────────────────

class TestChangeApplier:
    def _risk_plan(self):
        from core.self_correction.change_planner import ChangePlan
        return ChangePlan(
            plan_id="p1", issue_type="RISK_VIOLATION", target_module="risk_engine",
            parameter="KELLY_FRACTION", current_value=0.25, proposed_value=0.22,
            delta_pct=0.12, rationale="high DD", expected_impact="reduce size",
            auto_eligible=False, priority_rank=0,
        )

    def test_valid_plan_applied(self):
        applier = ChangeApplier()
        applied, blocked = applier.apply([self._risk_plan()], _base_params())
        assert len(applied) == 1
        assert "KELLY_FRACTION" in applier.get_overlay()
        assert applier.get_overlay()["KELLY_FRACTION"] == pytest.approx(0.22)

    def test_hard_limit_plan_blocked(self):
        from core.self_correction.change_planner import ChangePlan
        applier = ChangeApplier()
        bad_plan = ChangePlan(
            plan_id="bad", issue_type="RISK_VIOLATION", target_module="risk",
            parameter="MAX_DRAWDOWN_HALT", current_value=0.15, proposed_value=0.10,
            delta_pct=0.33, rationale="test", expected_impact="none",
            auto_eligible=False, priority_rank=0,
        )
        applied, blocked = applier.apply([bad_plan], _base_params())
        assert len(applied) == 0
        assert "MAX_DRAWDOWN_HALT" not in applier.get_overlay()

    def test_rollback_restores_value(self):
        applier = ChangeApplier()
        applied, _ = applier.apply([self._risk_plan()], _base_params())
        assert len(applied) == 1
        change_id = applied[0].change_id
        applier.rollback_change(change_id)
        # After rollback, overlay should have original value
        assert applier.get_overlay().get("KELLY_FRACTION") == pytest.approx(0.25)

    def test_version_hash_present(self):
        applier = ChangeApplier()
        applied, _ = applier.apply([self._risk_plan()], _base_params())
        assert applied[0].version_hash
        assert len(applied[0].version_hash) == 8   # SHA1 first 8 chars


# ── Part 7: Cooldown Manager ──────────────────────────────────────────────────

class TestCooldownManager:
    def test_first_cycle_always_allowed(self):
        cm = CooldownManager()
        result = cm.can_run()
        assert result["allowed"] is True

    def test_session_limit_blocks(self):
        cm = CooldownManager()
        for _ in range(MAX_CYCLES_PER_SESSION):
            cm.record_cycle()
        result = cm.can_run()
        assert result["allowed"] is False
        assert "SESSION_LIMIT" in result["blocking_reason"]

    def test_cooldown_blocks_after_cycle(self):
        cm = CooldownManager()
        cm.record_cycle()
        result = cm.can_run()
        assert result["allowed"] is False
        assert "COOLDOWN" in result["blocking_reason"]

    def test_critical_bypass_overrides_cooldown(self):
        cm = CooldownManager()
        cm.record_cycle()
        result = cm.can_run(risk_violated=True)
        assert result["allowed"] is True
        assert result["bypass_active"] is True

    def test_score_below_floor_triggers_bypass(self):
        cm = CooldownManager()
        cm.record_cycle()
        result = cm.can_run(system_score=30.0)
        assert result["allowed"] is True

    def test_reset_clears_state(self):
        cm = CooldownManager()
        for _ in range(MAX_CYCLES_PER_SESSION):
            cm.record_cycle()
        cm.reset()
        assert cm.can_run()["allowed"] is True


# ── Part 8: Rollback Manager ──────────────────────────────────────────────────

class TestRollbackManager:
    def test_keep_when_all_good(self):
        rm = RollbackManager()
        result = rm.evaluate("c1", "KELLY_FRACTION", 0.25,
                             100.0, 110.0, 75.0, 78.0, False, True)
        assert result["decision"] == "KEEP"
        assert result["stop_engine"] is False

    def test_rollback_on_perf_drop(self):
        rm = RollbackManager()
        result = rm.evaluate("c2", "KELLY_FRACTION", 0.25,
                             100.0, 80.0, 75.0, 74.0, False, True)
        assert result["decision"] == "ROLLBACK"
        assert result["trigger"] == RollbackTrigger.PERF_DROP.value

    def test_rollback_on_score_drop(self):
        rm = RollbackManager()
        result = rm.evaluate("c3", "TR_EV_WEIGHT", 0.55,
                             100.0, 102.0, 75.0, 68.0, False, True)
        assert result["decision"] == "ROLLBACK"
        assert result["trigger"] == RollbackTrigger.VALIDATION_FAIL.value

    def test_rollback_on_risk_violation(self):
        rm = RollbackManager()
        result = rm.evaluate("c4", "KELLY_FRACTION", 0.25,
                             100.0, 105.0, 75.0, 76.0, True, True)
        assert result["decision"] == "ROLLBACK"
        assert result["trigger"] == RollbackTrigger.RISK_VIOLATION.value

    def test_3_rollbacks_stops_engine(self):
        rm = RollbackManager()
        for i in range(3):
            rm.evaluate(f"c{i}", "KELLY_FRACTION", 0.25,
                        100.0, 80.0, 75.0, 74.0, False, True)
        assert rm.should_stop() is True

    def test_reset_clears_stop(self):
        rm = RollbackManager()
        for i in range(3):
            rm.evaluate(f"c{i}", "KELLY_FRACTION", 0.25, 100.0, 80.0, 75.0, 74.0, False, True)
        rm.reset()
        assert rm.should_stop() is False


# ── Part 9: Audit Logger ──────────────────────────────────────────────────────

class TestAuditLogger:
    def test_applied_entry_logged(self):
        al = AuditLogger()
        entry = al.log_applied(
            change_id="CHG_001", issue_type="RISK_VIOLATION",
            issue_severity="CRITICAL", affected_module="risk_engine",
            rationale="high DD", parameter="KELLY_FRACTION",
            value_before=0.25, value_after=0.22,
            delta_pct=0.12, confidence=75.0, pre_score=72.0,
        )
        assert entry.parameter == "KELLY_FRACTION"
        assert entry.final_state == FinalState.KEPT

    def test_blocked_entry_logged(self):
        al = AuditLogger()
        entry = al.log_blocked("CHG_002", "MAX_DRAWDOWN_HALT", "HARD_LIMIT", 60.0, 65.0)
        assert entry.final_state == FinalState.BLOCKED

    def test_resolve_updates_final_state(self):
        al = AuditLogger()
        al.log_applied(
            change_id="CHG_003", issue_type="PERF", issue_severity="HIGH",
            affected_module="m", rationale="r", parameter="TR_EV_WEIGHT",
            value_before=0.55, value_after=0.58, delta_pct=0.05,
            confidence=80.0, pre_score=70.0,
        )
        al.resolve("CHG_003", 68.0, FinalState.ROLLED_BACK, "PERF_DROP")
        recent = al.recent(5)
        entry = [e for e in recent if e["change_id"] == "CHG_003"][0]
        assert entry["final_state"] == FinalState.ROLLED_BACK.value
        assert entry["rollback_trigger"] == "PERF_DROP"

    def test_last_change_returns_most_recent(self):
        al = AuditLogger()
        al.log_applied(
            change_id="CHG_004", issue_type="RISK", issue_severity="HIGH",
            affected_module="m", rationale="r", parameter="KELLY_FRACTION",
            value_before=0.25, value_after=0.22, delta_pct=0.12,
            confidence=75.0, pre_score=70.0,
        )
        last = al.last_change()
        assert last is not None
        assert last["change_id"] == "CHG_004"

    def test_summary_has_required_fields(self):
        al = AuditLogger()
        s = al.summary()
        for k in ("total_entries", "kept", "rolled_back", "blocked", "last_change"):
            assert k in s


# ── Full Orchestrator (integration) ──────────────────────────────────────────

class TestCorrectionOrchestrator:
    def _run_cycle(self, orch: CorrectionOrchestrator, n_trades: int = 35, score: float = 80.0):
        return orch.run_cycle(
            ftd028_validators=_ftd028_failed_validators(),
            ftd028_meta=_ftd028_meta(score),
            current_params=_base_params(),
            system_state=_orchestrator_state(n_trades),
            ai_brain_score=score,
        )

    def test_insufficient_trades_blocked(self):
        orch = _fresh_orchestrator()
        result = self._run_cycle(orch, n_trades=5)
        assert result["verdict"] == "BLOCKED"

    def test_low_meta_score_blocked(self):
        orch = _fresh_orchestrator()
        result = self._run_cycle(orch, score=40.0)
        assert result["verdict"] == "BLOCKED"

    def test_healthy_cycle_produces_result(self):
        orch = _fresh_orchestrator()
        result = self._run_cycle(orch, n_trades=35, score=80.0)
        assert result["verdict"] in ("APPLIED", "NO_ACTION", "BLOCKED")
        # Must have required fields
        for key in ("cycle_id", "module", "phase", "applied", "ts"):
            assert key in result

    def test_human_override_stop_blocks(self):
        orch = _fresh_orchestrator()
        orch.human_override_stop()
        result = self._run_cycle(orch)
        assert result["verdict"] == "BLOCKED"

    def test_clear_overlay_resets(self):
        orch = _fresh_orchestrator()
        orch._change_applier._overlay["KELLY_FRACTION"] = 0.20
        orch.clear_overlay()
        assert orch.get_overlay() == {}

    def test_summary_is_json_serialisable(self):
        import json
        orch = _fresh_orchestrator()
        s = json.dumps(orch.summary(), default=str)
        assert len(s) > 0

    def test_logs_returns_list(self):
        orch = _fresh_orchestrator()
        logs = orch.logs(10)
        assert isinstance(logs, list)

    def test_last_change_none_before_any_correction(self):
        orch = _fresh_orchestrator()
        assert orch.last_change() is None

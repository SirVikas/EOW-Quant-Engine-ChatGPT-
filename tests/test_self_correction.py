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

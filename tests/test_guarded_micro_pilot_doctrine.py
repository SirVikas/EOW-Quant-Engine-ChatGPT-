"""
Tests for FTD-GMPD: Ultra-Guarded Micro Pilot Execution Doctrine.

Verifies:
  - Human confirmation invariants (every execution entry must be confirmed)
  - No autonomous execution authority anywhere in the output
  - Immutable pilot ledger guarantees
  - Kill-switch enforcement
  - Rollback integrity markers
  - Constitutional-state integrity
  - Fail-open behavior (never raises)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.micro_pilot_doctrine import (
    PAPER_ONLY,
    SHADOW_OBSERVATION,
    HUMAN_ARMED_MICRO,
    SINGLE_CONFIRM_EXECUTION,
    MANUAL_KILL_SWITCH,
    CONSTITUTION_LOCKDOWN,
    REALITY_CONSISTENT,
    EXECUTION_DRIFT,
    SLIPPAGE_COLLAPSE,
    LIQUIDITY_FAILURE,
    HUMAN_REVIEW_ESCALATION,
    PILOT_LOCKDOWN_RECOMMENDED,
    PILOT_HARD_PRINCIPLES,
    _execution_readiness_metric,
    _fill_quality_metric,
    _slippage_reconciliation_metric,
    _latency_reconciliation_metric,
    _fee_drag_reconciliation_metric,
    _hold_economics_reconciliation_metric,
    _confirmation_chain_integrity,
    _kill_switch_advisory,
    _pilot_survivability_score,
    _classify_pilot,
    _assess_pilot_state,
    _generate_pilot_recommendations,
    _generate_pilot_audit_entry,
    _recommend_pilot_opportunity,
    compute_guarded_micro_pilot,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _trade(net_pnl=1.0, gross_pnl=1.2, fee_entry=0.05, fee_exit=0.05,
           slippage_cost=0.02, entry_ts=1000, exit_ts=2000):
    return {
        "net_pnl": net_pnl, "gross_pnl": gross_pnl,
        "fee_entry": fee_entry, "fee_exit": fee_exit,
        "slippage_cost": slippage_cost,
        "entry_ts": entry_ts, "exit_ts": exit_ts,
    }


def _trades(n=50, **kwargs):
    return [_trade(**kwargs) for _ in range(n)]


def _exec_entry(human_confirmed=True, expected_fill=1.0, actual_fill=1.0,
                expected_slippage=0.02, actual_slippage=0.02,
                expected_latency_ms=10.0, actual_latency_ms=10.0,
                expected_fee=0.10, actual_fee=0.10,
                expected_net_pnl=1.0, actual_net_pnl=1.0,
                auto_authorized=False):
    return {
        "entry_type":          "EXECUTION",
        "human_confirmed":     human_confirmed,
        "expected_fill":       expected_fill,
        "actual_fill":         actual_fill,
        "expected_slippage":   expected_slippage,
        "actual_slippage":     actual_slippage,
        "expected_latency_ms": expected_latency_ms,
        "actual_latency_ms":   actual_latency_ms,
        "expected_fee":        expected_fee,
        "actual_fee":          actual_fee,
        "expected_net_pnl":    expected_net_pnl,
        "actual_net_pnl":      actual_net_pnl,
        "auto_authorized":     auto_authorized,
        "immutable":           True,
    }


def _analysis_entry(pilot_state=PAPER_ONLY, auto_authorized=False):
    return {
        "entry_type":      "ANALYSIS",
        "pilot_state":     pilot_state,
        "auto_authorized": auto_authorized,
        "immutable":       True,
    }


# ── TestExecutionReadinessMetric ───────────────────────────────────────────────

class TestExecutionReadinessMetric:
    def test_empty_trades_returns_insufficient(self):
        r = _execution_readiness_metric([])
        assert r["score"] == 0.0
        assert r["tier"] == "INSUFFICIENT"
        assert r["trade_count"] == 0

    def test_no_fees_no_slippage_low_score(self):
        r = _execution_readiness_metric(_trades(100, fee_entry=0, fee_exit=0, slippage_cost=0))
        assert r["score"] < 25.0
        assert r["fee_coverage"] == 0.0
        assert r["slippage_coverage"] == 0.0

    def test_full_fee_coverage_raises_score(self):
        r = _execution_readiness_metric(_trades(100))
        assert r["fee_coverage"] == 1.0
        assert r["score"] > 10.0

    def test_large_corpus_full_coverage_adequate(self):
        r = _execution_readiness_metric(_trades(500))
        assert r["tier"] == "ADEQUATE"
        assert r["score"] >= 70.0

    def test_corpus_size_scales_score(self):
        small = _execution_readiness_metric(_trades(25))
        large = _execution_readiness_metric(_trades(500))
        assert large["score"] > small["score"]

    def test_none_values_handled(self):
        trades = [{"net_pnl": None, "fee_entry": None, "fee_exit": None, "slippage_cost": None}]
        r = _execution_readiness_metric(trades)
        assert r["score"] < 5.0
        assert r["tier"] == "INSUFFICIENT"


# ── TestFillQuality ────────────────────────────────────────────────────────────

class TestFillQuality:
    def test_empty_ledger_insufficient(self):
        r = _fill_quality_metric([])
        assert r["tier"] == "INSUFFICIENT"
        assert r["sample_count"] == 0

    def test_analysis_entries_only_insufficient(self):
        r = _fill_quality_metric([_analysis_entry(), _analysis_entry()])
        assert r["tier"] == "INSUFFICIENT"
        assert r["sample_count"] == 0

    def test_perfect_fill_minimal_score(self):
        r = _fill_quality_metric([_exec_entry(expected_fill=1.0, actual_fill=1.0)])
        assert r["score"] < 5.0
        assert r["tier"] == "MINIMAL"

    def test_poor_fill_high_score(self):
        r = _fill_quality_metric([_exec_entry(expected_fill=1.0, actual_fill=0.4)])
        assert r["score"] >= 35.0
        assert r["tier"] == "HIGH"

    def test_zero_expected_fill_no_crash(self):
        r = _fill_quality_metric([_exec_entry(expected_fill=0.0, actual_fill=0.5)])
        assert isinstance(r, dict)
        assert "tier" in r


# ── TestSlippageReconciliation ─────────────────────────────────────────────────

class TestSlippageReconciliation:
    def test_empty_ledger_insufficient(self):
        r = _slippage_reconciliation_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_no_execution_entries_insufficient(self):
        r = _slippage_reconciliation_metric([_analysis_entry()])
        assert r["tier"] == "INSUFFICIENT"

    def test_low_slippage_divergence(self):
        r = _slippage_reconciliation_metric([_exec_entry(expected_slippage=0.02, actual_slippage=0.021)])
        assert r["tier"] == "LOW"

    def test_high_slippage_divergence(self):
        entries = [_exec_entry(expected_slippage=0.02, actual_slippage=0.10)] * 3
        r = _slippage_reconciliation_metric(entries)
        assert r["tier"] in ("HIGH", "CRITICAL")


# ── TestLatencyReconciliation ──────────────────────────────────────────────────

class TestLatencyReconciliation:
    def test_empty_ledger_insufficient(self):
        r = _latency_reconciliation_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_no_execution_entries_insufficient(self):
        r = _latency_reconciliation_metric([_analysis_entry()])
        assert r["tier"] == "INSUFFICIENT"

    def test_acceptable_latency(self):
        r = _latency_reconciliation_metric([_exec_entry(expected_latency_ms=10.0, actual_latency_ms=10.5)])
        assert r["score"] < 10.0
        assert r["tier"] == "LOW"

    def test_high_latency_inflation(self):
        r = _latency_reconciliation_metric([_exec_entry(expected_latency_ms=10.0, actual_latency_ms=30.0)])
        assert r["score"] >= 30.0
        assert r["tier"] in ("MODERATE", "HIGH", "CRITICAL")


# ── TestFeeDragReconciliation ──────────────────────────────────────────────────

class TestFeeDragReconciliation:
    def test_empty_ledger_insufficient(self):
        r = _fee_drag_reconciliation_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_no_execution_entries_insufficient(self):
        r = _fee_drag_reconciliation_metric([_analysis_entry()])
        assert r["tier"] == "INSUFFICIENT"

    def test_low_fee_drag(self):
        r = _fee_drag_reconciliation_metric([_exec_entry(expected_fee=0.10, actual_fee=0.102)])
        assert r["tier"] == "LOW"

    def test_high_fee_drag(self):
        r = _fee_drag_reconciliation_metric([_exec_entry(expected_fee=0.10, actual_fee=0.25)])
        assert r["tier"] in ("HIGH", "CRITICAL")


# ── TestHoldEconomicsReconciliation ───────────────────────────────────────────

class TestHoldEconomicsReconciliation:
    def test_empty_ledger_insufficient(self):
        r = _hold_economics_reconciliation_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_no_execution_entries_insufficient(self):
        r = _hold_economics_reconciliation_metric([_analysis_entry()])
        assert r["tier"] == "INSUFFICIENT"

    def test_meets_expectations(self):
        r = _hold_economics_reconciliation_metric([_exec_entry(expected_net_pnl=1.0, actual_net_pnl=1.0)])
        assert r["score"] == 0.0

    def test_underperforms_expectations(self):
        entries = [_exec_entry(expected_net_pnl=1.0, actual_net_pnl=0.1)] * 3
        r = _hold_economics_reconciliation_metric(entries)
        assert r["score"] > 0.0
        assert r["tier"] in ("MODERATE", "HIGH", "CRITICAL")

    def test_outperforms_expectations_score_zero(self):
        r = _hold_economics_reconciliation_metric([_exec_entry(expected_net_pnl=1.0, actual_net_pnl=2.0)])
        assert r["score"] == 0.0


# ── TestConfirmationChainIntegrity ─────────────────────────────────────────────

class TestConfirmationChainIntegrity:
    def test_empty_ledger(self):
        r = _confirmation_chain_integrity([])
        assert r["integrity"] == "EMPTY"
        assert r["all_human_confirmed"] is True
        assert r["unauthorized_entries"] == 0
        assert r["execution_entries"] == 0

    def test_analysis_entries_only_intact(self):
        r = _confirmation_chain_integrity([_analysis_entry(), _analysis_entry()])
        assert r["integrity"] == "INTACT"
        assert r["all_human_confirmed"] is True
        assert r["execution_entries"] == 0

    def test_all_confirmed_exec_intact(self):
        r = _confirmation_chain_integrity([_exec_entry(human_confirmed=True)] * 3)
        assert r["integrity"] == "INTACT"
        assert r["all_human_confirmed"] is True
        assert r["execution_entries"] == 3

    def test_unauthorized_exec_violated(self):
        r = _confirmation_chain_integrity([_exec_entry(human_confirmed=False)])
        assert r["integrity"] == "VIOLATED"
        assert r["all_human_confirmed"] is False
        assert r["unauthorized_entries"] == 1

    def test_auto_authorized_violated(self):
        e = _analysis_entry(auto_authorized=True)
        r = _confirmation_chain_integrity([e])
        assert r["integrity"] == "VIOLATED"
        assert r["auto_authorized_entries"] == 1

    def test_mixed_entries_all_confirmed(self):
        ledger = [_analysis_entry(), _exec_entry(), _exec_entry()]
        r = _confirmation_chain_integrity(ledger)
        assert r["integrity"] == "INTACT"
        assert r["total_entries"] == 3
        assert r["execution_entries"] == 2


# ── TestKillSwitchAdvisory ─────────────────────────────────────────────────────

class TestKillSwitchAdvisory:
    def _clean_recon(self):
        return {
            "fill_quality":                  {"score": 2.0, "tier": "MINIMAL", "sample_count": 1},
            "slippage_reconciliation":       {"score": 5.0, "tier": "LOW",     "sample_count": 1},
            "latency_reconciliation":        {"score": 5.0, "tier": "LOW",     "sample_count": 1},
            "fee_drag_reconciliation":       {"score": 5.0, "tier": "LOW",     "sample_count": 1},
            "hold_economics_reconciliation": {"score": 5.0, "tier": "LOW",     "sample_count": 1},
        }

    def test_no_triggers_no_engage(self):
        chain = _confirmation_chain_integrity([])
        r = _kill_switch_advisory(self._clean_recon(), chain)
        assert r["engage"] is False
        assert r["priority"] == "NONE"
        assert r["trigger_count"] == 0

    def test_unauthorized_entry_engages(self):
        chain = _confirmation_chain_integrity([_exec_entry(human_confirmed=False)])
        r = _kill_switch_advisory(self._clean_recon(), chain)
        assert r["engage"] is True
        assert r["priority"] in ("HIGH", "CRITICAL")

    def test_auto_authorized_violation_engages(self):
        chain = {"all_human_confirmed": True, "auto_authorized_entries": 1,
                 "unauthorized_entries": 0, "execution_entries": 0, "total_entries": 1}
        r = _kill_switch_advisory(self._clean_recon(), chain)
        assert r["engage"] is True

    def test_critical_slippage_engages(self):
        recon = self._clean_recon()
        recon["slippage_reconciliation"] = {"score": 85.0, "tier": "CRITICAL", "sample_count": 3}
        chain = _confirmation_chain_integrity([])
        r = _kill_switch_advisory(recon, chain)
        assert r["engage"] is True

    def test_multiple_triggers_critical_priority(self):
        recon = self._clean_recon()
        recon["slippage_reconciliation"]       = {"score": 85.0, "tier": "CRITICAL", "sample_count": 1}
        recon["hold_economics_reconciliation"] = {"score": 70.0, "tier": "HIGH",     "sample_count": 1}
        chain = _confirmation_chain_integrity([])
        r = _kill_switch_advisory(recon, chain)
        assert r["priority"] == "CRITICAL"
        assert r["trigger_count"] >= 2


# ── TestPilotSurvivabilityScore ────────────────────────────────────────────────

class TestPilotSurvivabilityScore:
    def _insuf_recon(self):
        return {k: {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0}
                for k in ["fill_quality", "slippage_reconciliation",
                           "latency_reconciliation", "fee_drag_reconciliation",
                           "hold_economics_reconciliation"]}

    def test_no_exec_low_readiness_weak(self):
        read = {"score": 20.0, "tier": "EARLY"}
        r = _pilot_survivability_score(read, self._insuf_recon())
        assert r["score"] == pytest.approx(12.0)
        assert r["tier"] == "WEAK"

    def test_no_exec_high_readiness_capped_at_sixty(self):
        read = {"score": 100.0, "tier": "ADEQUATE"}
        r = _pilot_survivability_score(read, self._insuf_recon())
        assert r["score"] == pytest.approx(60.0)
        assert r["tier"] == "ADEQUATE"

    def test_perfect_execution_strong(self):
        read  = {"score": 90.0, "tier": "ADEQUATE"}
        recon = {k: {"score": 0.0, "tier": "MINIMAL", "sample_count": 1}
                 for k in ["fill_quality", "slippage_reconciliation",
                            "latency_reconciliation", "fee_drag_reconciliation",
                            "hold_economics_reconciliation"]}
        r = _pilot_survivability_score(read, recon)
        assert r["score"] >= 70.0
        assert r["tier"] == "STRONG"

    def test_terrible_execution_weak(self):
        read  = {"score": 50.0, "tier": "DEVELOPING"}
        recon = {k: {"score": 100.0, "tier": "CRITICAL", "sample_count": 2}
                 for k in ["fill_quality", "slippage_reconciliation",
                            "latency_reconciliation", "fee_drag_reconciliation",
                            "hold_economics_reconciliation"]}
        r = _pilot_survivability_score(read, recon)
        assert r["score"] < 50.0

    def test_empty_inputs_no_crash(self):
        r = _pilot_survivability_score({}, {})
        assert r["score"] == 0.0
        assert r["tier"] == "WEAK"


# ── TestPilotClassification ────────────────────────────────────────────────────

class TestPilotClassification:
    def _surv(self, score=60.0):
        tier = "STRONG" if score >= 70 else "ADEQUATE" if score >= 50 else "MARGINAL" if score >= 30 else "WEAK"
        return {"score": score, "tier": tier}

    def _read(self, tier="ADEQUATE", score=80.0):
        return {"score": score, "tier": tier}

    def _insuf_recon(self):
        return {k: {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0}
                for k in ["fill_quality", "slippage_reconciliation",
                           "latency_reconciliation", "fee_drag_reconciliation",
                           "hold_economics_reconciliation"]}

    def test_unauthorized_entries_lockdown(self):
        chain = _confirmation_chain_integrity([_exec_entry(human_confirmed=False)])
        r = _classify_pilot(self._insuf_recon(), self._surv(60), chain, self._read())
        assert r == PILOT_LOCKDOWN_RECOMMENDED

    def test_auto_authorized_lockdown(self):
        chain = {"all_human_confirmed": True, "auto_authorized_entries": 1,
                 "unauthorized_entries": 0, "execution_entries": 0, "total_entries": 1}
        r = _classify_pilot(self._insuf_recon(), self._surv(60), chain, self._read())
        assert r == PILOT_LOCKDOWN_RECOMMENDED

    def test_low_survivability_with_data_lockdown(self):
        chain = _confirmation_chain_integrity([_analysis_entry()])
        recon = {k: {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 1}
                 for k in ["fill_quality", "slippage_reconciliation",
                            "latency_reconciliation", "fee_drag_reconciliation",
                            "hold_economics_reconciliation"]}
        r = _classify_pilot(recon, self._surv(5.0), chain, self._read("DEVELOPING", 45.0))
        assert r == PILOT_LOCKDOWN_RECOMMENDED

    def test_marginal_survivability_human_review(self):
        chain = _confirmation_chain_integrity([])
        recon = {k: {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 1}
                 for k in ["fill_quality", "slippage_reconciliation",
                            "latency_reconciliation", "fee_drag_reconciliation",
                            "hold_economics_reconciliation"]}
        r = _classify_pilot(recon, self._surv(25.0), chain, self._read("DEVELOPING", 45.0))
        assert r == HUMAN_REVIEW_ESCALATION

    def test_critical_slippage_collapse(self):
        chain = _confirmation_chain_integrity([])
        recon = self._insuf_recon()
        recon["slippage_reconciliation"] = {"score": 90.0, "tier": "CRITICAL", "sample_count": 2}
        r = _classify_pilot(recon, self._surv(60), chain, self._read())
        assert r == SLIPPAGE_COLLAPSE

    def test_high_fill_liquidity_failure(self):
        chain = _confirmation_chain_integrity([])
        recon = self._insuf_recon()
        recon["fill_quality"] = {"score": 60.0, "tier": "HIGH", "sample_count": 2}
        r = _classify_pilot(recon, self._surv(60), chain, self._read())
        assert r == LIQUIDITY_FAILURE

    def test_clean_state_reality_consistent(self):
        chain = _confirmation_chain_integrity([])
        r = _classify_pilot(self._insuf_recon(), self._surv(60), chain, self._read())
        assert r == REALITY_CONSISTENT


# ── TestPilotStateAssessment ───────────────────────────────────────────────────

class TestPilotStateAssessment:
    def _read(self, score=80.0, tier="ADEQUATE"):
        return {"score": score, "tier": tier}

    def _surv(self, score=60.0):
        return {"score": score, "tier": "ADEQUATE" if score >= 50 else "MARGINAL"}

    def _clean_chain(self, exec_entries=0):
        return {"integrity": "INTACT", "all_human_confirmed": True,
                "unauthorized_entries": 0, "execution_entries": exec_entries,
                "total_entries": exec_entries, "auto_authorized_entries": 0}

    def test_lockdown_recommended_gives_lockdown(self):
        r = _assess_pilot_state(self._read(), PILOT_LOCKDOWN_RECOMMENDED, self._surv(), self._clean_chain(), 0)
        assert r == CONSTITUTION_LOCKDOWN

    def test_unauthorized_chain_gives_lockdown(self):
        chain = {"integrity": "VIOLATED", "all_human_confirmed": False,
                 "unauthorized_entries": 1, "execution_entries": 1,
                 "total_entries": 1, "auto_authorized_entries": 0}
        r = _assess_pilot_state(self._read(), REALITY_CONSISTENT, self._surv(), chain, 1)
        assert r == CONSTITUTION_LOCKDOWN

    def test_escalation_gives_kill_switch(self):
        for cls in (HUMAN_REVIEW_ESCALATION, SLIPPAGE_COLLAPSE, LIQUIDITY_FAILURE):
            r = _assess_pilot_state(self._read(), cls, self._surv(), self._clean_chain(), 0)
            assert r == MANUAL_KILL_SWITCH

    def test_reality_consistent_with_exec_history_single_confirm(self):
        r = _assess_pilot_state(
            self._read(80.0), REALITY_CONSISTENT,
            {"score": 65.0, "tier": "STRONG"},
            self._clean_chain(exec_entries=2), 3,
        )
        assert r == SINGLE_CONFIRM_EXECUTION

    def test_good_readiness_no_exec_human_armed(self):
        r = _assess_pilot_state(self._read(80.0), REALITY_CONSISTENT, self._surv(55.0), self._clean_chain(0), 0)
        assert r == HUMAN_ARMED_MICRO

    def test_developing_readiness_shadow(self):
        r = _assess_pilot_state(self._read(35.0, "EARLY"), REALITY_CONSISTENT, self._surv(20.0), self._clean_chain(), 0)
        assert r == SHADOW_OBSERVATION

    def test_insufficient_readiness_paper_only(self):
        r = _assess_pilot_state(self._read(0.0, "INSUFFICIENT"), REALITY_CONSISTENT, self._surv(0.0), self._clean_chain(), 0)
        assert r == PAPER_ONLY


# ── TestRecommendationGeneration ──────────────────────────────────────────────

class TestRecommendationGeneration:
    def _insuf_recon(self):
        return {k: {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0}
                for k in ["fill_quality", "slippage_reconciliation",
                           "latency_reconciliation", "fee_drag_reconciliation",
                           "hold_economics_reconciliation"]}

    def _ks(self, engage=False):
        return {"engage": engage, "reason": "test", "priority": "CRITICAL" if engage else "NONE",
                "trigger_count": 1 if engage else 0}

    def test_kill_switch_active_generates_critical(self):
        recs = _generate_pilot_recommendations(
            PAPER_ONLY, REALITY_CONSISTENT, {"score": 0.0, "tier": "INSUFFICIENT"},
            self._insuf_recon(), self._ks(engage=True), 0,
        )
        priorities = [r["priority"] for r in recs]
        assert "CRITICAL" in priorities

    def test_lockdown_state_generates_critical(self):
        recs = _generate_pilot_recommendations(
            CONSTITUTION_LOCKDOWN, PILOT_LOCKDOWN_RECOMMENDED,
            {"score": 0.0, "tier": "INSUFFICIENT"},
            self._insuf_recon(), self._ks(), 0,
        )
        types = [r["type"] for r in recs]
        assert "CONSTITUTIONAL_LOCKDOWN" in types

    def test_insufficient_readiness_generates_high(self):
        recs = _generate_pilot_recommendations(
            PAPER_ONLY, REALITY_CONSISTENT, {"score": 5.0, "tier": "INSUFFICIENT"},
            self._insuf_recon(), self._ks(), 0,
        )
        assert any(r["type"] == "EXECUTION_READINESS" for r in recs)

    def test_no_ledger_history_medium_rec(self):
        recs = _generate_pilot_recommendations(
            HUMAN_ARMED_MICRO, REALITY_CONSISTENT, {"score": 80.0, "tier": "ADEQUATE"},
            self._insuf_recon(), self._ks(), 0,
        )
        assert any(r["type"] == "PILOT_READINESS" for r in recs)

    def test_execution_drift_with_ledger(self):
        recs = _generate_pilot_recommendations(
            MANUAL_KILL_SWITCH, EXECUTION_DRIFT, {"score": 70.0, "tier": "ADEQUATE"},
            self._insuf_recon(), self._ks(), 5,
        )
        assert any(r["type"] == "EXECUTION_DRIFT" for r in recs)

    def test_all_recommendations_auto_authorized_false(self):
        recs = _generate_pilot_recommendations(
            PAPER_ONLY, REALITY_CONSISTENT, {"score": 0.0, "tier": "INSUFFICIENT"},
            self._insuf_recon(), self._ks(), 0,
        )
        for rec in recs:
            assert rec["auto_authorized"] is False


# ── TestAuditEntry ─────────────────────────────────────────────────────────────

class TestAuditEntry:
    def _entry(self, pilot_state=PAPER_ONLY, cls=REALITY_CONSISTENT):
        return _generate_pilot_audit_entry(
            pilot_state, cls,
            {"score": 40.0, "tier": "MARGINAL"},
            {"score": 50.0, "tier": "DEVELOPING"},
            {"engage": False, "reason": "none", "priority": "NONE", "trigger_count": 0},
            [],
        )

    def test_entry_id_format(self):
        e = self._entry()
        assert e["entry_id"].startswith("GMPD-")

    def test_auto_authorized_always_false(self):
        for state in (PAPER_ONLY, SHADOW_OBSERVATION, HUMAN_ARMED_MICRO, CONSTITUTION_LOCKDOWN):
            e = self._entry(pilot_state=state)
            assert e["auto_authorized"] is False

    def test_immutable_always_true(self):
        e = self._entry()
        assert e["immutable"] is True

    def test_entry_type_analysis(self):
        e = self._entry()
        assert e["entry_type"] == "ANALYSIS"

    def test_human_approval_required_paper_only_false(self):
        e = self._entry(pilot_state=PAPER_ONLY)
        assert e["human_approval_required"] is False

    def test_human_approval_required_non_paper_true(self):
        for state in (SHADOW_OBSERVATION, HUMAN_ARMED_MICRO, SINGLE_CONFIRM_EXECUTION,
                      MANUAL_KILL_SWITCH, CONSTITUTION_LOCKDOWN):
            e = self._entry(pilot_state=state)
            assert e["human_approval_required"] is True


# ── TestComputeStructure ───────────────────────────────────────────────────────

class TestComputeStructure:
    _REQUIRED_KEYS = {
        "scope_note", "total_trades", "pilot_ledger_depth", "pilot_state",
        "pilot_state_description", "pilot_classification", "pilot_survivability",
        "execution_readiness", "confirmation_chain_integrity", "reconciliation_metrics",
        "kill_switch_advisory", "recommendations", "pilot_opportunity",
        "pilot_hard_principles", "audit_entry",
    }

    def test_returns_dict(self):
        assert isinstance(compute_guarded_micro_pilot([]), dict)

    def test_required_keys_present(self):
        r = compute_guarded_micro_pilot(_trades(50))
        assert self._REQUIRED_KEYS.issubset(r.keys())

    def test_empty_trades_does_not_crash(self):
        r = compute_guarded_micro_pilot([])
        assert isinstance(r, dict)

    def test_none_ledger_does_not_crash(self):
        r = compute_guarded_micro_pilot(_trades(10), None)
        assert isinstance(r, dict)

    def test_empty_ledger_does_not_crash(self):
        r = compute_guarded_micro_pilot(_trades(10), [])
        assert isinstance(r, dict)

    def test_scope_note_research_only(self):
        r = compute_guarded_micro_pilot([])
        assert "research" in r.get("scope_note", "").lower() or "FTD-GMPD" in r.get("scope_note", "")

    def test_pilot_state_valid_value(self):
        valid = {PAPER_ONLY, SHADOW_OBSERVATION, HUMAN_ARMED_MICRO,
                 SINGLE_CONFIRM_EXECUTION, MANUAL_KILL_SWITCH, CONSTITUTION_LOCKDOWN}
        r = compute_guarded_micro_pilot(_trades(50))
        assert r["pilot_state"] in valid

    def test_classification_valid_value(self):
        valid = {REALITY_CONSISTENT, EXECUTION_DRIFT, SLIPPAGE_COLLAPSE,
                 LIQUIDITY_FAILURE, HUMAN_REVIEW_ESCALATION, PILOT_LOCKDOWN_RECOMMENDED}
        r = compute_guarded_micro_pilot(_trades(50))
        assert r["pilot_classification"] in valid

    def test_hard_principles_present(self):
        r = compute_guarded_micro_pilot([])
        assert isinstance(r.get("pilot_hard_principles"), dict)
        assert r["pilot_hard_principles"]["human_confirmation_required"] is True

    def test_audit_entry_present(self):
        r = compute_guarded_micro_pilot(_trades(50))
        ae = r.get("audit_entry", {})
        assert ae.get("auto_authorized") is False
        assert ae.get("immutable") is True


# ── TestProductionIsolation ────────────────────────────────────────────────────

class TestProductionIsolation:
    def test_no_import_from_main(self):
        import core.micro_pilot_doctrine as m
        src = Path(m.__file__).read_text()
        assert "from main" not in src
        assert "import main" not in src

    def test_fail_open_corrupted_trades(self):
        bad = [None, "string", 42, {"entry_ts": "bad"}]
        r = compute_guarded_micro_pilot(bad)
        assert isinstance(r, dict)

    def test_fail_open_corrupted_ledger(self):
        r = compute_guarded_micro_pilot(_trades(10), [None, 42, "bad"])
        assert isinstance(r, dict)

    def test_input_trades_not_mutated(self):
        original = _trades(20)
        copy     = [dict(t) for t in original]
        compute_guarded_micro_pilot(original, [])
        for a, b in zip(original, copy):
            assert a == b

    def test_scope_note_not_execution_authority(self):
        r = compute_guarded_micro_pilot(_trades(10))
        note = r.get("scope_note", "").upper()
        assert "NOT AN EXECUTION AUTHORITY" in note or "NEVER SELF-FIRE" in note or "RESEARCH" in note


# ── TestConstitutionalPrinciples ───────────────────────────────────────────────

class TestConstitutionalPrinciples:
    def test_sovereign_authority_false(self):
        assert PILOT_HARD_PRINCIPLES["sovereign_economic_authority"] is False

    def test_self_authorized_execution_false(self):
        assert PILOT_HARD_PRINCIPLES["self_authorized_execution"] is False

    def test_human_confirmation_required_true(self):
        assert PILOT_HARD_PRINCIPLES["human_confirmation_required"] is True

    def test_all_recommendations_auto_authorized_false(self):
        r = compute_guarded_micro_pilot(_trades(500))
        for rec in r.get("recommendations", []):
            assert rec["auto_authorized"] is False

    def test_audit_entry_auto_authorized_false(self):
        r = compute_guarded_micro_pilot(_trades(50))
        assert r["audit_entry"]["auto_authorized"] is False

    def test_pilot_opportunity_auto_authorized_false(self):
        r = compute_guarded_micro_pilot(_trades(200))
        assert r["pilot_opportunity"]["auto_authorized"] is False
        assert r["pilot_opportunity"]["human_confirmation_required"] is True

    def test_hard_principles_contains_no_autonomous_escalation(self):
        assert PILOT_HARD_PRINCIPLES["recursive_authority_escalation"] is False
        assert PILOT_HARD_PRINCIPLES["retry_execution_autonomous"] is False
        assert PILOT_HARD_PRINCIPLES["exposure_scaling_autonomous"] is False


# ── TestEdgeCases ──────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_single_trade(self):
        r = compute_guarded_micro_pilot([_trade()])
        assert isinstance(r, dict)
        assert r["total_trades"] == 1

    def test_very_large_trade_list(self):
        r = compute_guarded_micro_pilot(_trades(5000))
        assert r["total_trades"] == 5000
        assert r["execution_readiness"]["tier"] == "ADEQUATE"

    def test_ledger_entry_missing_type(self):
        ledger = [{"human_confirmed": True, "auto_authorized": False}]
        r = compute_guarded_micro_pilot(_trades(10), ledger)
        assert isinstance(r, dict)

    def test_zero_expected_values_in_reconciliation(self):
        ledger = [_exec_entry(expected_fill=0.0, expected_slippage=0.0,
                              expected_latency_ms=0.0, expected_fee=0.0, expected_net_pnl=0.0)]
        r = compute_guarded_micro_pilot(_trades(10), ledger)
        assert isinstance(r, dict)

    def test_pilot_ledger_depth_matches_input(self):
        ledger = [_analysis_entry()] * 7
        r = compute_guarded_micro_pilot(_trades(50), ledger)
        assert r["pilot_ledger_depth"] == 7

"""
FTD-028 — tests/test_deep_validation.py
Scientific Proof Engine — unit tests for all 13 deep validators.
"""
from __future__ import annotations
import pytest

from core.deep_validation.contradiction_engine    import ContradictionEngine
from core.deep_validation.data_integrity_checker  import DataIntegrityChecker
from core.deep_validation.decision_scorer         import DecisionScorer
from core.deep_validation.risk_validator          import RiskValidator
from core.deep_validation.tuning_validator        import TuningValidator
from core.deep_validation.evolution_validator     import EvolutionValidator
from core.deep_validation.capital_validator       import CapitalValidator
from core.deep_validation.audit_validator         import AuditValidator
from core.deep_validation.alert_validator         import AlertValidator
from core.deep_validation.performance_validator   import PerformanceValidator
from core.deep_validation.failure_simulator       import FailureSimulator
from core.deep_validation.system_consistency_checker import SystemConsistencyChecker
from core.deep_validation.meta_score_engine       import MetaScoreEngine


# ── PART 1: Contradiction Engine ──────────────────────────────────────────────

class TestContradictionEngine:
    def test_clean_state_passes(self):
        result = ContradictionEngine().run({
            "total_trades": 5, "total_signals": 5,
            "total_pnl": 100.0, "win_rate": 0.60,
            "risk_halted": False, "trades_active": True,
            "current_drawdown_pct": 0.05, "max_drawdown_pct": 0.15,
            "halted": False, "equity": 1000.0,
        })
        assert result["passed"] is True
        assert result["contradiction_count"] == 0

    def test_trades_without_signals(self):
        result = ContradictionEngine().run({
            "total_trades": 3, "total_signals": 0,
            "equity": 1000.0,
        })
        codes = [c["code"] for c in result["contradictions"]]
        assert "TRADES_WITHOUT_SIGNALS" in codes
        assert result["block_report"] is True

    def test_losing_with_high_win_rate_flagged(self):
        result = ContradictionEngine().run({
            "total_trades": 10, "total_signals": 10,
            "total_pnl": -500.0, "win_rate": 0.80,
            "equity": 1000.0,
        })
        codes = [c["code"] for c in result["contradictions"]]
        assert "LOSING_WITH_HIGH_WIN_RATE" in codes

    def test_trading_while_risk_halted(self):
        result = ContradictionEngine().run({
            "risk_halted": True, "trades_active": True,
            "equity": 1000.0,
        })
        codes = [c["code"] for c in result["contradictions"]]
        assert "TRADING_WHILE_RISK_HALTED" in codes
        assert result["block_report"] is True

    def test_dd_breach_without_halt(self):
        result = ContradictionEngine().run({
            "current_drawdown_pct": 0.20, "max_drawdown_pct": 0.15,
            "halted": False, "equity": 800.0,
        })
        codes = [c["code"] for c in result["contradictions"]]
        assert "DD_BREACH_WITHOUT_HALT" in codes

    def test_negative_equity_flagged(self):
        result = ContradictionEngine().run({"equity": -100.0})
        codes = [c["code"] for c in result["contradictions"]]
        assert "NEGATIVE_EQUITY" in codes


# ── PART 2: Data Integrity Checker ───────────────────────────────────────────

class TestDataIntegrityChecker:
    def _valid_state(self):
        return {
            "equity": 1000.0,
            "current_drawdown_pct": 0.05,
            "total_trades": 10,
            "win_rate": 0.60,
            "total_pnl": 50.0,
            "pipeline_stages": ["market_data", "signal", "risk", "execution"],
        }

    def test_valid_state_passes(self):
        result = DataIntegrityChecker().run(self._valid_state())
        assert result["passed"] is True

    def test_missing_field_detected(self):
        state = self._valid_state()
        del state["equity"]
        result = DataIntegrityChecker().run(state)
        codes = [i["code"] for i in result["issues"]]
        assert "MISSING_FIELD" in codes

    def test_out_of_bounds_win_rate(self):
        state = self._valid_state()
        state["win_rate"] = 1.5   # > 1.0
        result = DataIntegrityChecker().run(state)
        codes = [i["code"] for i in result["issues"]]
        assert "OUT_OF_BOUNDS" in codes

    def test_missing_pipeline_stage_detected(self):
        state = self._valid_state()
        state["pipeline_stages"] = ["market_data", "signal"]   # missing risk + execution
        result = DataIntegrityChecker().run(state)
        codes = [i["code"] for i in result["issues"]]
        assert "MISSING_PIPELINE_STAGE" in codes


# ── PART 3: Decision Scorer ───────────────────────────────────────────────────

class TestDecisionScorer:
    def test_empty_decisions_passes(self):
        result = DecisionScorer().run([])
        assert result["passed"] is True
        assert result["verdict"] == "NO_DATA"

    def test_correct_trade_scores_positive(self):
        result = DecisionScorer().run([
            {"action": "TRADE", "outcome": "PROFIT", "pnl": 100.0},
        ])
        assert result["score"] > 0
        assert result["correct"] == 1
        assert result["wrong"] == 0

    def test_wrong_trade_scores_negative(self):
        result = DecisionScorer().run([
            {"action": "TRADE", "outcome": "LOSS", "pnl": -50.0},
        ])
        assert result["score"] < 0
        assert result["wrong"] == 1

    def test_correct_avoidance_scores_positive(self):
        result = DecisionScorer().run([
            {"action": "AVOID", "outcome": "CRASH"},
        ])
        assert result["score"] > 0

    def test_mixed_decisions_score_range(self):
        decisions = [
            {"action": "TRADE",  "outcome": "PROFIT"},
            {"action": "TRADE",  "outcome": "LOSS"},
            {"action": "AVOID",  "outcome": "CRASH"},
            {"action": "AVOID",  "outcome": "MISS"},
        ]
        result = DecisionScorer().run(decisions)
        assert result["scored_count"] == 4
        assert -1.0 <= result["score"] <= 1.0


# ── PART 4: Risk Validator ────────────────────────────────────────────────────

class TestRiskValidator:
    def test_safe_state_passes(self):
        result = RiskValidator().run({
            "risk_of_ruin": 0.20,
            "exposure_pct": 0.50,
            "current_drawdown_pct": 0.05,
            "halted": False,
            "kill_switch_active": False,
            "trades_active": True,
        })
        assert result["passed"] is True

    def test_ror_out_of_range(self):
        result = RiskValidator().run({"risk_of_ruin": 1.5})
        codes = [e["code"] for e in result["errors"]]
        assert "ROR_OUT_OF_RANGE" in codes

    def test_over_exposure(self):
        result = RiskValidator().run({
            "risk_of_ruin": 0.10,
            "exposure_pct": 1.50,
        })
        codes = [e["code"] for e in result["errors"]]
        assert "OVER_EXPOSED" in codes

    def test_kill_switch_missing(self):
        result = RiskValidator().run({
            "current_drawdown_pct": 0.20,
            "halted": False,
            "kill_switch_active": False,
        })
        codes = [e["code"] for e in result["errors"]]
        assert "KILL_SWITCH_MISSING" in codes

    def test_kill_switch_bypassed(self):
        result = RiskValidator().run({
            "kill_switch_active": True,
            "trades_active": True,
        })
        codes = [e["code"] for e in result["errors"]]
        assert "KILL_SWITCH_BYPASSED" in codes


# ── PART 5: Tuning Validator ──────────────────────────────────────────────────

class TestTuningValidator:
    def test_empty_history_passes(self):
        result = TuningValidator().run([])
        assert result["passed"] is True
        assert result["verdict"] == "NO_DATA"

    def test_valid_improvement_passes(self):
        result = TuningValidator().run([{
            "label": "cycle_1",
            "before": {"score": 0.50},
            "after":  {"score": 0.55},
            "samples": 20,
            "rolled_back": False,
        }])
        assert result["passed"] is True

    def test_regression_without_rollback_flagged(self):
        result = TuningValidator().run([{
            "label": "cycle_bad",
            "before": {"score": 0.60},
            "after":  {"score": 0.45},
            "samples": 20,
            "rolled_back": False,
        }])
        codes = [i["code"] for i in result["issues"]]
        assert "REGRESSION_WITHOUT_ROLLBACK" in codes

    def test_insufficient_samples_flagged(self):
        result = TuningValidator().run([{
            "label": "small",
            "before": {"score": 0.50},
            "after":  {"score": 0.52},
            "samples": 3,
            "rolled_back": False,
        }])
        codes = [i["code"] for i in result["issues"]]
        assert "INSUFFICIENT_SAMPLES" in codes


# ── PART 6: Evolution Validator ───────────────────────────────────────────────

class TestEvolutionValidator:
    def test_healthy_evolution_passes(self):
        result = EvolutionValidator().run({
            "generation": 5,
            "champion_score": 0.65,
            "strategies": [{"name": "rsi_cross"}],
        })
        assert result["passed"] is True

    def test_challenger_beats_champion_flagged(self):
        result = EvolutionValidator().run({
            "generation": 2,
            "champion_score": 0.50,
            "challenger_score": 0.70,
            "strategies": [{"name": "rsi"}],
        })
        codes = [i["code"] for i in result["issues"]]
        assert "CHALLENGER_BEATS_CHAMPION" in codes

    def test_overfitting_detected(self):
        result = EvolutionValidator().run({
            "generation": 3,
            "champion_score": 0.70,
            "in_sample_score": 0.90,
            "out_sample_score": 0.50,
            "strategies": [{"name": "rsi"}],
        })
        codes = [i["code"] for i in result["issues"]]
        assert "OVERFITTING_DETECTED" in codes


# ── PART 7: Capital Validator ─────────────────────────────────────────────────

class TestCapitalValidator:
    def test_safe_capital_passes(self):
        result = CapitalValidator().run({
            "equity": 1000.0,
            "total_exposure": 800.0,
            "scale_factor": 1.0,
            "current_drawdown_pct": 0.02,
            "initial_capital": 1000.0,
        })
        assert result["passed"] is True

    def test_over_leveraged_detected(self):
        result = CapitalValidator().run({
            "equity": 1000.0,
            "total_exposure": 4000.0,
            "scale_factor": 1.0,
            "current_drawdown_pct": 0.01,
        })
        codes = [i["code"] for i in result["issues"]]
        assert "OVER_LEVERAGED" in codes

    def test_scaling_up_during_dd_detected(self):
        result = CapitalValidator().run({
            "equity": 900.0,
            "total_exposure": 500.0,
            "scale_factor": 1.20,
            "current_drawdown_pct": 0.10,
        })
        codes = [i["code"] for i in result["issues"]]
        assert "SCALING_UP_DURING_DD" in codes


# ── PART 8: Audit Validator ───────────────────────────────────────────────────

class TestAuditValidator:
    def test_complete_audit_passes(self):
        events = [
            {"type": "TRADE_OPEN",  "ts": 1000},
            {"type": "TRADE_CLOSE", "ts": 2000},
            {"type": "RISK_CHECK",  "ts": 1500},
        ]
        result = AuditValidator().run({
            "events": events,
            "total_trades": 1,
            "total_events": 3,
            "severity_breakdown": {},
        })
        assert result["passed"] is True

    def test_incomplete_audit_trail_detected(self):
        result = AuditValidator().run({
            "events": [{"type": "TRADE_OPEN", "ts": 1000}],
            "total_trades": 5,
            "total_events": 1,
            "severity_breakdown": {},
        })
        codes = [i["code"] for i in result["issues"]]
        assert "INCOMPLETE_AUDIT_TRAIL" in codes


# ── PART 9: Alert Validator ───────────────────────────────────────────────────

class TestAlertValidator:
    def test_clean_alerts_pass(self):
        result = AlertValidator().run({
            "alerts": [
                {"severity": "CRITICAL"},
                {"severity": "HIGH"},
                {"severity": "MEDIUM"},
            ],
            "false_alert_count": 0,
            "missed_alert_count": 0,
            "critical_events_detected": 1,
        })
        assert result["passed"] is True

    def test_high_false_alert_rate_flagged(self):
        result = AlertValidator().run({
            "alerts": [{"severity": "INFO"}] * 10,
            "false_alert_count": 8,
            "missed_alert_count": 0,
            "critical_events_detected": 0,
        })
        codes = [i["code"] for i in result["issues"]]
        assert "HIGH_FALSE_ALERT_RATE" in codes

    def test_missed_alerts_flagged(self):
        result = AlertValidator().run({
            "alerts": [],
            "false_alert_count": 0,
            "missed_alert_count": 3,
            "critical_events_detected": 0,
        })
        codes = [i["code"] for i in result["issues"]]
        assert "MISSED_ALERTS" in codes


# ── PART 10: Performance Validator ───────────────────────────────────────────

class TestPerformanceValidator:
    def test_on_target_performance_passes(self):
        result = PerformanceValidator().run(
            {"total_pnl": 100.0, "win_rate": 0.60, "total_trades": 10, "sharpe_ratio": 1.5},
            expected={"pnl": 110.0, "win_rate": 0.62},
        )
        assert result["passed"] is True

    def test_large_pnl_deviation_flagged(self):
        result = PerformanceValidator().run(
            {"total_pnl": 10.0, "win_rate": 0.60, "total_trades": 10},
            expected={"pnl": 100.0},
        )
        codes = [i["code"] for i in result["issues"]]
        assert "PNL_DEVIATION" in codes

    def test_low_sharpe_flagged(self):
        result = PerformanceValidator().run({
            "total_pnl": -500.0, "win_rate": 0.40,
            "total_trades": 20, "sharpe_ratio": -2.0,
        })
        codes = [i["code"] for i in result["issues"]]
        assert "SHARPE_BELOW_MINIMUM" in codes


# ── PART 11: Failure Simulator ────────────────────────────────────────────────

class TestFailureSimulator:
    def test_all_guards_active_passes(self):
        state = {
            "volatility_guard_active":    True,
            "rr_engine_active":           True,
            "drawdown_controller_active": True,
            "data_health_monitor_active": True,
            "safe_mode_engine_active":    True,
            "ws_stabilizer_active":       True,
            "error_registry_active":      True,
            "api_manager_active":         True,
            "self_healing_active":        True,
        }
        result = FailureSimulator().run(state)
        assert result["passed"] is True
        assert result["failed_count"] == 0

    def test_no_guards_fails(self):
        result = FailureSimulator().run({})
        assert result["passed"] is False
        assert result["failed_count"] > 0

    def test_scenario_names_present(self):
        result = FailureSimulator().run({})
        names = {s["scenario"] for s in result["scenarios"]}
        assert "EXTREME_VOLATILITY" in names
        assert "DATA_PIPELINE_FAILURE" in names
        assert "API_EXCHANGE_FAILURE" in names


# ── PART 12: System Consistency Checker ──────────────────────────────────────

class TestSystemConsistencyChecker:
    def test_consistent_modules_pass(self):
        result = SystemConsistencyChecker().run({
            "risk":     {"equity": 1000.0, "halted": False, "mode": "PAPER"},
            "capital":  {"equity": 1000.0, "halted": False, "mode": "PAPER"},
        })
        assert result["passed"] is True

    def test_equity_desync_detected(self):
        result = SystemConsistencyChecker().run({
            "risk":     {"equity": 1000.0},
            "capital":  {"equity": 500.0},   # big discrepancy
        })
        codes = [i["code"] for i in result["issues"]]
        assert "EQUITY_DESYNC" in codes

    def test_halt_desync_detected(self):
        result = SystemConsistencyChecker().run({
            "risk":  {"halted": True},
            "gate":  {"halted": False},
        })
        codes = [i["code"] for i in result["issues"]]
        assert "HALT_STATE_DESYNC" in codes


# ── PART 13: Meta Score Engine ────────────────────────────────────────────────

class TestMetaScoreEngine:
    def _all_pass(self):
        return {k: {"passed": True, "issue_count": 0} for k in [
            "contradiction", "data_integrity", "decision_quality", "risk",
            "tuning", "evolution", "capital", "audit", "alert",
            "performance", "failure_resilience", "consistency",
        ]}

    def test_all_pass_yields_high_score(self):
        result = MetaScoreEngine().run(self._all_pass())
        assert result["system_score"] >= 70
        assert result["verdict"] == "PASS"

    def test_score_range(self):
        result = MetaScoreEngine().run(self._all_pass())
        assert 0 <= result["system_score"] <= 100
        assert 0 <= result["risk_score"] <= 100
        assert 0 <= result["stability_score"] <= 100
        assert 0 <= result["confidence_score"] <= 100

    def test_critical_failures_reduce_score(self):
        results = self._all_pass()
        results["contradiction"] = {
            "passed": False,
            "issue_count": 3,
            "contradictions": [{"message": "trades without signals"}],
        }
        results["risk"] = {
            "passed": False,
            "issue_count": 2,
            "errors": [{"message": "over exposed"}],
        }
        result = MetaScoreEngine().run(results)
        # score should drop from 100
        assert result["system_score"] < 100

    def test_verdict_fail_below_threshold(self):
        results = {k: {"passed": False, "issue_count": 5} for k in [
            "contradiction", "data_integrity", "decision_quality", "risk",
            "tuning", "evolution", "capital", "audit", "alert",
            "performance", "failure_resilience", "consistency",
        ]}
        result = MetaScoreEngine().run(results)
        assert result["verdict"] == "FAIL"

    def test_critical_errors_list_populated(self):
        results = self._all_pass()
        results["risk"] = {
            "passed": False,
            "issue_count": 1,
            "errors": [{"message": "over leveraged"}],
        }
        result = MetaScoreEngine().run(results)
        assert any("over leveraged" in e for e in result["critical_errors"])

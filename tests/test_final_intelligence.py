"""
Tests for FTD-034 — Final Intelligence Engine.

Coverage:
  ✔ signals > 0 & trades == 0 → primary_issue = NO_EXECUTION
  ✔ wrong root cause (SYSTEM_IN_LOSS with 0 trades) corrected by consistency engine
  ✔ AI decision = BLOCKED when signals blocked
  ✔ gate trace injected into alerts_enriched
  ✔ consistency enforced (no mismatch)
  ✔ trade_activator.no_execution_override lowers score_min
  ✔ learning_memory exploration_boost activates when trades == 0
"""
import pytest

from core.reporting.final_intelligence_engine import apply as final_apply
from core.reporting.consistency_engine import enforce
from core.reporting.intelligence_layer import explain_decision


# ── Helpers ───────────────────────────────────────────────────────────────────

def _base_data(**overrides) -> dict:
    base = {
        "trade_flow": {
            "total_signals": 15,
            "total_trades":   0,
            "top_rejection_reasons": {"LOW_SCORE": 10},
        },
        "thresholds": {"score_min": 0.58, "tier": "NORMAL"},
        "gate":       {"can_trade": True, "reason": "BOOT_GRACE"},
        "gate_trace": {
            "dominant_block": "PRE_TRADE",
            "dominant_reason": "LOW_SCORE",
            "top_3_failures": [
                {"gate_reason": "PRE_TRADE:LOW_SCORE", "count": 10, "pct": 66.7}
            ],
        },
        "_truth": {},
        "_intel": {},
    }
    base.update(overrides)
    return base


# ── Part 1: Final Intelligence Engine ─────────────────────────────────────────

class TestFinalIntelligenceEngine:

    def test_no_execution_sets_primary_issue(self):
        data = _base_data()
        result = final_apply(data)
        assert result["primary_issue"] == "NO_EXECUTION"

    def test_no_execution_sets_severity_critical(self):
        data = _base_data()
        result = final_apply(data)
        assert result["severity"] == "CRITICAL"

    def test_no_execution_sets_primary_reason(self):
        data = _base_data()
        result = final_apply(data)
        assert "blocked" in result["primary_reason"].lower()

    def test_no_trades_no_signals_does_not_override(self):
        data = _base_data()
        data["trade_flow"]["total_signals"] = 0
        data["trade_flow"]["total_trades"]  = 0
        result = final_apply(data)
        assert result.get("primary_issue") != "NO_EXECUTION"

    def test_trades_executed_does_not_override(self):
        data = _base_data()
        data["trade_flow"]["total_trades"] = 5
        result = final_apply(data)
        assert result.get("severity") != "CRITICAL"

    def test_gate_trace_injected_into_alerts_enriched(self):
        data = _base_data()
        result = final_apply(data)
        ae = result["alerts_enriched"]
        assert "dominant_block" in ae
        assert len(ae["dominant_block"]) > 0

    def test_gate_trace_falls_back_to_gate_dict(self):
        data = _base_data()
        data.pop("gate_trace", None)
        data["gate"] = {"can_trade": False, "reason": "DRAWDOWN_EXCEEDED"}
        result = final_apply(data)
        assert result["alerts_enriched"]["reason"] == "DRAWDOWN_EXCEEDED"

    def test_priority_no_execution_beats_other_issues(self):
        data = _base_data()
        data["primary_issue"] = "STRATEGY_WEAKNESS"
        result = final_apply(data)
        assert result["primary_issue"] == "NO_EXECUTION"


# ── Part 2: Consistency Engine ────────────────────────────────────────────────

class TestConsistencyEngine:

    def test_system_in_loss_corrected_when_no_trades(self):
        data = {
            "trade_flow":    {"total_trades": 0, "total_signals": 10},
            "primary_issue": "SYSTEM_IN_LOSS",
        }
        result = enforce(data)
        assert result["primary_issue"] == "NO_EXECUTION"

    def test_system_in_loss_string_variant_corrected(self):
        data = {
            "trade_flow":    {"total_trades": 0, "total_signals": 10},
            "primary_issue": "SYSTEM IN LOSS",
        }
        result = enforce(data)
        assert result["primary_issue"] == "NO_EXECUTION"

    def test_primary_reason_populated(self):
        data = {
            "trade_flow":    {"total_trades": 0, "total_signals": 10},
            "primary_issue": "NO_EXECUTION",
        }
        result = enforce(data)
        assert result["primary_reason"]

    def test_system_in_loss_preserved_when_trades_exist(self):
        data = {
            "trade_flow":    {"total_trades": 5, "total_signals": 20},
            "primary_issue": "SYSTEM_IN_LOSS",
        }
        result = enforce(data)
        assert result["primary_issue"] == "SYSTEM_IN_LOSS"


# ── Part 3: AI Decision Correction ───────────────────────────────────────────

class TestAIDecisionCorrection:

    def test_blocked_when_signals_no_trades(self):
        data = _base_data()
        dec = explain_decision(data)
        assert dec["decision"] == "BLOCKED"

    def test_blocked_reason_populated(self):
        data = _base_data()
        dec = explain_decision(data)
        assert "NO_EXECUTION" in dec["decision_reason"]

    def test_monitor_when_trades_present(self):
        data = _base_data()
        data["trade_flow"]["total_trades"] = 5
        dec = explain_decision(data)
        assert dec["decision"] == "MONITOR"

    def test_monitor_when_no_signals(self):
        data = _base_data()
        data["trade_flow"]["total_signals"] = 0
        dec = explain_decision(data)
        assert dec["decision"] == "MONITOR"


# ── Part 4: Trade Activator Override ─────────────────────────────────────────

class TestTradeActivatorOverride:

    def setup_method(self):
        from core.trade_activator import TradeActivator
        self.activator = TradeActivator()

    def test_score_reduced_on_no_execution(self):
        reduced = self.activator.no_execution_override(
            score_min=0.58, signals=15, trades=0
        )
        assert reduced == pytest.approx(0.48)

    def test_score_floor_respected(self):
        reduced = self.activator.no_execution_override(
            score_min=0.42, signals=10, trades=0
        )
        assert reduced == pytest.approx(0.40)

    def test_no_override_when_trades_present(self):
        score = self.activator.no_execution_override(
            score_min=0.58, signals=10, trades=3
        )
        assert score == pytest.approx(0.58)

    def test_no_override_when_no_signals(self):
        score = self.activator.no_execution_override(
            score_min=0.58, signals=0, trades=0
        )
        assert score == pytest.approx(0.58)


# ── Part 5: Learning Memory Exploration Boost ─────────────────────────────────

class TestLearningExplorationBoost:

    def setup_method(self):
        from core.learning_memory.learning_memory_orchestrator import (
            LearningMemoryOrchestrator,
        )
        self.orch = LearningMemoryOrchestrator()

    def test_boost_active_when_trades_zero(self):
        self.orch.set_exploration_boost(trades_total=0)
        assert self.orch.is_exploration_boost() is True

    def test_boost_inactive_when_trades_present(self):
        self.orch.set_exploration_boost(trades_total=5)
        assert self.orch.is_exploration_boost() is False

    def test_boost_reflected_in_summary(self):
        self.orch.set_exploration_boost(trades_total=0)
        s = self.orch.summary()
        assert s["exploration_boost"] is True

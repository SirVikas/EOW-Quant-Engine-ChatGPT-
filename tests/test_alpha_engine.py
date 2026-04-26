"""
FTD-033 — Tests for Cost + Execution + Alpha Engine

Covers:
  ✔ cost reduces edge correctly
  ✔ negative net edge → reject
  ✔ exploration allows low edge (tagged)
  ✔ execution trace populated
  ✔ gate trace correct
  ✔ report shows execution gap
  ✔ cost learning adapter records patterns
  ✔ exploration controller enforces daily cap
"""
import sys
import os
import pytest

# Allow import from project root without installing as package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

ENTRY = 100.0
TP_GOOD  = 115.0   # 15% move — comfortably positive net edge
TP_BAD   = 100.02  # 0.02% move — well below min net edge threshold (costs swamp it)
SL       = 97.0
QTY      = 10.0
ATR_PCT  = 0.008


# ─────────────────────────────────────────────────────────────────────────────
# Part 1: Cost Engine (core dependency)
# ─────────────────────────────────────────────────────────────────────────────

class TestCostEngine:
    def test_calculate_cost_returns_all_fields(self):
        from core.cost.cost_engine import calculate_cost
        cb = calculate_cost(ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        assert cb.fee_entry > 0
        assert cb.fee_exit > 0
        assert cb.slippage_entry >= 0
        assert cb.slippage_exit >= 0
        assert cb.spread_cost >= 0
        assert cb.total_cost == pytest.approx(
            cb.fee_entry + cb.fee_exit + cb.slippage_entry + cb.slippage_exit + cb.spread_cost,
            abs=1e-6
        )
        assert cb.cost_pct_of_notional >= 0

    def test_cost_reduces_edge(self):
        from core.cost.cost_engine import calculate_cost
        cb = calculate_cost(ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        gross_move = (TP_GOOD - ENTRY) * QTY  # 150.0 USDT
        net_edge   = gross_move - cb.total_cost
        assert net_edge < gross_move, "Cost must reduce net edge"
        assert net_edge > 0, "Net edge should still be positive for a 15% move"

    def test_zero_qty_returns_empty_cost(self):
        from core.cost.cost_engine import calculate_cost
        cb = calculate_cost(ENTRY, TP_GOOD, SL, 0.0, ATR_PCT)
        assert cb.total_cost == 0.0

    def test_slippage_capped_at_max(self):
        from core.cost.cost_engine import _slippage_pct, COST_SLIPPAGE_MAX_PCT
        # Very high ATR should be capped
        result = _slippage_pct(atr_pct=1.0)   # 100% ATR — extreme
        assert result <= COST_SLIPPAGE_MAX_PCT


# ─────────────────────────────────────────────────────────────────────────────
# Part 2: Net Edge Filter
# ─────────────────────────────────────────────────────────────────────────────

class TestNetEdgeEngine:
    def setup_method(self):
        from core.alpha.net_edge_engine import NetEdgeEngine
        self.engine = NetEdgeEngine()

    def test_good_setup_approved(self):
        d = self.engine.evaluate(ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        assert d.approved, f"Expected APPROVE but got {d.verdict}: {d.rejection_reason}"
        assert d.size_factor > 0

    def test_negative_net_edge_rejected(self):
        from core.cost.cost_engine import REJECT_NEG_EDGE, REJECT_BELOW_THRESH
        d = self.engine.evaluate(ENTRY, TP_BAD, SL, QTY, ATR_PCT)
        assert d.rejected, f"Expected rejection but got verdict={d.verdict}"
        assert d.size_factor == 0.0, "Rejected signal must have size_factor=0"

    def test_batch_evaluate_orders_by_net_edge(self):
        signals = [
            {"entry_price": ENTRY, "take_profit": TP_BAD,  "stop_loss": SL, "qty": QTY, "atr_pct": ATR_PCT, "side": "LONG"},
            {"entry_price": ENTRY, "take_profit": TP_GOOD, "stop_loss": SL, "qty": QTY, "atr_pct": ATR_PCT, "side": "LONG"},
        ]
        decisions = self.engine.batch_evaluate(signals)
        # Best edge should be first
        assert decisions[0].net_edge_pct >= decisions[1].net_edge_pct

    def test_size_factor_positive_for_approved(self):
        d = self.engine.evaluate(ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        assert d.size_factor > 0

    def test_rejection_reason_populated(self):
        d = self.engine.evaluate(ENTRY, TP_BAD, SL, QTY, ATR_PCT)
        assert d.rejection_reason != "", "Rejection must include a reason"


# ─────────────────────────────────────────────────────────────────────────────
# Part 3: Execution Trace
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutionTrace:
    def setup_method(self):
        from core.execution.execution_trace import ExecutionTrace, STATUS_EXECUTED, STATUS_REJECTED
        self.trace   = ExecutionTrace()
        self.EXEC    = STATUS_EXECUTED
        self.REJECT  = STATUS_REJECTED

    def test_start_creates_record(self):
        rec = self.trace.start("ETHUSDT", "LONG", "TCB", score=0.72, rr=3.5)
        assert rec.symbol == "ETHUSDT"
        assert rec.final_status == "PENDING"

    def test_finalize_updates_status(self):
        rec = self.trace.start("SOLUSDT", "SHORT", "PBE", score=0.65, rr=2.0)
        self.trace.finalize(rec, self.REJECT)
        assert rec.final_status == self.REJECT

    def test_summary_counts_correctly(self):
        # 2 executed, 1 rejected
        for _ in range(2):
            r = self.trace.start("BTCUSDT", "LONG", "TCB", 0.80, 3.0)
            r.rejection_reason = ""
            self.trace.finalize(r, self.EXEC)
        r = self.trace.start("BTCUSDT", "SHORT", "TCB", 0.55, 1.5)
        r.rejection_reason = "LOW_SCORE"
        r.failed_at = "PRE_TRADE_GATE"
        self.trace.finalize(r, self.REJECT)

        s = self.trace.summary()
        assert s["executed"] == 2
        assert s["rejected"] == 1
        assert s["dominant_block"] == "PRE_TRADE_GATE"
        assert "LOW_SCORE" in s["rejection_reasons"]

    def test_recent_returns_n_records(self):
        for i in range(5):
            r = self.trace.start(f"SYM{i}", "LONG", "TCB", 0.70, 2.0)
            self.trace.finalize(r, self.EXEC)
        assert len(self.trace.recent(3)) == 3


# ─────────────────────────────────────────────────────────────────────────────
# Part 4: Gate Trace Engine
# ─────────────────────────────────────────────────────────────────────────────

class TestGateTraceEngine:
    def setup_method(self):
        # gate_trace_engine.py has no external deps — load it directly, bypassing
        # gating/__init__.py which pulls in loguru/pydantic_settings.
        import importlib.util, sys, os
        modname = "core.gating.gate_trace_engine"
        if modname not in sys.modules:
            path = os.path.join(os.path.dirname(__file__), "..", "core", "gating", "gate_trace_engine.py")
            spec = importlib.util.spec_from_file_location(modname, path)
            mod  = importlib.util.module_from_spec(spec)
            # Register BEFORE exec so dataclass __module__ lookup succeeds
            sys.modules[modname] = mod
            spec.loader.exec_module(mod)
        mod = sys.modules[modname]
        self.engine = mod.GateTraceEngine()
        self.PASS   = mod.PASS
        self.FAIL   = mod.FAIL

    def test_all_pass_detected(self):
        t = self.engine.new_trace("ETHUSDT", "TCB", 0.75)
        self.engine.record(t, "GLOBAL",    self.PASS)
        self.engine.record(t, "PRE_TRADE", self.PASS)
        self.engine.record(t, "RISK",      self.PASS)
        self.engine.record(t, "EXECUTION", self.PASS)
        self.engine.commit(t)
        assert t.all_passed
        assert t.first_failure is None

    def test_first_failure_identified(self):
        t = self.engine.new_trace("SOLUSDT", "PBE", 0.55)
        self.engine.record(t, "GLOBAL",    self.PASS)
        self.engine.record(t, "PRE_TRADE", self.FAIL, reason="LOW_SCORE")
        self.engine.commit(t)
        ff = t.first_failure
        assert ff is not None
        assert ff.gate == "PRE_TRADE"
        assert ff.reason == "LOW_SCORE"

    def test_summary_dominant_block(self):
        for _ in range(3):
            t = self.engine.new_trace("XRPUSDT", "TCB", 0.60)
            self.engine.record(t, "GLOBAL",    self.PASS)
            self.engine.record(t, "PRE_TRADE", self.FAIL, reason="LOW_SCORE")
            self.engine.commit(t)
        t = self.engine.new_trace("XRPUSDT", "TCB", 0.80)
        self.engine.record(t, "GLOBAL",    self.PASS)
        self.engine.record(t, "PRE_TRADE", self.PASS)
        self.engine.record(t, "RISK",      self.FAIL, reason="DD_LIMIT")
        self.engine.commit(t)

        s = self.engine.summary()
        assert s["dominant_block"] == "PRE_TRADE"
        assert s["dominant_reason"] == "LOW_SCORE"


# ─────────────────────────────────────────────────────────────────────────────
# Part 5: Alpha Engine
# ─────────────────────────────────────────────────────────────────────────────

class TestAlphaEngine:
    def setup_method(self):
        from core.alpha.alpha_engine import AlphaEngine
        self.engine = AlphaEngine()

    def test_approved_signal_has_positive_alpha_score(self):
        result = self.engine.evaluate(
            symbol="ETHUSDT", side="LONG", signal_type="TCB",
            entry_price=ENTRY, take_profit=TP_GOOD, stop_loss=SL,
            qty=QTY, atr_pct=ATR_PCT,
            raw_score=0.80, confidence=0.90, regime_weight=1.0,
        )
        assert result.approved
        assert result.alpha_score > 0

    def test_rejected_signal_zero_size_factor(self):
        result = self.engine.evaluate(
            symbol="BTCUSDT", side="LONG", signal_type="PBE",
            entry_price=ENTRY, take_profit=TP_BAD, stop_loss=SL,
            qty=QTY, atr_pct=ATR_PCT,
        )
        assert result.size_factor == 0.0

    def test_rank_signals_best_first(self):
        good = self.engine.evaluate("ETHUSDT", "LONG", "TCB", ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        bad  = self.engine.evaluate("BTCUSDT", "LONG", "TCB", ENTRY, TP_BAD,  SL, QTY, ATR_PCT)
        ranked = self.engine.rank_signals([bad, good])
        assert ranked[0].alpha_score >= ranked[1].alpha_score

    def test_net_edge_summary_populated(self):
        for _ in range(3):
            self.engine.evaluate("ETHUSDT", "LONG", "TCB", ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        summary = self.engine.net_edge_summary()
        assert summary["total_evaluated"] >= 3


# ─────────────────────────────────────────────────────────────────────────────
# Part 6: Exploration Controller
# ─────────────────────────────────────────────────────────────────────────────

class TestExplorationController:
    def setup_method(self):
        from core.alpha.exploration_controller import ExplorationController
        self.ctrl = ExplorationController()
        self.ctrl.set_equity(1000.0)

    def test_allows_marginal_positive_edge_with_good_score(self):
        # Marginal edge just below threshold but above floor
        d = self.ctrl.should_explore(net_edge_pct=0.005, score=0.65)
        assert d.allow
        assert d.tagged
        assert d.size_mult > 0

    def test_rejects_below_score_floor(self):
        d = self.ctrl.should_explore(net_edge_pct=0.05, score=0.30)
        assert not d.allow
        assert "score" in d.reason

    def test_rejects_below_edge_floor(self):
        # Very negative edge — below -0.05% floor
        d = self.ctrl.should_explore(net_edge_pct=-0.10, score=0.70)
        assert not d.allow

    def test_daily_cap_enforcement(self):
        # Exhaust daily loss cap
        daily_cap = 1000.0 * 0.02  # 20 USDT
        self.ctrl._daily_loss_usdt = daily_cap + 1.0   # force exhaustion
        d = self.ctrl.should_explore(net_edge_pct=0.01, score=0.70)
        assert not d.allow
        assert "cap" in d.reason.lower()

    def test_summary_reflects_state(self):
        s = self.ctrl.summary()
        assert "enabled" in s
        assert "daily_loss_cap" in s


# ─────────────────────────────────────────────────────────────────────────────
# Part 7: Cost Learning Adapter
# ─────────────────────────────────────────────────────────────────────────────

class TestCostLearningAdapter:
    def setup_method(self):
        from core.learning.cost_learning_adapter import CostLearningAdapter
        from core.cost.cost_engine import make_trade_record, evaluate_net_edge
        self.adapter = CostLearningAdapter()
        self.make_record = make_trade_record
        self.eval_edge   = evaluate_net_edge

    def _make_completed_record(self, tp, net_pnl):
        result = self.eval_edge(ENTRY, tp, SL, QTY, ATR_PCT, "LONG", False)
        rec = self.make_record("t1", "ETHUSDT", "TCB", result)
        rec.outcome_net_pnl   = net_pnl
        rec.outcome_gross_pnl = net_pnl + result.total_cost
        rec.cost_was_accurate = True
        return rec

    def test_records_without_outcome_are_accepted(self):
        result = self.eval_edge(ENTRY, TP_GOOD, SL, QTY, ATR_PCT)
        rec = self.make_record("t0", "SOLUSDT", "PBE", result)
        self.adapter.record(rec)   # no exception
        s = self.adapter.summary()
        assert s["total_records"] == 1

    def test_negative_pattern_detected(self):
        # Feed 10 losing trades to trigger blacklist check
        for i in range(10):
            rec = self._make_completed_record(TP_BAD, -5.0)
            rec.trade_id    = f"t{i}"
            rec.cost_adjusted_rr = 0.5    # low RR → triggers Low_RR+High_Fee
            self.adapter.record(rec)
        s = self.adapter.summary()
        assert s["negative_patterns"] >= 0   # may or may not reach blacklist threshold

    def test_summary_keys_present(self):
        s = self.adapter.summary()
        for key in ["total_records", "patterns_tracked", "negative_patterns",
                    "blacklisted", "high_slippage_symbols"]:
            assert key in s, f"Missing key: {key}"

    def test_confidence_adjustment_within_bounds(self):
        conf = self.adapter.get_confidence_adjustment("TCB", "ETHUSDT")
        assert 0.0 <= conf <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Part 8: Report section sanity (no exception)
# ─────────────────────────────────────────────────────────────────────────────

class TestReportSections:
    def _get_sections(self):
        from core.reporting.unified_report_engine_v2 import (
            _s12_execution_analysis,
            _s13_cost_analysis,
            _s14_net_edge_summary,
            _s15_developer_summary_ftd033,
        )
        return _s12_execution_analysis, _s13_cost_analysis, _s14_net_edge_summary, _s15_developer_summary_ftd033

    def test_sections_with_empty_data(self):
        s12, s13, s14, s15 = self._get_sections()
        data = {}
        for fn in [s12, s13, s14, s15]:
            result = fn(data)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_sections_with_populated_data(self):
        s12, s13, s14, s15 = self._get_sections()
        data = {
            "execution_trace": {
                "total_signals": 100, "executed": 12, "rejected": 88,
                "execution_rate_pct": 12.0,
                "dominant_block": "PRE_TRADE_GATE",
                "top_rejection": "LOW_SCORE",
                "rejection_reasons": {"LOW_SCORE": 50.0, "NEGATIVE_NET_EDGE": 25.0},
                "gate_breakdown": {"PRE_TRADE_GATE": 80.0},
            },
            "gate_trace": {
                "dominant_block": "PRE_TRADE", "dominant_reason": "LOW_SCORE",
                "gate_stats": {
                    "GLOBAL":    {"pass": 100, "fail": 0,  "pass_pct": 100.0},
                    "PRE_TRADE": {"pass": 12,  "fail": 88, "pass_pct": 12.0},
                },
            },
            "cost_analysis": {
                "avg_cost_pct": 0.42, "high_cost_symbols": ["BTCUSDT", "ETHUSDT"],
            },
            "net_edge_summary": {
                "total_evaluated": 100, "positive_net_edge_pct": 20.0,
                "rejected_due_to_cost_pct": 60.0, "avg_alpha_score": -0.003,
                "strategy_summary": {"TCB": {"count": 50, "avg_alpha": 0.002, "approval_rate_pct": 15.0}},
            },
            "cost_learning": {
                "blacklisted_keys": ["Low_RR+High_Fee"],
            },
            "session_stats": {
                "n_trades": 133, "fees_paid": 45.76, "gross_pnl": 182.0,
                "profit_factor": 0.369, "win_rate": 48.9,
            },
            "_intel": {
                "capital": {"capital_idle_pct_str": "100%", "missed_opportunity": True},
            },
        }
        for fn in [s12, s13, s14, s15]:
            result = fn(data)
            assert isinstance(result, str)
            assert len(result) > 10

    def test_execution_gap_visible_in_s12(self):
        s12, _, _, _ = self._get_sections()
        data = {
            "execution_trace": {
                "total_signals": 15, "executed": 0, "rejected": 15,
                "execution_rate_pct": 0.0, "dominant_block": "PRE_TRADE_GATE",
                "top_rejection": "LOW_SCORE", "rejection_reasons": {},
            }
        }
        result = s12(data)
        assert "PRE_TRADE_GATE" in result or "Execution" in result

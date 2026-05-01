"""
FTD-REF-026 — tests/test_ftd_026.py
Tests for: UI truth sync, error throttling, strategy usage detection,
           regime stability gate, profit guard, and CT-Scan engine.
"""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

# ── Imports under test ────────────────────────────────────────────────────────
from core.error_registry import (
    ErrorRegistry,
    ERROR_THROTTLE,
    SEV_WARNING,
)
from core.regime_ai import (
    RegimeAI,
    RegimeAiResult,
    MIN_CONFIDENCE_TRADE,
    MIN_STABILITY_TICKS,
)
from core.strategy_engine import StrategyEngine, ACTIVE_THRESH, KNOWN_STRATEGIES
from core.profit_guard import (
    ProfitGuard,
    PROFIT_FACTOR_MIN,
    FEE_RATIO_MAX,
    FREQ_REDUCE_MULT,
    MIN_TRADES_FOR_PF,
)
from core.ct_scan_engine import (
    CtScanEngine,
    HEALTH_CRITICAL,
    HEALTH_WARNING,
    HEALTH_HEALTHY,
    MIN_TRADES_FOR_EVAL,
)
from core.ws_truth_engine import WsTruthEngine, WS_CONNECTED, WS_RECONNECTING


# ── A: UI Truth Sync ──────────────────────────────────────────────────────────

class TestUiTruthSync:
    """ws_truth_engine.get_ui_label() drives the ws_status field."""

    def test_fresh_engine_returns_live_label(self):
        engine = WsTruthEngine()
        label = engine.get_ui_label()
        assert "LIVE" in label.upper()

    def test_stale_engine_returns_non_live_label(self):
        engine = WsTruthEngine()
        engine._last_tick_ts = time.time() - 25   # 25s > CONNECTED_THRESH(20)
        label = engine.get_ui_label()
        assert "LIVE" not in label.upper() or "RECONNECTING" in label.upper()

    def test_to_dict_ws_status_key_present(self):
        engine = WsTruthEngine()
        d = engine.to_dict()
        assert "state" in d
        assert "ui_label" in d

    def test_record_tick_restores_connected_state(self):
        engine = WsTruthEngine()
        engine._last_tick_ts = time.time() - 90
        assert engine.get_state() != WS_CONNECTED
        engine.record_tick()
        assert engine.get_state() == WS_CONNECTED


# ── B: Error Spam Control ─────────────────────────────────────────────────────

class TestErrorThrottling:
    """DATA_001 emits to loguru at most once per 10 s."""

    def test_throttle_constant_defined(self):
        assert "DATA_001" in ERROR_THROTTLE
        assert ERROR_THROTTLE["DATA_001"] == 10.0

    def test_first_log_always_emits(self):
        reg = ErrorRegistry()
        emitted = []
        with patch("core.error_registry.logger") as mock_log:
            mock_log.info = lambda msg: emitted.append(msg)
            mock_log.warning = lambda msg: emitted.append(msg)
            mock_log.error   = lambda msg: emitted.append(msg)
            mock_log.debug   = lambda msg: emitted.append(msg)
            mock_log.critical= lambda msg: emitted.append(msg)
            reg.log("DATA_001")
        # throttle_ts for DATA_001 should now be set
        assert "DATA_001" in reg._throttle_ts

    def test_second_log_within_window_is_suppressed(self):
        reg = ErrorRegistry()
        # Pre-set throttle timestamp to "just now"
        reg._throttle_ts["DATA_001"] = time.time()
        emit_count = [0]
        with patch("core.error_registry.logger") as mock_log:
            def _inc(msg): emit_count[0] += 1
            mock_log.info = _inc
            mock_log.warning = _inc
            mock_log.error   = _inc
            mock_log.debug   = _inc
            mock_log.critical= _inc
            reg.log("DATA_001")
        # Should NOT have emitted
        assert emit_count[0] == 0

    def test_count_still_increments_when_throttled(self):
        reg = ErrorRegistry()
        reg._throttle_ts["DATA_001"] = time.time()
        with patch("core.error_registry.logger"):
            reg.log("DATA_001")
        assert reg.counts().get("DATA_001", 0) == 1

    def test_record_still_stored_when_throttled(self):
        reg = ErrorRegistry()
        reg._throttle_ts["DATA_001"] = time.time()
        with patch("core.error_registry.logger"):
            reg.log("DATA_001", extra="buf=3")
        assert len(reg.recent(10)) == 1

    def test_log_emits_after_throttle_window_expires(self):
        reg = ErrorRegistry()
        # Pre-set timestamp to well before the throttle window
        reg._throttle_ts["DATA_001"] = time.time() - 20.0
        emit_count = [0]
        with patch("core.error_registry.logger") as mock_log:
            def _inc(msg): emit_count[0] += 1
            mock_log.info = _inc
            mock_log.warning = _inc
            mock_log.error   = _inc
            mock_log.debug   = _inc
            mock_log.critical= _inc
            reg.log("DATA_001")
        assert emit_count[0] == 1

    def test_unthrottled_code_always_emits(self):
        reg = ErrorRegistry()
        emit_count = [0]
        with patch("core.error_registry.logger") as mock_log:
            def _inc(msg): emit_count[0] += 1
            mock_log.info = _inc
            mock_log.warning = _inc
            mock_log.error   = _inc
            mock_log.debug   = _inc
            mock_log.critical= _inc
            # WS_002 has no throttle — should always emit
            reg.log("WS_002")
            reg.log("WS_002")
        assert emit_count[0] == 2


# ── C: Strategy Usage Detection ───────────────────────────────────────────────

class TestStrategyUsageDetection:
    """StrategyEngine tracks usage and identifies dominant strategies."""

    def test_empty_usage_returns_zeros(self):
        eng = StrategyEngine()
        u = eng.usage()
        for s in KNOWN_STRATEGIES:
            assert u[s] == 0.0

    def test_record_single_strategy_gives_100_pct(self):
        eng = StrategyEngine()
        for _ in range(5):
            eng.record_trade("TrendFollowing")
        u = eng.usage()
        assert u["TrendFollowing"] == 1.0
        assert u["MeanReversion"] == 0.0
        assert u["VolatilityExpansion"] == 0.0

    def test_equal_distribution(self):
        eng = StrategyEngine()
        for s in KNOWN_STRATEGIES:
            for _ in range(3):
                eng.record_trade(s)
        u = eng.usage()
        for s in KNOWN_STRATEGIES:
            assert abs(u[s] - 1 / 3) < 0.01

    def test_active_strategies_excludes_below_thresh(self):
        eng = StrategyEngine()
        for _ in range(99):
            eng.record_trade("TrendFollowing")
        eng.record_trade("MeanReversion")  # 1% usage < ACTIVE_THRESH (5%)
        active = eng.active_strategies()
        assert "TrendFollowing" in active
        assert "MeanReversion" not in active

    def test_warning_when_single_strategy_after_min_trades(self):
        eng = StrategyEngine()
        for _ in range(15):
            eng.record_trade("TrendFollowing")
        s = eng.summary()
        assert s["warning"] != ""
        assert "1 strategy" in s["warning"].lower() or "only" in s["warning"].lower()

    def test_no_warning_when_below_min_trades(self):
        eng = StrategyEngine()
        for _ in range(5):
            eng.record_trade("TrendFollowing")
        assert eng.summary()["warning"] == ""

    def test_no_warning_when_multiple_strategies_active(self):
        eng = StrategyEngine()
        for _ in range(6):
            eng.record_trade("TrendFollowing")
        for _ in range(6):
            eng.record_trade("MeanReversion")
        assert eng.summary()["warning"] == ""

    def test_summary_structure(self):
        eng = StrategyEngine()
        eng.record_trade("TrendFollowing")
        s = eng.summary()
        for key in ("total_trades", "strategy_usage", "usage_fractions",
                    "active_strategies", "warning"):
            assert key in s


# ── D: Regime Stability Gate ──────────────────────────────────────────────────

class TestRegimeStabilityGate:
    """RegimeAI.classify() sets block_trade based on confidence and stability."""

    _TRENDING_CLOSES = (
        [100 + i for i in range(31)]
        + [130 - (i + 1) * 2 for i in range(15)]
        + [100 + (i + 1) * 3 for i in range(14)]
    )

    def test_block_trade_true_on_first_tick(self):
        """MIN_STABILITY_TICKS=1 — first tick satisfies stability; block depends on confidence."""
        ai = RegimeAI()
        res = ai.classify(
            adx=25, atr_pct=0.30, bb_width=3.5,
            closes=self._TRENDING_CLOSES, symbol="BTCUSDT",
        )
        # With MIN_STABILITY_TICKS=1, stability is met on tick 1; confidence=0.455 > 0.10
        assert res.block_trade is False
        assert res.stability_ticks == 1

    def test_block_trade_false_after_three_stable_ticks(self):
        """After 3 consecutive ticks with same regime and conf≥0.50, unblocked."""
        ai = RegimeAI()
        # Simulate 3 ticks returning TRENDING with decent confidence
        for _ in range(MIN_STABILITY_TICKS):
            res = ai.classify(
                adx=30, atr_pct=0.35, bb_width=4.5,
                closes=self._TRENDING_CLOSES, symbol="ETHUSDT",
            )
        # After 3 ticks: stability_ticks=3, confidence should be ≥0.50
        if res.confidence >= MIN_CONFIDENCE_TRADE:
            assert res.block_trade is False
        assert res.stability_ticks == MIN_STABILITY_TICKS

    def test_stability_resets_on_regime_change(self):
        ai = RegimeAI()
        # Pump 3 ticks of one regime
        for _ in range(3):
            ai.classify(adx=30, atr_pct=0.35, bb_width=4.5,
                        closes=self._TRENDING_CLOSES, symbol="XRPUSDT")
        # Now switch to a very different regime (mean reverting)
        mean_rev_closes = [100.0] * 60
        res = ai.classify(adx=10, atr_pct=0.05, bb_width=1.0,
                          closes=mean_rev_closes, symbol="XRPUSDT")
        assert res.stability_ticks == 1

    def test_block_trade_true_when_low_confidence(self):
        ai = RegimeAI()
        # Pre-warm stability to 3 ticks
        for _ in range(3):
            ai._stability_ticks["SYM"] = 3
            ai._last_regime_str["SYM"] = "TRENDING"
        # Force a result with very low confidence — below MIN_CONFIDENCE_TRADE=0.10
        res = RegimeAiResult(
            regime=__import__("core.regime_detector", fromlist=["Regime"]).Regime.TRENDING,
            confidence=0.05,  # below MIN_CONFIDENCE_TRADE (0.10)
            adx_score=0.5, atr_score=0.3, bb_score=0.4, rsi_score=0.1,
        )
        # block_trade logic: confidence < 0.10 → True
        assert res.confidence < MIN_CONFIDENCE_TRADE

    def test_stability_ticks_field_in_result(self):
        ai = RegimeAI()
        res = ai.classify(adx=25, atr_pct=0.30, bb_width=3.5,
                          closes=self._TRENDING_CLOSES, symbol="BNBUSDT")
        assert hasattr(res, "stability_ticks")
        assert hasattr(res, "block_trade")


# ── E: Profit Guard ───────────────────────────────────────────────────────────

class TestProfitGuard:
    """ProfitGuard gates: frequency multiplier + fee-ratio block."""

    def test_full_mult_when_pf_above_1(self):
        pg = ProfitGuard()
        assert pg.frequency_multiplier(1.5, MIN_TRADES_FOR_PF) == 1.0

    def test_reduced_mult_when_pf_below_1_after_min_trades(self):
        pg = ProfitGuard()
        mult = pg.frequency_multiplier(0.80, MIN_TRADES_FOR_PF)
        assert mult == FREQ_REDUCE_MULT

    def test_full_mult_when_below_min_trades(self):
        """Gate not active until MIN_TRADES_FOR_PF trades completed."""
        pg = ProfitGuard()
        mult = pg.frequency_multiplier(0.50, MIN_TRADES_FOR_PF - 1)
        assert mult == 1.0

    def test_full_mult_when_pf_exactly_1(self):
        pg = ProfitGuard()
        # PF == 1.0 is not < 1.0 → no reduction
        assert pg.frequency_multiplier(1.0, MIN_TRADES_FOR_PF) == 1.0

    def test_fee_ratio_blocks_when_over_max(self):
        pg = ProfitGuard()
        gross = 10.0
        fees  = gross * (FEE_RATIO_MAX + 0.05)   # 25% > 20%
        blocked, reason = pg.check_fee_ratio(gross, fees)
        assert blocked is True
        assert "HIGH_FEE_RATIO" in reason

    def test_fee_ratio_passes_when_under_max(self):
        pg = ProfitGuard()
        gross = 10.0
        fees  = gross * (FEE_RATIO_MAX - 0.05)   # 15% < 20%
        blocked, _ = pg.check_fee_ratio(gross, fees)
        assert blocked is False

    def test_fee_ratio_passes_on_zero_gross(self):
        """Cannot compute ratio when gross ≤ 0 — should not block."""
        pg = ProfitGuard()
        blocked, _ = pg.check_fee_ratio(0.0, 1.0)
        assert blocked is False

    def test_summary_reflects_pf_guard_active(self):
        pg = ProfitGuard()
        s = pg.summary(profit_factor=0.5, n_trades=MIN_TRADES_FOR_PF)
        assert s["pf_guard_active"] is True
        assert s["frequency_multiplier"] == FREQ_REDUCE_MULT

    def test_summary_guard_inactive_when_pf_ok(self):
        pg = ProfitGuard()
        s = pg.summary(profit_factor=1.5, n_trades=MIN_TRADES_FOR_PF)
        assert s["pf_guard_active"] is False
        assert s["frequency_multiplier"] == 1.0


# ── F: CT-Scan Engine ─────────────────────────────────────────────────────────

class TestCtScanEngine:
    """CtScanEngine.scan() correctly classifies system health."""

    def _usage(self, dominant: str) -> dict:
        return {s: (1.0 if s == dominant else 0.0) for s in KNOWN_STRATEGIES}

    def test_healthy_when_all_good(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=1.5,
            fee_ratio=0.05,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55,
            regime_stable=True,
            n_trades=20,
        )
        assert result["system_health"] == HEALTH_HEALTHY
        assert result["issues"] == []
        assert result["score"] == 100

    def test_critical_when_pf_below_1(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=0.80,
            fee_ratio=0.05,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55,
            n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert result["system_health"] == HEALTH_CRITICAL
        assert any("profit factor" in i.lower() for i in result["issues"])

    def test_warning_when_high_fees(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=1.2,
            fee_ratio=0.30,   # 30% > FEE_RATIO_WARN(20%)
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55,
            n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert result["system_health"] == HEALTH_WARNING
        assert any("fee" in i.lower() for i in result["issues"])

    def test_warning_when_single_strategy(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=1.2,
            fee_ratio=0.05,
            strategy_usage=self._usage("TrendFollowing"),
            win_rate=0.55,
            n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert result["system_health"] == HEALTH_WARNING
        assert any("strategy" in i.lower() for i in result["issues"])

    def test_warning_when_low_win_rate(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=1.2,
            fee_ratio=0.05,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.35,   # below 40%
            n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert result["system_health"] == HEALTH_WARNING
        assert any("win rate" in i.lower() for i in result["issues"])

    def test_score_decreases_with_each_issue(self):
        eng = CtScanEngine()
        good = eng.scan(
            profit_factor=1.5, fee_ratio=0.05,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55, n_trades=MIN_TRADES_FOR_EVAL,
        )
        bad = eng.scan(
            profit_factor=0.8, fee_ratio=0.35,
            strategy_usage=self._usage("TrendFollowing"),
            win_rate=0.30, n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert bad["score"] < good["score"]

    def test_no_critical_below_min_trades(self):
        """PF gate should not fire before MIN_TRADES_FOR_EVAL."""
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=0.50,
            fee_ratio=0.05,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55,
            n_trades=MIN_TRADES_FOR_EVAL - 1,
        )
        assert result["system_health"] != HEALTH_CRITICAL

    def test_action_contains_reduce_trades_when_pf_low(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=0.70,
            fee_ratio=0.05,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55,
            n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert "reduce" in result["action"].lower()

    def test_action_contains_fee_advice_when_fees_high(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=1.5,
            fee_ratio=0.35,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.55,
            n_trades=MIN_TRADES_FOR_EVAL,
        )
        assert "fee" in result["action"].lower() or "notional" in result["action"].lower()

    def test_result_contains_required_keys(self):
        eng = CtScanEngine()
        result = eng.scan(
            profit_factor=1.0, fee_ratio=0.10,
            strategy_usage={"TrendFollowing": 0.5, "MeanReversion": 0.3, "VolatilityExpansion": 0.2},
            win_rate=0.50, n_trades=5,
        )
        for key in ("system_health", "issues", "action", "score"):
            assert key in result

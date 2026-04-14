"""
Tests for FTD-REF-024 Edge Creation Engine.

Covers:
  - Edge calculation accuracy        (core/edge_engine.py)
  - Strategy auto-disable kill switch (core/edge_engine.py)
  - Trade rejection logic            (core/signal_filter.py edge gate)
  - Market structure detection       (core/market_structure.py)
  - Fee-aware gate                   (core/execution_engine.py)
  - Capital preservation soft cut    (core/risk_engine.py)
  - Drastic weight below 40% WR      (core/learning_engine.py)
  - Profit factor tracking           (edge_engine expectancy)

Run with:  python -m pytest tests/test_edge_engine.py -v
"""
import pytest

from core.edge_engine      import EdgeEngine, MIN_TRADES, EDGE_BOOST_THRESH, EDGE_BOOST_MULT
from core.market_structure import (
    MarketStructureDetector,
    STRUCTURE_TREND, STRUCTURE_RANGE,
    STRUCTURE_FAKE_BREAKOUT, STRUCTURE_LOW_VOL_TRAP, STRUCTURE_UNKNOWN,
    ATR_LOW_VOL_TRAP, ADX_RANGE_MAX, BB_RANGE_MAX,
)
from core.execution_engine import ExecutionEngine, FEE_RATE
from core.risk_engine      import RiskEngine, SIZE_SOFT_CUT_AT, SIZE_SOFT_CUT_TO, SIZE_HALVE_AT_DD
from core.learning_engine  import (
    LearningEngine, WR_DRASTIC_THRESH, WEIGHT_AT_DRASTIC_WR, WEIGHT_AT_LOW_WR,
)
from core.signal_filter    import SignalFilter


# ═══════════════════════════════════════════════════════════════════════════════
# A. EDGE ENGINE — EDGE CALCULATION ACCURACY
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCalculation:

    def setup_method(self):
        self.eng = EdgeEngine()

    def test_no_trades_returns_zero_edge(self):
        assert self.eng.get_edge("TRENDING", "TrendFollowing") == 0.0

    def test_all_wins_positive_edge(self):
        for _ in range(5):
            self.eng.record("TRENDING", "TrendFollowing", net_pnl=100.0, r_mult=2.0)
        assert self.eng.get_edge("TRENDING", "TrendFollowing") > 0

    def test_all_losses_negative_edge(self):
        for _ in range(5):
            self.eng.record("TRENDING", "TrendFollowing", net_pnl=-80.0, r_mult=-1.0)
        assert self.eng.get_edge("TRENDING", "TrendFollowing") < 0

    def test_edge_formula_correctness(self):
        """edge = (win_rate × avg_win) − ((1−win_rate) × avg_loss)"""
        # 3 wins of 100, 2 losses of 50 → win_rate=0.6, avg_win=100, avg_loss=50
        # edge = 0.6×100 − 0.4×50 = 60 − 20 = 40
        for _ in range(3):
            self.eng.record("TRENDING", "Strat", net_pnl=100.0)
        for _ in range(2):
            self.eng.record("TRENDING", "Strat", net_pnl=-50.0)
        edge = self.eng.get_edge("TRENDING", "Strat")
        assert abs(edge - 40.0) < 1e-6

    def test_expectancy_negative_when_avg_loss_dominates(self):
        """2 wins of 10, 3 losses of 100 → negative edge"""
        for _ in range(2):
            self.eng.record("TRENDING", "Strat", net_pnl=10.0)
        for _ in range(3):
            self.eng.record("TRENDING", "Strat", net_pnl=-100.0)
        assert self.eng.get_edge("TRENDING", "Strat") < 0

    def test_stats_structure(self):
        self.eng.record("TRENDING", "Strat", net_pnl=50.0, r_mult=1.5)
        s = self.eng.stats("TRENDING", "Strat")
        assert s.n_trades == 1
        assert s.avg_win > 0
        assert s.avg_rr == pytest.approx(1.5)

    def test_rolling_window_drops_old_trades(self):
        eng = EdgeEngine()
        eng._history[("TRENDING", "Strat")] = __import__("collections").deque(maxlen=5)
        for _ in range(5):
            eng.record("TRENDING", "Strat", net_pnl=-100.0)   # 5 losses
        for _ in range(5):
            eng.record("TRENDING", "Strat", net_pnl=200.0)    # 5 wins overwrite
        assert eng.get_edge("TRENDING", "Strat") > 0

    def test_multiple_strategies_independent(self):
        self.eng.record("TRENDING", "StratA", net_pnl=100.0)
        self.eng.record("TRENDING", "StratB", net_pnl=-100.0)
        assert self.eng.get_edge("TRENDING", "StratA") > 0
        assert self.eng.get_edge("TRENDING", "StratB") < 0

    def test_summary_structure(self):
        self.eng.record("TRENDING", "Strat", net_pnl=50.0)
        s = self.eng.summary()
        assert "window_size" in s
        assert "strategies"  in s


# ═══════════════════════════════════════════════════════════════════════════════
# B. AUTO STRATEGY KILL SWITCH
# ═══════════════════════════════════════════════════════════════════════════════

class TestKillSwitch:

    def setup_method(self):
        self.eng = EdgeEngine()

    def _add_trades(self, n_win, n_loss, win_pnl=50.0, loss_pnl=-100.0):
        for _ in range(n_win):
            self.eng.record("TRENDING", "Strat", net_pnl=win_pnl)
        for _ in range(n_loss):
            self.eng.record("TRENDING", "Strat", net_pnl=loss_pnl)

    def test_no_kill_before_min_trades(self):
        """Kill switch requires MIN_TRADES before activating."""
        for _ in range(MIN_TRADES - 1):
            self.eng.record("TRENDING", "Strat", net_pnl=-100.0)
        allowed, _ = self.eng.check_trade("TRENDING", "Strat")
        assert allowed is True

    def test_kill_activates_on_negative_edge(self):
        """MIN_TRADES losses → edge < 0 → kill switch on."""
        for _ in range(MIN_TRADES):
            self.eng.record("TRENDING", "Strat", net_pnl=-100.0)
        allowed, reason = self.eng.check_trade("TRENDING", "Strat")
        assert allowed is False
        assert "EDGE_KILL" in reason

    def test_kill_allows_trade_before_min_trades(self):
        """Only 5 losses (< MIN_TRADES) → still allowed."""
        for _ in range(5):
            self.eng.record("TRENDING", "Strat", net_pnl=-100.0)
        allowed, _ = self.eng.check_trade("TRENDING", "Strat")
        assert allowed is True

    def test_kill_switch_clears_when_edge_recovers(self):
        """After kill switch, large wins turn edge positive → re-enabled."""
        for _ in range(MIN_TRADES):
            self.eng.record("TRENDING", "Strat", net_pnl=-50.0)
        allowed_before, _ = self.eng.check_trade("TRENDING", "Strat")
        assert allowed_before is False

        # Record many large wins to flip edge positive
        for _ in range(MIN_TRADES * 2):
            self.eng.record("TRENDING", "Strat", net_pnl=500.0)
        allowed_after, _ = self.eng.check_trade("TRENDING", "Strat")
        assert allowed_after is True

    def test_kill_switch_per_regime_independent(self):
        """Kill switch on TRENDING does not affect MEAN_REVERTING."""
        for _ in range(MIN_TRADES):
            self.eng.record("TRENDING",       "Strat", net_pnl=-100.0)
            self.eng.record("MEAN_REVERTING", "Strat", net_pnl=+100.0)
        assert self.eng.check_trade("TRENDING",       "Strat")[0] is False
        assert self.eng.check_trade("MEAN_REVERTING", "Strat")[0] is True


# ═══════════════════════════════════════════════════════════════════════════════
# C. EDGE BOOSTER — SIZE MULTIPLIER
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeBooster:

    def setup_method(self):
        self.eng = EdgeEngine()

    def test_no_boost_without_data(self):
        assert self.eng.get_size_multiplier("TRENDING", "Strat") == 1.0

    def test_no_boost_before_min_trades(self):
        for _ in range(MIN_TRADES - 1):
            self.eng.record("TRENDING", "Strat", net_pnl=500.0)
        assert self.eng.get_size_multiplier("TRENDING", "Strat") == 1.0

    def test_boost_activates_on_strong_positive_edge(self):
        """Large wins after MIN_TRADES → edge > EDGE_BOOST_THRESH → mult > 1.0."""
        for _ in range(MIN_TRADES):
            self.eng.record("TRENDING", "Strat", net_pnl=500.0)
        mult = self.eng.get_size_multiplier("TRENDING", "Strat")
        # With 100% win rate and big wins, edge >> EDGE_BOOST_THRESH
        assert mult == pytest.approx(EDGE_BOOST_MULT)

    def test_no_boost_on_weak_edge(self):
        """Barely positive edge below EDGE_BOOST_THRESH → mult stays 1.0."""
        # 51% win rate, small difference → edge < EDGE_BOOST_THRESH
        for i in range(MIN_TRADES):
            self.eng.record("TRENDING", "Strat", net_pnl=1.0 if i % 2 == 0 else -0.9)
        mult = self.eng.get_size_multiplier("TRENDING", "Strat")
        assert mult == 1.0

    def test_boost_capped_at_max(self):
        for _ in range(MIN_TRADES):
            self.eng.record("TRENDING", "Strat", net_pnl=10_000.0)
        mult = self.eng.get_size_multiplier("TRENDING", "Strat")
        assert mult <= EDGE_BOOST_MULT   # capped at EDGE_BOOST_MULT ≤ MAX_EDGE_MULT


# ═══════════════════════════════════════════════════════════════════════════════
# D. SIGNAL FILTER — EDGE GATE (TRADE REJECTION)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalFilterEdgeGate:

    def setup_method(self):
        self.sf = SignalFilter()

    def _good_params(self, **overrides):
        p = dict(
            symbol="BTCUSDT", entry=50000, take_profit=50900, stop_loss=49500,
            cost_usdt=5.0, atr_pct=0.3, confidence=0.7, regime="TRENDING",
        )
        p.update(overrides)
        return p

    def test_negative_edge_rejects_trade(self):
        """expected_edge < 0 → FilterResult(ok=False)."""
        r = self.sf.check(**self._good_params(), expected_edge=-0.05)
        assert r.ok is False
        assert "NEGATIVE_EDGE" in r.reason

    def test_zero_edge_allows_trade(self):
        """expected_edge == 0.0 (default) → does NOT reject."""
        r = self.sf.check(**self._good_params(), expected_edge=0.0)
        assert r.ok is True

    def test_positive_edge_allows_trade(self):
        r = self.sf.check(**self._good_params(), expected_edge=0.5)
        assert r.ok is True

    def test_edge_gate_fires_before_other_gates(self):
        """Even with perfect RR/confidence, negative edge blocks the trade."""
        r = self.sf.check(
            symbol="BTC", entry=100, take_profit=200, stop_loss=99,
            cost_usdt=0.01, atr_pct=0.5, confidence=0.99,
            regime="TRENDING", expected_edge=-1.0,
        )
        assert r.ok is False
        assert "NEGATIVE_EDGE" in r.reason


# ═══════════════════════════════════════════════════════════════════════════════
# E. MARKET STRUCTURE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarketStructure:

    def setup_method(self):
        self.det = MarketStructureDetector()

    def test_low_vol_trap_detected(self):
        r = self.det.detect(adx=25.0, bb_width=3.0, atr_pct=0.03)
        assert r.structure == STRUCTURE_LOW_VOL_TRAP
        assert r.tradeable is False
        assert "LOW_VOL_TRAP" in r.block_reason

    def test_fake_breakout_detected(self):
        # ADX in ambiguous zone (15-20), BB contracting, low ATR%
        r = self.det.detect(adx=17.0, bb_width=2.0, atr_pct=0.10)
        assert r.structure == STRUCTURE_FAKE_BREAKOUT
        assert r.tradeable is False

    def test_trend_detected(self):
        r = self.det.detect(adx=28.0, bb_width=5.0, atr_pct=0.30)
        assert r.structure == STRUCTURE_TREND
        assert r.tradeable is True

    def test_range_detected(self):
        r = self.det.detect(adx=10.0, bb_width=1.5, atr_pct=0.20)
        assert r.structure == STRUCTURE_RANGE
        assert r.tradeable is True

    def test_unknown_on_mixed_signals(self):
        # ADX strong but BB tight (mixed)
        r = self.det.detect(adx=22.0, bb_width=2.0, atr_pct=0.25)
        assert r.structure == STRUCTURE_UNKNOWN
        assert r.tradeable is True   # UNKNOWN allows trading

    def test_low_vol_trap_takes_priority_over_trend(self):
        """Even with strong ADX, low ATR% → LOW_VOL_TRAP."""
        r = self.det.detect(adx=40.0, bb_width=6.0, atr_pct=0.02)
        assert r.structure == STRUCTURE_LOW_VOL_TRAP

    def test_confidence_in_range(self):
        r = self.det.detect(adx=25.0, bb_width=4.0, atr_pct=0.30)
        assert 0.0 <= r.confidence <= 1.0

    def test_block_reason_empty_when_tradeable(self):
        r = self.det.detect(adx=25.0, bb_width=4.0, atr_pct=0.30)
        assert r.block_reason == ""


# ═══════════════════════════════════════════════════════════════════════════════
# F. EXECUTION ENGINE — FEE-AWARE GATE
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionEngineFeeGate:

    def setup_method(self):
        self.eng = ExecutionEngine()

    def test_reject_when_profit_less_than_fees(self):
        """Gross profit < round-trip fees → reject."""
        notional = 10_000.0
        fee_rt = notional * FEE_RATE * 2   # round-trip fees
        # Give gross profit just below fees
        reject, reason = self.eng.should_reject_for_fees(
            expected_gross_profit=fee_rt * 0.5,
            notional=notional,
        )
        assert reject is True
        assert "FEE_EXCEEDS_PROFIT" in reason

    def test_allow_when_profit_exceeds_fees(self):
        notional = 10_000.0
        fee_rt = notional * FEE_RATE * 2
        reject, _ = self.eng.should_reject_for_fees(
            expected_gross_profit=fee_rt * 2,   # 2× fees → profitable
            notional=notional,
        )
        assert reject is False

    def test_reject_zero_profit(self):
        reject, _ = self.eng.should_reject_for_fees(
            expected_gross_profit=0.0, notional=10_000.0
        )
        assert reject is True

    def test_large_profit_never_rejected(self):
        reject, _ = self.eng.should_reject_for_fees(
            expected_gross_profit=1_000.0, notional=10_000.0
        )
        assert reject is False


# ═══════════════════════════════════════════════════════════════════════════════
# G. RISK ENGINE — CAPITAL PRESERVATION TIERED DD CUT
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskEngineCapitalPreservation:

    def setup_method(self):
        self.re = RiskEngine()
        self.re.initialize(current_equity=10_000.0)

    def test_soft_cut_at_5pct_drawdown(self):
        """5.1% DD → size_multiplier should be SIZE_SOFT_CUT_TO (0.75)."""
        self.re.update_equity(9_490.0)   # ~5.1% DD
        assert self.re.size_multiplier == SIZE_SOFT_CUT_TO

    def test_full_halve_at_10pct_drawdown(self):
        """10.1% DD → size_multiplier should be 0.50."""
        self.re.update_equity(8_990.0)   # ~10.1% DD
        assert self.re.size_multiplier == 0.50

    def test_no_cut_below_5pct_drawdown(self):
        """4% DD → size_multiplier stays 1.0."""
        self.re.update_equity(9_600.0)   # 4% DD
        assert self.re.size_multiplier == 1.0

    def test_recovery_from_soft_cut_restores_full(self):
        """After soft cut, recovering below 5% DD restores to 1.0."""
        self.re.update_equity(9_490.0)   # 5.1% → soft cut
        assert self.re.size_multiplier == SIZE_SOFT_CUT_TO
        self.re._state.peak_equity = 9_490.0   # new peak (simulated)
        self.re.update_equity(9_500.0)          # < 5% DD from new peak
        assert self.re.size_multiplier == 1.0

    def test_recovery_from_halve_goes_to_soft_cut_first(self):
        """
        Recovering from 10%+ DD to 5-10% range should land at soft cut (0.75),
        not jump directly to 1.0.
        """
        self.re.update_equity(8_990.0)   # 10.1% → halve to 0.5
        assert self.re.size_multiplier == 0.50
        # Recover to 7% DD range
        self.re._state.peak_equity = 10_000.0   # keep original peak
        self.re.update_equity(9_300.0)           # 7% DD → should be soft cut
        assert self.re.size_multiplier == SIZE_SOFT_CUT_TO


# ═══════════════════════════════════════════════════════════════════════════════
# H. LEARNING ENGINE — DRASTIC WEIGHT BELOW 40% WIN RATE
# ═══════════════════════════════════════════════════════════════════════════════

class TestLearningEngineDrasticWeight:

    def setup_method(self):
        self.le = LearningEngine()

    def test_very_low_wr_returns_drastic_weight(self):
        """WR = 0% → weight = WEIGHT_AT_DRASTIC_WR (0.50)."""
        for _ in range(10):
            self.le.record("TRENDING", False)
        w = self.le.get_regime_weight("TRENDING")
        assert w == WEIGHT_AT_DRASTIC_WR

    def test_40pct_wr_returns_drastic_weight(self):
        """WR exactly at WR_DRASTIC_THRESH → drastic weight."""
        # 4 wins, 6 losses = 40% WR (at threshold → drastic)
        for _ in range(4):
            self.le.record("TRENDING", True)
        for _ in range(6):
            self.le.record("TRENDING", False)
        w = self.le.get_regime_weight("TRENDING")
        assert w == WEIGHT_AT_DRASTIC_WR

    def test_mid_range_40_45_interpolates(self):
        """WR between 40% and 45% → between DRASTIC and LOW weights."""
        # 43% win rate: 43 wins, 57 losses over 100 trades (window=50 so use 50)
        # 43% over 50 trades: ~21 wins, 29 losses
        le = LearningEngine(window_size=50)
        for _ in range(21):
            le.record("TRENDING", True)
        for _ in range(29):
            le.record("TRENDING", False)
        w = le.get_regime_weight("TRENDING")
        assert WEIGHT_AT_DRASTIC_WR < w < WEIGHT_AT_LOW_WR

    def test_normal_45pct_returns_low_weight(self):
        """WR exactly at 45% boundary → at or just above WEIGHT_AT_LOW_WR."""
        for _ in range(9):
            self.le.record("TRENDING", True)
        for _ in range(11):
            self.le.record("TRENDING", False)
        w = self.le.get_regime_weight("TRENDING")
        # ~45% WR → WEIGHT_AT_LOW_WR = 0.80
        assert abs(w - WEIGHT_AT_LOW_WR) < 0.05

    def test_high_wr_still_returns_full_weight(self):
        """WR ≥ 55% → weight = 1.0 (drastic tier doesn't affect this)."""
        for _ in range(10):
            self.le.record("TRENDING", True)
        assert self.le.get_regime_weight("TRENDING") == 1.0

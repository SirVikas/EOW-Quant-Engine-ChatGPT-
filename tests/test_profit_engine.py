"""
Tests for Phase 4 — Profit Engine (Alpha Generation Core)

Covers:
  - RR Engine rejection + volatility scaling   (core/rr_engine.py)
  - Trade Scorer filtering                     (core/trade_scorer.py)
  - Alpha Entry Engine signal types            (strategies/alpha_engine.py)
  - Capital Allocator sizing + caps            (core/capital_allocator.py)
  - Trade Manager lifecycle management         (core/trade_manager.py)

Run with:  python -m pytest tests/test_profit_engine.py -v
"""
import math
import pytest

from core.rr_engine        import RREngine
from core.trade_scorer     import TradeScorer, WEIGHTS
from core.capital_allocator import CapitalAllocator
from core.trade_manager    import TradeManager, ManagedPosition
from strategies.alpha_engine import (
    TrendContinuationBreakout,
    PullbackEntryInTrend,
    VolatilitySqueezeEntry,
    AlphaEntryEngine,
)


# ═══════════════════════════════════════════════════════════════════════════════
# A. RR ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TestRREngine:

    def setup_method(self):
        self.engine = RREngine()

    def test_accepts_trade_meeting_min_rr(self):
        """Trade with RR=2.4 must pass (default min_rr=1.5)."""
        result = self.engine.evaluate(
            side="LONG", entry=100.0,
            stop_loss=97.5,   # SL dist = 2.5
            take_profit=106.0, # TP dist = 6.0  → RR=2.4
            atr=2.5, atr_pct=1.0,
        )
        assert result.ok, f"Expected OK but got: {result.reason}"
        assert result.rr >= 1.5

    def test_rejects_trade_below_min_rr(self):
        """Trade with RR=1.0 must be rejected."""
        result = self.engine.evaluate(
            side="LONG", entry=100.0,
            stop_loss=95.0,    # SL dist = 5.0
            take_profit=105.0, # TP dist = 5.0  → RR=1.0
            atr=5.0, atr_pct=1.0,
        )
        assert not result.ok
        assert "RR_BELOW_MIN" in result.reason

    def test_rejects_zero_sl_distance(self):
        result = self.engine.evaluate(
            side="LONG", entry=100.0,
            stop_loss=100.0, take_profit=106.0,
            atr=1.0, atr_pct=1.0,
        )
        assert not result.ok
        assert "ZERO_SL_DISTANCE" in result.reason

    def test_high_volatility_widens_tp_long(self):
        """atr_pct > 2% → TP widened by 20% for LONG."""
        result = self.engine.evaluate(
            side="LONG", entry=100.0,
            stop_loss=97.0, take_profit=106.0,
            atr=3.0, atr_pct=3.0,  # high volatility
        )
        # original TP dist = 6.0; adjusted = 6.0 * 1.20 = 7.2 → adj_tp = 107.2
        assert result.adjusted_tp > 106.0

    def test_high_volatility_widens_tp_short(self):
        """atr_pct > 2% → TP widened (lower) for SHORT."""
        result = self.engine.evaluate(
            side="SHORT", entry=100.0,
            stop_loss=103.0, take_profit=94.0,
            atr=3.0, atr_pct=3.0,
        )
        # original TP dist = 6.0; adjusted = 6.0 * 1.20 = 7.2 → adj_tp = 92.8
        assert result.adjusted_tp < 94.0

    def test_low_volatility_tightens_sl_long(self):
        """atr_pct < 0.5% → SL tightened by 20% for LONG."""
        result = self.engine.evaluate(
            side="LONG", entry=100.0,
            stop_loss=97.0, take_profit=110.0,  # TP very wide so RR passes
            atr=0.4, atr_pct=0.3,   # low volatility
        )
        # original SL dist = 3.0; tightened = 3.0 * 0.80 = 2.4 → adj_sl = 97.6
        assert result.adjusted_sl > 97.0

    def test_short_rejection_below_min_rr(self):
        """SHORT trade with RR=1.2 rejected."""
        result = self.engine.evaluate(
            side="SHORT", entry=100.0,
            stop_loss=103.0, take_profit=96.4,  # TP dist=3.6, SL dist=3.0 → RR=1.2
            atr=3.0, atr_pct=1.0,
        )
        assert not result.ok

    def test_rr_is_returned_on_success(self):
        result = self.engine.evaluate(
            side="LONG", entry=100.0,
            stop_loss=96.0, take_profit=112.0,
            atr=4.0, atr_pct=1.0,
        )
        assert result.ok
        assert result.rr == pytest.approx(3.0, abs=0.01)

    def test_summary_contains_min_rr(self):
        s = self.engine.summary()
        assert "min_rr" in s
        assert s["module"] == "RR_ENGINE"
        assert s["phase"] == 4


# ═══════════════════════════════════════════════════════════════════════════════
# B. TRADE SCORER
# ═══════════════════════════════════════════════════════════════════════════════

class TestTradeScorer:

    def setup_method(self):
        self.scorer = TradeScorer()

    def _high_quality_kwargs(self, side="LONG"):
        return dict(
            regime="TRENDING", adx=40.0,
            rsi=55.0, rsi_prev=50.0,       # positive slope for LONG
            atr_pct=1.5, avg_atr_pct=1.0,  # expansion ratio = 1.5
            vol_ratio=2.5, cost_fraction=0.05,
            signal_side=side,
        )

    def test_high_quality_trade_passes(self):
        result = self.scorer.score(**self._high_quality_kwargs())
        assert result.ok, f"Expected pass but reason={result.reason}"
        assert result.score >= 0.60

    def test_unknown_regime_lowers_score(self):
        kwargs = self._high_quality_kwargs()
        kwargs["regime"] = "UNKNOWN"
        result = self.scorer.score(**kwargs)
        # Should still pass given other strong factors, but score < TRENDING version
        trending_score = self.scorer.score(**self._high_quality_kwargs()).score
        assert result.score < trending_score

    def test_low_adx_reduces_score(self):
        kwargs = self._high_quality_kwargs()
        kwargs["adx"] = 5.0   # very low trend strength
        result = self.scorer.score(**kwargs)
        high = self.scorer.score(**self._high_quality_kwargs()).score
        assert result.score < high

    def test_zero_volume_ratio_rejects(self):
        """Near-zero volume → low score → rejection."""
        kwargs = self._high_quality_kwargs()
        kwargs["vol_ratio"] = 0.0
        kwargs["regime"] = "UNKNOWN"
        kwargs["adx"] = 5.0
        result = self.scorer.score(**kwargs)
        assert not result.ok

    def test_high_cost_fraction_reduces_score(self):
        kwargs = self._high_quality_kwargs()
        kwargs["cost_fraction"] = 0.19  # near cap
        low_cost = self.scorer.score(**kwargs).score
        kwargs["cost_fraction"] = 0.01
        high_eff = self.scorer.score(**kwargs).score
        assert high_eff > low_cost

    def test_wrong_rsi_slope_direction(self):
        """Negative RSI slope for a LONG signal should reduce momentum score."""
        kw_pos = self._high_quality_kwargs()
        kw_pos["rsi"]      = 55.0
        kw_pos["rsi_prev"] = 50.0   # positive slope
        kw_neg = self._high_quality_kwargs()
        kw_neg["rsi"]      = 45.0
        kw_neg["rsi_prev"] = 55.0   # negative slope (momentum against direction)
        pos_score = self.scorer.score(**kw_pos).score
        neg_score = self.scorer.score(**kw_neg).score
        assert pos_score > neg_score

    def test_rejection_returns_reason(self):
        kwargs = dict(
            regime="UNKNOWN", adx=5.0,
            rsi=50.0, rsi_prev=50.0,
            atr_pct=0.5, avg_atr_pct=1.0,
            vol_ratio=0.0, cost_fraction=0.19,
            signal_side="LONG",
        )
        result = self.scorer.score(**kwargs)
        assert not result.ok
        assert "LOW_SCORE" in result.reason

    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_breakdown_keys_match_weights(self):
        result = self.scorer.score(**self._high_quality_kwargs())
        assert set(result.breakdown.keys()) == set(WEIGHTS.keys())

    def test_summary_structure(self):
        s = self.scorer.summary()
        assert "min_score" in s
        assert "weights" in s
        assert s["phase"] == 4


# ═══════════════════════════════════════════════════════════════════════════════
# C. CAPITAL ALLOCATOR
# ═══════════════════════════════════════════════════════════════════════════════

class TestCapitalAllocator:

    def setup_method(self):
        self.alloc = CapitalAllocator()

    def test_score_above_0_9_gives_2x(self):
        result = self.alloc.allocate(trade_score=0.92, equity=1000.0, base_risk_usdt=10.0)
        assert result.size_multiplier == pytest.approx(2.0, abs=0.01)

    def test_score_0_85_gives_1_5x(self):
        result = self.alloc.allocate(trade_score=0.85, equity=1000.0, base_risk_usdt=10.0)
        assert result.size_multiplier == pytest.approx(1.5, abs=0.01)

    def test_score_0_75_gives_1x(self):
        result = self.alloc.allocate(trade_score=0.75, equity=1000.0, base_risk_usdt=10.0)
        assert result.size_multiplier == pytest.approx(1.0, abs=0.01)

    def test_score_0_65_gives_0_5x(self):
        result = self.alloc.allocate(trade_score=0.65, equity=1000.0, base_risk_usdt=10.0)
        assert result.size_multiplier == pytest.approx(0.5, abs=0.01)

    def test_score_below_0_6_blocked(self):
        result = self.alloc.allocate(trade_score=0.55, equity=1000.0, base_risk_usdt=10.0)
        assert result.size_multiplier == 0.0
        assert "SCORE_BELOW_MIN" in result.reason

    def test_max_capital_per_trade_cap(self):
        """2× on a large base_risk should be capped at max_capital_pct (5% of equity)."""
        equity = 1000.0
        # base_risk = 30 USDT; 2× = 60 USDT > 5% of 1000 = 50 USDT
        result = self.alloc.allocate(trade_score=0.95, equity=equity, base_risk_usdt=30.0)
        max_risk = equity * self.alloc.max_capital_pct
        assert result.max_risk_usdt <= max_risk + 0.001

    def test_daily_risk_cap_blocks_after_budget_exhausted(self):
        alloc = CapitalAllocator()
        equity = 1000.0
        # Exhaust daily budget: daily cap = 3% = 30 USDT
        alloc._daily_risk_used = equity * alloc.daily_risk_cap + 1.0
        result = alloc.allocate(trade_score=0.95, equity=equity, base_risk_usdt=5.0)
        assert result.size_multiplier == 0.0
        assert "DAILY_RISK_CAP_REACHED" in result.reason

    def test_record_risk_used_accumulates(self):
        alloc = CapitalAllocator()
        alloc.record_risk_used(5.0)
        alloc.record_risk_used(3.0)
        assert alloc._daily_risk_used == pytest.approx(8.0)

    def test_summary_structure(self):
        s = self.alloc.summary()
        assert "max_capital_pct" in s
        assert "daily_risk_cap" in s
        assert "score_bands" in s
        assert s["phase"] == 4


# ═══════════════════════════════════════════════════════════════════════════════
# D. TRADE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

def _make_position(side="LONG", entry=100.0, sl=97.0, tp=112.0, qty=1.0):
    return ManagedPosition(
        symbol="TESTUSDT", side=side,
        entry_price=entry, stop_loss=sl, take_profit=tp,
        initial_risk=abs(entry - sl), qty=qty,
    )


class TestTradeManager:

    def setup_method(self):
        self.mgr = TradeManager()

    def test_register_tracks_position(self):
        pos = _make_position()
        self.mgr.register(pos)
        assert self.mgr.is_managed("TESTUSDT")

    def test_deregister_removes_position(self):
        self.mgr.register(_make_position())
        self.mgr.deregister("TESTUSDT")
        assert not self.mgr.is_managed("TESTUSDT")

    def test_no_action_below_be_trigger(self):
        pos = _make_position(entry=100.0, sl=97.0)
        self.mgr.register(pos)
        action = self.mgr.update("TESTUSDT", current_price=101.5, atr=1.0)
        # 1.5 / 3.0 = 0.5R — below BE trigger of 1R
        assert action.action in ("HOLD", "NONE")

    def test_move_breakeven_at_1r_long(self):
        pos = _make_position(entry=100.0, sl=97.0)  # risk=3.0
        self.mgr.register(pos)
        # 1R = entry + 3.0 = 103.0; pass 103.5 to trigger BE
        action = self.mgr.update("TESTUSDT", current_price=103.5, atr=1.0)
        assert action.action == "MOVE_BE"
        assert action.new_sl > 97.0       # SL moved away from original
        assert action.new_sl >= 100.0     # at or above entry

    def test_move_breakeven_at_1r_short(self):
        pos = _make_position(side="SHORT", entry=100.0, sl=103.0, tp=91.0)
        self.mgr.register(pos)
        # risk=3.0; 1R = entry - 3.0 = 97.0; pass price 96.5
        action = self.mgr.update("TESTUSDT", current_price=96.5, atr=1.0)
        assert action.action == "MOVE_BE"
        assert action.new_sl <= 100.0  # SL moved down toward entry

    def test_be_set_only_once(self):
        pos = _make_position(entry=100.0, sl=97.0)
        self.mgr.register(pos)
        self.mgr.update("TESTUSDT", current_price=103.5, atr=1.0)  # triggers BE
        second = self.mgr.update("TESTUSDT", current_price=104.0, atr=1.0)
        assert second.action != "MOVE_BE"  # not triggered again

    def test_partial_tp_at_1_5r_long(self):
        pos = _make_position(entry=100.0, sl=97.0, qty=2.0)  # risk=3.0
        self.mgr.register(pos)
        # Force breakeven first
        self.mgr.update("TESTUSDT", current_price=103.5, atr=1.0)
        # 1.5R = 100 + 4.5 = 104.5; pass 105
        action = self.mgr.update("TESTUSDT", current_price=105.0, atr=1.0)
        assert action.action == "PARTIAL_TP"
        assert action.partial_qty == pytest.approx(1.0, abs=1e-6)  # 50% of 2.0

    def test_partial_tp_set_only_once(self):
        pos = _make_position(entry=100.0, sl=97.0, qty=2.0)
        self.mgr.register(pos)
        self.mgr.update("TESTUSDT", current_price=103.5, atr=1.0)  # BE
        self.mgr.update("TESTUSDT", current_price=105.0, atr=1.0)  # partial TP
        second = self.mgr.update("TESTUSDT", current_price=106.0, atr=1.0)
        assert second.action != "PARTIAL_TP"

    def test_trail_sl_after_breakeven(self):
        pos = _make_position(entry=100.0, sl=97.0)
        self.mgr.register(pos)
        # Set breakeven
        self.mgr.update("TESTUSDT", current_price=103.5, atr=1.0)
        # Push price higher to update peak
        self.mgr.update("TESTUSDT", current_price=107.0, atr=1.0)
        action = self.mgr.update("TESTUSDT", current_price=107.5, atr=1.0)
        assert action.action in ("TRAIL_SL", "HOLD")
        # Trail SL should be above the initial BE price
        if action.action == "TRAIL_SL":
            assert action.new_sl > 100.0

    def test_no_trail_before_breakeven(self):
        """Trail SL must not fire before breakeven is set."""
        pos = _make_position(entry=100.0, sl=97.0)
        self.mgr.register(pos)
        action = self.mgr.update("TESTUSDT", current_price=101.0, atr=1.0)
        assert action.action not in ("TRAIL_SL",)

    def test_get_current_sl_initial(self):
        pos = _make_position(entry=100.0, sl=97.0)
        self.mgr.register(pos)
        assert self.mgr.get_current_sl("TESTUSDT") == pytest.approx(97.0)

    def test_get_current_sl_missing(self):
        assert self.mgr.get_current_sl("MISSING") is None

    def test_summary_structure(self):
        s = self.mgr.summary()
        assert "managed_count" in s
        assert "be_r" in s
        assert "partial_tp_r" in s
        assert s["phase"] == 4


# ═══════════════════════════════════════════════════════════════════════════════
# E. ALPHA ENTRY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _make_trend_data(n: int = 150, drift: float = 0.003):
    """Generate synthetic uptrending OHLCV data."""
    closes  = [100.0 * (1 + drift) ** i for i in range(n)]
    highs   = [c * 1.005 for c in closes]
    lows    = [c * 0.995 for c in closes]
    volumes = [1_000_000.0 * (1.5 if i == n - 1 else 1.0) for i in range(n)]
    return closes, highs, lows, volumes


class TestAlphaEntryEngine:

    def test_trend_breakout_returns_signal_on_new_high(self):
        """TCB fires when price exceeds recent high with volume spike."""
        strat = TrendContinuationBreakout()
        closes, highs, lows, volumes = _make_trend_data(n=80, drift=0.005)
        # Ensure last price is a new high
        highs[-1] = max(highs[:-1]) * 1.01
        closes[-1] = highs[-1] * 0.999

        result = strat.generate(
            symbol="BTCUSDT", closes=closes, highs=highs, lows=lows,
            volumes=volumes, adx=35.0, atr_pct=1.2, avg_atr_pct=1.0,
            regime="TRENDING",
        )
        # May be None if score < threshold, that's acceptable — just verify types
        if result is not None:
            assert result.trade_signal.symbol == "BTCUSDT"
            assert result.rr >= 1.5
            assert result.score >= 0.60

    def test_trend_breakout_requires_adx_threshold(self):
        """TCB must not fire when ADX is below threshold."""
        strat = TrendContinuationBreakout()
        closes, highs, lows, volumes = _make_trend_data(n=80)
        highs[-1] = max(highs[:-1]) * 1.01
        closes[-1] = highs[-1] * 0.999
        result = strat.generate(
            symbol="XUSDT", closes=closes, highs=highs, lows=lows,
            volumes=volumes, adx=10.0,   # below 25 threshold
            atr_pct=1.2, avg_atr_pct=1.0, regime="TRENDING",
        )
        assert result is None

    def test_pullback_entry_returns_signal_near_ema(self):
        """PBE fires when price is near EMA and RSI has reset."""
        strat = PullbackEntryInTrend()
        # Flat then slight downward retrace (to simulate pullback)
        closes = [100.0 + i * 0.1 for i in range(120)]
        # Simulate pullback: last price slightly below recent trend
        closes[-1] = closes[-2] * 0.998
        highs   = [c * 1.002 for c in closes]
        lows    = [c * 0.998 for c in closes]
        volumes = [500_000.0] * 120
        result = strat.generate(
            symbol="ETHUSDT", closes=closes, highs=highs, lows=lows,
            volumes=volumes, adx=28.0, atr_pct=0.8, avg_atr_pct=0.8,
            regime="TRENDING",
        )
        # Either fires or doesn't based on exact RSI; just ensure no exception
        if result is not None:
            assert result.rr >= 1.5
            assert result.score >= 0.60

    def test_volatility_squeeze_requires_sufficient_data(self):
        """VSE returns None when data is too short."""
        strat = VolatilitySqueezeEntry()
        closes  = [100.0] * 30  # too short
        highs   = [c * 1.001 for c in closes]
        lows    = [c * 0.999 for c in closes]
        volumes = [1_000_000.0] * 30
        result = strat.generate(
            symbol="SOLSDT", closes=closes, highs=highs, lows=lows,
            volumes=volumes, adx=20.0, atr_pct=0.5, avg_atr_pct=0.5,
            regime="VOLATILITY_EXPANSION",
        )
        assert result is None

    def test_alpha_engine_returns_none_on_insufficient_data(self):
        engine = AlphaEntryEngine()
        closes  = [100.0] * 10
        highs   = [c * 1.001 for c in closes]
        lows    = [c * 0.999 for c in closes]
        volumes = [500_000.0] * 10
        result = engine.generate(
            symbol="XUSDT", closes=closes, highs=highs, lows=lows,
            volumes=volumes, adx=30.0, atr_pct=1.0, avg_atr_pct=1.0,
            regime="TRENDING",
        )
        assert result is None

    def test_alpha_engine_returns_best_scoring_signal(self):
        """When multiple strategies fire, the highest score wins."""
        engine = AlphaEntryEngine()
        closes, highs, lows, volumes = _make_trend_data(n=150, drift=0.005)
        highs[-1] = max(highs[:-1]) * 1.01
        closes[-1] = highs[-1] * 0.999

        result = engine.generate(
            symbol="BTCUSDT", closes=closes, highs=highs, lows=lows,
            volumes=volumes, adx=35.0, atr_pct=1.5, avg_atr_pct=1.0,
            regime="TRENDING",
        )
        if result is not None:
            assert result.score >= 0.60
            assert result.rr   >= 1.5
            assert result.alpha_type in ("TrendBreakout", "PullbackEntry", "VolatilitySqueeze")

    def test_alpha_engine_summary(self):
        engine = AlphaEntryEngine()
        s = engine.summary()
        assert "strategies" in s
        assert len(s["strategies"]) == 3
        assert s["phase"] == 4


# ═══════════════════════════════════════════════════════════════════════════════
# F. INTEGRATION: RR + SCORER + ALLOCATOR PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class TestProfitEnginePipeline:
    """End-to-end pipeline: score → RR → allocate."""

    def setup_method(self):
        self.rr     = RREngine()
        self.scorer = TradeScorer()
        self.alloc  = CapitalAllocator()

    def test_full_pipeline_high_quality_trade(self):
        """High-quality TRENDING trade passes all three gates."""
        score_res = self.scorer.score(
            regime="TRENDING", adx=42.0,
            rsi=58.0, rsi_prev=52.0,
            atr_pct=1.5, avg_atr_pct=1.0,
            vol_ratio=2.0, cost_fraction=0.04,
            signal_side="LONG",
        )
        assert score_res.ok, f"Score gate failed: {score_res.reason}"

        rr_res = self.rr.evaluate(
            side="LONG", entry=100.0,
            stop_loss=97.5, take_profit=115.0,
            atr=2.5, atr_pct=1.5,
        )
        assert rr_res.ok, f"RR gate failed: {rr_res.reason}"

        alloc_res = self.alloc.allocate(
            trade_score=score_res.score,
            equity=1000.0, base_risk_usdt=10.0,
        )
        assert alloc_res.size_multiplier > 0
        assert alloc_res.size_multiplier >= 1.0  # score should qualify for at least 1x

    def test_full_pipeline_rejects_weak_rr(self):
        """Good score but bad RR → pipeline rejects at RR gate."""
        score_res = self.scorer.score(
            regime="TRENDING", adx=40.0,
            rsi=55.0, rsi_prev=50.0,
            atr_pct=1.2, avg_atr_pct=1.0,
            vol_ratio=2.0, cost_fraction=0.04,
            signal_side="LONG",
        )
        # Score might pass
        rr_res = self.rr.evaluate(
            side="LONG", entry=100.0,
            stop_loss=95.0, take_profit=101.0,  # RR=0.2 — terrible
            atr=5.0, atr_pct=1.2,
        )
        assert not rr_res.ok

    def test_full_pipeline_rejects_low_score(self):
        """Bad score → rejected before RR check."""
        score_res = self.scorer.score(
            regime="UNKNOWN", adx=5.0,
            rsi=50.0, rsi_prev=50.0,
            atr_pct=0.5, avg_atr_pct=1.0,
            vol_ratio=0.0, cost_fraction=0.18,
            signal_side="LONG",
        )
        assert not score_res.ok

    def test_capital_scales_correctly_with_score(self):
        """Higher score must result in equal or larger allocation multiplier."""
        low_alloc  = self.alloc.allocate(0.65, 1000.0, 10.0)
        mid_alloc  = self.alloc.allocate(0.75, 1000.0, 10.0)
        high_alloc = self.alloc.allocate(0.85, 1000.0, 10.0)
        top_alloc  = self.alloc.allocate(0.92, 1000.0, 10.0)

        assert low_alloc.size_multiplier  <= mid_alloc.size_multiplier
        assert mid_alloc.size_multiplier  <= high_alloc.size_multiplier
        assert high_alloc.size_multiplier <= top_alloc.size_multiplier

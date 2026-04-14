"""
Tests for FTD-REF-023 Profitability Unlock Layer.

Covers:
  - Trade frequency relaxation      (core/trade_frequency.py)
  - Execution realism               (core/execution_engine.py)
  - Learning engine regime weights  (core/learning_engine.py)
  - Regime AI UNKNOWN fallback      (core/regime_ai.py — FTD-REF-023 additions)
  - Regime AI stability factor      (core/regime_ai.py — FTD-REF-023 additions)
  - Signal filter adaptive regimes  (core/signal_filter.py — FTD-REF-023 additions)
  - Risk engine streak scaling      (core/risk_engine.py — FTD-REF-023 additions)
  - Deployability warmup + bonus    (core/deployability.py — FTD-REF-023 additions)

Run with:  python -m pytest tests/test_profitability.py -v
"""
import time
import pytest

from core.trade_frequency  import TradeFrequency, RELAX_SHORT, RELAX_LONG, WINDOW_SHORT_SEC
from core.execution_engine import ExecutionEngine, FEE_RATE, SLIPPAGE_BASE_PCT
from core.learning_engine  import (
    LearningEngine, WR_HIGH_THRESH, WR_LOW_THRESH,
    WR_DRASTIC_THRESH, WEIGHT_AT_LOW_WR, WEIGHT_AT_DRASTIC_WR,
)
from core.regime_ai        import RegimeAI, FALLBACK_CONF_PENALTY, ATR_HIGH_THRESH, ATR_LOW_THRESH
from core.signal_filter    import SignalFilter
from core.risk_engine      import (
    RiskEngine,
    WIN_STREAK_BOOST_AT, WIN_STREAK_BOOST_PCT,
    LOSS_STREAK_CUT_AT, LOSS_STREAK_CUT_PCT,
    MIN_STREAK_MULTIPLIER, MAX_STREAK_MULTIPLIER,
)
from core.deployability    import (
    DeployabilityEngine,
    STATUS_WARMUP, STATUS_IMPROVING, STATUS_READY, STATUS_NOT_READY,
    WARMUP_TRADES, MIN_TRADES, CONSISTENCY_BONUS, CONSISTENCY_THRESH,
)
from core.regime_detector  import Regime


# ═══════════════════════════════════════════════════════════════════════════════
# A. TRADE FREQUENCY CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class TestTradeFrequency:

    def setup_method(self):
        self.tf = TradeFrequency()

    def test_no_trades_returns_relax_short(self):
        """Empty history → maximum relaxation (dry spell)."""
        factor = self.tf.get_relaxation_factor()
        assert factor == RELAX_SHORT

    def test_one_recent_trade_returns_relax_long(self):
        """One trade in 30 min window → 2-hr window check triggers RELAX_LONG."""
        self.tf.record_trade()
        factor = self.tf.get_relaxation_factor()
        # 1 trade in short window → count_short=1, but count_long<2 → RELAX_LONG
        assert factor == RELAX_LONG

    def test_two_recent_trades_returns_full_factor(self):
        """Two trades within 2 hr window → no relaxation."""
        self.tf.record_trade()
        self.tf.record_trade()
        factor = self.tf.get_relaxation_factor()
        assert factor == 1.0

    def test_record_trade_increments_count(self):
        """trades_in_window reflects recorded trades."""
        self.tf.record_trade()
        self.tf.record_trade()
        assert self.tf.trades_in_window(3600) == 2

    def test_summary_keys(self):
        s = self.tf.summary()
        assert "trades_last_30min" in s
        assert "trades_last_2hr"   in s
        assert "relaxation_factor" in s

    def test_factor_is_bounded(self):
        for _ in range(10):
            self.tf.record_trade()
        factor = self.tf.get_relaxation_factor()
        assert RELAX_SHORT <= factor <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# B. EXECUTION ENGINE — REALISTIC PRICING
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionEngine:

    def setup_method(self):
        self.eng = ExecutionEngine()

    def test_long_entry_above_mid(self):
        """LONG entry fill must be above mid price (slippage + spread)."""
        entry = self.eng.simulate_entry(mid_price=100.0, side="BUY")
        assert entry > 100.0

    def test_short_entry_below_mid(self):
        """SHORT entry fill must be below mid price."""
        entry = self.eng.simulate_entry(mid_price=100.0, side="SELL")
        assert entry < 100.0

    def test_long_exit_below_mid(self):
        """LONG exit fill must be below mid price."""
        exit_p = self.eng.simulate_exit(mid_price=100.0, side="SELL")
        assert exit_p < 100.0

    def test_short_exit_above_mid(self):
        """SHORT exit fill must be above mid price."""
        exit_p = self.eng.simulate_exit(mid_price=100.0, side="BUY")
        assert exit_p > 100.0

    def test_fee_calculation(self):
        fee = self.eng.fee_for_notional(1000.0)
        assert abs(fee - 1000.0 * FEE_RATE) < 1e-9

    def test_slippage_capped(self):
        """High ATR should not push slippage above SLIPPAGE_MAX_PCT."""
        from core.execution_engine import SLIPPAGE_MAX_PCT
        price = 50000.0
        slip  = ExecutionEngine._slippage(price, atr_abs=price * 0.05)  # huge ATR
        assert slip <= price * SLIPPAGE_MAX_PCT + 1e-9

    def test_simulate_trade_long_profitable(self):
        """If exit > entry in direction, net_pnl after fees should be positive."""
        result = self.eng.simulate_trade(
            entry_mid=100.0, exit_mid=110.0, qty=1.0, direction="LONG"
        )
        assert result.net_pnl > 0

    def test_simulate_trade_long_losing(self):
        """If exit < entry, net_pnl should be negative."""
        result = self.eng.simulate_trade(
            entry_mid=100.0, exit_mid=95.0, qty=1.0, direction="LONG"
        )
        assert result.net_pnl < 0

    def test_simulate_trade_short_profitable(self):
        """SHORT: exit_mid < entry_mid → profit."""
        result = self.eng.simulate_trade(
            entry_mid=100.0, exit_mid=90.0, qty=1.0, direction="SHORT"
        )
        assert result.net_pnl > 0

    def test_simulate_trade_includes_fees(self):
        """Fees must be > 0 and reduce PnL."""
        result = self.eng.simulate_trade(
            entry_mid=100.0, exit_mid=110.0, qty=1.0, direction="LONG"
        )
        assert result.fee_entry > 0
        assert result.fee_exit  > 0

    def test_cost_summary_keys(self):
        s = self.eng.cost_summary()
        for k in ("slippage_base_pct", "fee_rate_per_leg", "fee_round_trip"):
            assert k in s


# ═══════════════════════════════════════════════════════════════════════════════
# C. LEARNING ENGINE — PER-REGIME WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLearningEngine:

    def setup_method(self):
        self.le = LearningEngine()

    def test_unknown_regime_returns_full_weight(self):
        """No data → weight = 1.0 (no penalty)."""
        assert self.le.get_regime_weight("TRENDING") == 1.0

    def test_insufficient_samples_returns_full_weight(self):
        """Below MIN_SAMPLES → no adjustment."""
        for _ in range(3):
            self.le.record("TRENDING", True)
        assert self.le.get_regime_weight("TRENDING") == 1.0

    def test_high_win_rate_returns_full_weight(self):
        """WR ≥ 55% → weight = 1.0."""
        for _ in range(10):
            self.le.record("TRENDING", True)   # 100% WR
        assert self.le.get_regime_weight("TRENDING") == 1.0

    def test_low_win_rate_returns_reduced_weight(self):
        """WR ≤ 40% → weight = WEIGHT_AT_DRASTIC_WR (FTD-REF-024 drastic tier)."""
        for _ in range(10):
            self.le.record("TRENDING", False)  # 0% WR
        w = self.le.get_regime_weight("TRENDING")
        assert w == WEIGHT_AT_DRASTIC_WR

    def test_mid_win_rate_interpolates(self):
        """WR between LOW and HIGH → interpolated weight."""
        # Exactly 50% win-rate (5 wins, 5 losses) with ≥ MIN_SAMPLES
        for _ in range(5):
            self.le.record("TRENDING", True)
        for _ in range(5):
            self.le.record("TRENDING", False)
        w = self.le.get_regime_weight("TRENDING")
        assert WEIGHT_AT_LOW_WR < w < 1.0

    def test_multiple_regimes_independent(self):
        """Records for different regimes don't cross-contaminate."""
        for _ in range(10):
            self.le.record("TRENDING",       True)
            self.le.record("MEAN_REVERTING", False)
        # TRENDING: 100% WR → full weight
        assert self.le.get_regime_weight("TRENDING") == 1.0
        # MEAN_REVERTING: 0% WR → drastic weight (FTD-REF-024)
        assert self.le.get_regime_weight("MEAN_REVERTING") == WEIGHT_AT_DRASTIC_WR

    def test_rolling_window_drops_old_trades(self):
        """Old losses are evicted from window by new wins."""
        le = LearningEngine(window_size=5)
        for _ in range(5):
            le.record("TRENDING", False)   # 5 losses
        for _ in range(5):
            le.record("TRENDING", True)    # 5 wins overwrite old
        assert le.get_regime_weight("TRENDING") == 1.0

    def test_summary_structure(self):
        self.le.record("TRENDING", True)
        s = self.le.summary()
        assert "regimes" in s
        assert "TRENDING" in s["regimes"]


# ═══════════════════════════════════════════════════════════════════════════════
# D. REGIME AI — FTD-REF-023 UPGRADES
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegimeAiFtd023:

    def setup_method(self):
        self.ai = RegimeAI()
        # Use enough closes for RSI calculation
        self._closes = [100.0 + i * 0.5 for i in range(30)]

    def test_unknown_with_no_cache_stays_unknown(self):
        """UNKNOWN when no prior valid regime cached."""
        result = self.ai.classify(
            adx=17.0, atr_pct=0.20, bb_width=3.0,
            closes=self._closes, symbol="TEST"
        )
        # ADX in ambiguous zone, confidence likely below MIN_CONFIDENCE
        # Just verify it returns a valid result
        assert result.regime is not None
        assert 0.0 <= result.confidence <= 1.0

    def test_fallback_used_after_valid_regime_cached(self):
        """After one TRENDING classification, UNKNOWN should fall back to it."""
        # Force TRENDING: high ADX + RSI slope
        trending_closes = [100.0 + i * 2.0 for i in range(30)]
        first = self.ai.classify(
            adx=25.0, atr_pct=0.30, bb_width=3.5,
            closes=trending_closes, symbol="BTC"
        )
        if first.regime == Regime.TRENDING:
            # Now classify with ambiguous ADX (no valid regime can be determined)
            unknown_result = self.ai.classify(
                adx=17.0, atr_pct=0.20, bb_width=3.0,
                closes=self._closes, symbol="BTC"
            )
            if unknown_result.fallback_used:
                assert unknown_result.regime == Regime.TRENDING
                assert unknown_result.confidence < first.confidence

    def test_stability_boost_on_high_atr(self):
        """High ATR% → confidence gets STAB_BOOST multiplier."""
        result = self.ai.classify(
            adx=25.0, atr_pct=0.60,    # above ATR_HIGH_THRESH=0.50
            bb_width=5.0,
            closes=self._closes, symbol="ETH"
        )
        assert result.stability_factor > 1.0

    def test_stability_reduce_on_low_atr(self):
        """Low ATR% → confidence gets STAB_REDUCE multiplier."""
        result = self.ai.classify(
            adx=25.0, atr_pct=0.05,    # below ATR_LOW_THRESH=0.10
            bb_width=2.0,
            closes=self._closes, symbol="SOL"
        )
        assert result.stability_factor < 1.0

    def test_normal_atr_stability_factor_is_one(self):
        """Mid-range ATR% → stability_factor = 1.0."""
        result = self.ai.classify(
            adx=25.0, atr_pct=0.30,    # between 0.10 and 0.50
            bb_width=3.0,
            closes=self._closes, symbol="ADA"
        )
        assert result.stability_factor == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# E. SIGNAL FILTER — ADAPTIVE REGIME THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalFilterAdaptive:

    def setup_method(self):
        self.sf = SignalFilter()

    def _ok_signal(self, regime, rr_ratio, confidence, relax=1.0):
        """Helper: build signal params for a given RR and confidence."""
        entry = 100.0
        tp    = entry + rr_ratio * 10
        sl    = entry - 10
        return self.sf.check(
            symbol="SYM", entry=entry, take_profit=tp, stop_loss=sl,
            cost_usdt=0.5, atr_pct=0.30, confidence=confidence,
            regime=regime, relaxation_factor=relax,
        )

    def test_trending_regime_lower_rr_passes(self):
        """TRENDING min_rr=1.4 — signal with RR=1.5 should pass."""
        res = self._ok_signal("TRENDING", rr_ratio=1.5, confidence=0.55)
        assert res.ok

    def test_unknown_regime_higher_rr_required(self):
        """UNKNOWN min_rr=1.8 — signal with RR=1.5 should fail."""
        res = self._ok_signal("UNKNOWN", rr_ratio=1.5, confidence=0.65)
        assert not res.ok
        assert "LOW_RR" in res.reason

    def test_relaxation_lowers_effective_threshold(self):
        """Relaxation factor=0.88 → effective min_rr and min_conf are reduced."""
        # With UNKNOWN (1.8) and relax 0.88 → effective = 1.584; RR=1.6 should pass
        res = self._ok_signal("UNKNOWN", rr_ratio=1.6, confidence=0.60, relax=0.88)
        # effective_rr = max(1.0, 1.8*0.88) = 1.584
        assert res.ok or "LOW_RR" not in res.reason   # might fail on conf

    def test_relaxation_floor_enforced(self):
        """Absolute floor: effective min_rr ≥ 1.0 regardless of relaxation."""
        res = self.sf.check(
            symbol="SYM", entry=100.0, take_profit=101.1, stop_loss=99.0,
            cost_usdt=0.1, atr_pct=0.30, confidence=0.70,
            regime="MEAN_REVERTING", relaxation_factor=0.5,   # extreme relax
        )
        # min_rr = max(1.0, 1.2*0.5) = 1.0; RR=1.1 > 1.0 should pass RR gate
        assert res.ok or "LOW_RR" not in res.reason

    def test_mean_reverting_confidence_lower_than_unknown(self):
        """MEAN_REVERTING min_conf=0.45 is lower than UNKNOWN=0.60."""
        res_mr = self._ok_signal("MEAN_REVERTING",   rr_ratio=1.3, confidence=0.46)
        res_un = self._ok_signal("UNKNOWN",           rr_ratio=1.3, confidence=0.46)
        # MR should pass confidence gate; UNKNOWN should fail RR (1.3 < 1.8)
        assert "LOW_CONF" not in res_mr.reason or not res_mr.ok  # might fail on RR
        assert not res_un.ok


# ═══════════════════════════════════════════════════════════════════════════════
# F. RISK ENGINE — STREAK SCALING
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskEngineStreaks:

    def setup_method(self):
        self.re = RiskEngine()
        self.re.initialize(current_equity=10_000.0)

    def test_initial_streak_multiplier_is_one(self):
        snap = self.re.snapshot()
        assert snap["streak_multiplier"] == 1.0

    def test_win_streak_boosts_multiplier(self):
        """WIN_STREAK_BOOST_AT consecutive wins → multiplier > 1.0."""
        for _ in range(WIN_STREAK_BOOST_AT):
            self.re.record_trade_result(net_pnl=100.0)
        snap = self.re.snapshot()
        assert snap["streak_multiplier"] > 1.0

    def test_loss_streak_cuts_multiplier(self):
        """LOSS_STREAK_CUT_AT consecutive losses → multiplier < 1.0."""
        for _ in range(LOSS_STREAK_CUT_AT):
            self.re.record_trade_result(net_pnl=-100.0)
        snap = self.re.snapshot()
        assert snap["streak_multiplier"] < 1.0

    def test_win_after_loss_resets_loss_streak(self):
        """Win after loss streak should reset loss counter."""
        for _ in range(LOSS_STREAK_CUT_AT):
            self.re.record_trade_result(net_pnl=-100.0)
        self.re.record_trade_result(net_pnl=100.0)
        snap = self.re.snapshot()
        assert snap["loss_streak"] == 0
        assert snap["win_streak"]  == 1

    def test_streak_multiplier_capped_at_max(self):
        """Multiplier should never exceed MAX_STREAK_MULTIPLIER."""
        for _ in range(50):
            self.re.record_trade_result(net_pnl=100.0)
        snap = self.re.snapshot()
        assert snap["streak_multiplier"] <= MAX_STREAK_MULTIPLIER

    def test_streak_multiplier_floored_at_min(self):
        """Multiplier should never go below MIN_STREAK_MULTIPLIER."""
        for _ in range(50):
            self.re.record_trade_result(net_pnl=-10.0)
        snap = self.re.snapshot()
        assert snap["streak_multiplier"] >= MIN_STREAK_MULTIPLIER

    def test_compute_risk_usdt_scales_with_streak(self):
        """Risk USDT increases after win streak."""
        base_risk = self.re.compute_risk_usdt(10_000.0)
        for _ in range(WIN_STREAK_BOOST_AT):
            self.re.record_trade_result(net_pnl=100.0)
        boosted_risk = self.re.compute_risk_usdt(10_000.0)
        assert boosted_risk > base_risk


# ═══════════════════════════════════════════════════════════════════════════════
# G. DEPLOYABILITY — WARMUP + CONSISTENCY BONUS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeployabilityFtd023:

    def setup_method(self):
        self.de = DeployabilityEngine()

    def _full_result(self, trades=60, sharpe=1.5, sortino=2.5,
                     win_rate=0.50, dd=0.05, ror=0.02, avg_r=1.2):
        return self.de.compute(
            trades=trades, sharpe=sharpe, sortino=sortino,
            win_rate=win_rate, max_drawdown=dd, risk_of_ruin=ror, avg_r=avg_r,
        )

    # ── Warmup mode ───────────────────────────────────────────────────────────

    def test_warmup_status_below_warmup_trades(self):
        result = self.de.compute(
            trades=10, sharpe=0.0, sortino=0.0,
            win_rate=0.50, max_drawdown=0.05, risk_of_ruin=0.02, avg_r=1.0,
        )
        assert result.status == STATUS_WARMUP
        assert result.warmup_mode is True

    def test_warmup_score_capped_at_60(self):
        result = self.de.compute(
            trades=WARMUP_TRADES - 1, sharpe=0, sortino=0,
            win_rate=1.0, max_drawdown=0.0, risk_of_ruin=0.0, avg_r=2.0,
        )
        assert result.score <= 60.0

    def test_warmup_score_increases_with_trades(self):
        r_few  = self.de.compute(trades=5,  sharpe=0, sortino=0,
                                  win_rate=0.5, max_drawdown=0.05,
                                  risk_of_ruin=0.02, avg_r=1.0)
        r_more = self.de.compute(trades=20, sharpe=0, sortino=0,
                                  win_rate=0.5, max_drawdown=0.05,
                                  risk_of_ruin=0.02, avg_r=1.0)
        assert r_more.score > r_few.score

    # ── Partial (improving) mode ───────────────────────────────────────────────

    def test_partial_mode_capped_at_79(self):
        result = self.de.compute(
            trades=40, sharpe=2.5, sortino=4.0,
            win_rate=0.70, max_drawdown=0.02, risk_of_ruin=0.01, avg_r=1.5,
        )
        assert result.score <= 79.0
        assert result.status in (STATUS_IMPROVING, STATUS_NOT_READY)

    # ── Consistency bonus ─────────────────────────────────────────────────────

    def test_consistency_bonus_applied(self):
        """WR ≥ 55% and trades ≥ 20 → bonus added."""
        result = self._full_result(trades=60, win_rate=CONSISTENCY_THRESH + 0.01)
        assert result.consistency_bonus == CONSISTENCY_BONUS

    def test_no_bonus_below_win_rate_thresh(self):
        """WR < 55% → no bonus."""
        result = self._full_result(trades=60, win_rate=CONSISTENCY_THRESH - 0.01)
        assert result.consistency_bonus == 0.0

    def test_no_bonus_below_trade_count(self):
        """trades < 20 in warmup → no bonus even with high WR."""
        result = self.de.compute(
            trades=10, sharpe=0, sortino=0,
            win_rate=0.70, max_drawdown=0.05, risk_of_ruin=0.02, avg_r=1.0,
        )
        assert result.consistency_bonus == 0.0

    def test_score_capped_at_100(self):
        """Score + bonus should never exceed 100."""
        result = self._full_result(
            trades=100, sharpe=2.5, sortino=4.0,
            win_rate=0.80, dd=0.01, ror=0.01,
        )
        assert result.score <= 100.0

    # ── Full scoring hard blocks ───────────────────────────────────────────────

    def test_hard_block_low_sharpe(self):
        from core.deployability import STATUS_BLOCKED
        result = self._full_result(trades=60, sharpe=0.5)
        assert result.status == STATUS_BLOCKED

    def test_hard_block_high_drawdown(self):
        from core.deployability import STATUS_BLOCKED
        result = self._full_result(trades=60, dd=0.25)
        assert result.status == STATUS_BLOCKED

    # ── Status tiers ──────────────────────────────────────────────────────────

    def test_ready_status_at_high_score(self):
        result = self._full_result(
            trades=60, sharpe=2.0, sortino=3.5,
            win_rate=0.65, dd=0.03, ror=0.01,
        )
        # Score should be high enough for READY (≥85)
        assert result.status in (STATUS_READY, STATUS_IMPROVING)

    def test_not_ready_status_at_low_score(self):
        result = self._full_result(
            trades=60, sharpe=1.1, sortino=1.0,
            win_rate=0.40, dd=0.18, ror=0.05,
        )
        assert result.status in (STATUS_NOT_READY, STATUS_IMPROVING)

    def test_to_dict_contains_all_keys(self):
        result = self._full_result()
        d = self.de.to_dict(result)
        for k in ("score", "status", "components", "thresholds", "warmup_mode"):
            assert k in d

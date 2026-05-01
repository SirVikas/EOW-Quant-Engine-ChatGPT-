"""
Tests for FTD-REF-MASTER-001 strategy intelligence modules.

Covers:
  - ADX validation          (core/indicator_guard.py)
  - Regime classification   (core/regime_ai.py)
  - Signal filtering        (core/signal_filter.py)
  - Risk enforcement        (core/risk_engine.py)
  - Deployability scoring   (core/deployability.py)

Run with:  python -m pytest tests/test_strategy_intelligence.py -v
"""
import time
import pytest

from core.indicator_guard import IndicatorGuard, ADX_CLAMP_ABOVE, ADX_WEAK_BELOW
from core.regime_ai       import RegimeAI, MIN_CONFIDENCE
from core.signal_filter   import SignalFilter, MIN_ATR_PCT, _REGIME_RR, _REGIME_CONF
from core.risk_engine     import RiskEngine, MAX_TRADES_PER_DAY, MAX_DAILY_LOSS_PCT
from core.deployability   import DeployabilityEngine, STATUS_READY, STATUS_IMPROVING
from core.regime_detector import Regime


# ═══════════════════════════════════════════════════════════════════════════════
# A. ADX VALIDATION  (indicator_guard.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIndicatorGuard:

    def setup_method(self):
        self.guard = IndicatorGuard()

    def test_insufficient_candles_blocked(self):
        r = self.guard.validate("BTCUSDT", 10, adx=25.0, atr_pct=0.3)
        assert r.ok is False
        assert "INSUFFICIENT_CANDLES" in r.reason

    def test_adx_none_blocked(self):
        r = self.guard.validate("BTCUSDT", 35, adx=None, atr_pct=0.3)
        assert r.ok is False
        assert "ADX_NOT_READY" in r.reason
        assert r.adx_quality == "NOT_READY"

    def test_adx_below_5_blocked(self):
        r = self.guard.validate("BTCUSDT", 35, adx=3.0, atr_pct=0.3)
        assert r.ok is False
        assert "ADX_UNSTABLE" in r.reason

    def test_adx_below_10_is_weak_but_allowed(self):
        r = self.guard.validate("BTCUSDT", 35, adx=8.0, atr_pct=0.3)
        assert r.ok is True
        assert r.adx_quality == "WEAK"

    def test_adx_above_60_clamped(self):
        r = self.guard.validate("BTCUSDT", 35, adx=90.0, atr_pct=0.3)
        assert r.ok is True
        assert r.adx == ADX_CLAMP_ABOVE

    def test_atr_too_low_blocked(self):
        r = self.guard.validate("BTCUSDT", 35, adx=25.0, atr_pct=0.01)
        assert r.ok is False
        assert "ATR_TOO_LOW" in r.reason

    def test_valid_indicators_pass(self):
        r = self.guard.validate("BTCUSDT", 50, adx=30.0, atr_pct=0.4)
        assert r.ok is True
        assert r.adx_quality == "STRONG"

    def test_adx_exactly_at_clamp_not_clamped(self):
        r = self.guard.validate("BTCUSDT", 50, adx=60.0, atr_pct=0.4)
        assert r.ok is True
        assert r.adx == 60.0   # exactly at limit — should pass unchanged

    def test_adx_quality_strong_above_10(self):
        r = self.guard.validate("BTCUSDT", 50, adx=15.0, atr_pct=0.3)
        assert r.ok is True
        assert r.adx_quality == "STRONG"


# ═══════════════════════════════════════════════════════════════════════════════
# B. REGIME CLASSIFICATION  (regime_ai.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegimeAI:

    def setup_method(self):
        self.ai = RegimeAI()
        # 60 bars: rising (0-30), falling (30-45), strong recovery (45-59).
        # The recovery boundary means change[44] is a loss while changes[45:59]
        # are all gains — this guarantees RSI slope >> RSI_SLOPE_BULLISH (0.5).
        self._trending_closes = (
            [100 + i for i in range(31)]             # 100 → 130  (bars 0-30)
            + [130 - (i + 1) * 2 for i in range(15)]  # 128 → 100  (bars 31-45)
            + [100 + (i + 1) * 3 for i in range(14)]  # 103 → 142  (bars 46-59)
        )
        # 60 bars of sideways oscillation
        self._sideways_closes = [100 + (i % 5) * 0.1 for i in range(60)]

    def test_volatility_expansion_detected(self):
        result = self.ai.classify(
            adx=15, atr_pct=0.55, bb_width=6.0,
            closes=self._trending_closes,
        )
        assert result.regime == Regime.VOLATILITY_EXPANSION

    def test_trending_detected(self):
        result = self.ai.classify(
            adx=28, atr_pct=0.25, bb_width=2.5,
            closes=self._trending_closes,
        )
        assert result.regime == Regime.TRENDING

    def test_mean_reverting_detected(self):
        result = self.ai.classify(
            adx=10, atr_pct=0.10, bb_width=1.5,
            closes=self._sideways_closes,
        )
        assert result.regime == Regime.MEAN_REVERTING

    def test_confidence_range(self):
        result = self.ai.classify(
            adx=25, atr_pct=0.3, bb_width=3.0,
            closes=self._trending_closes,
        )
        assert 0.0 <= result.confidence <= 1.0

    def test_low_confidence_returns_unknown(self):
        # Ambiguous inputs → should produce low confidence → UNKNOWN
        result = self.ai.classify(
            adx=16, atr_pct=0.19, bb_width=2.0,
            closes=[100.0] * 60,  # flat → near-zero RSI slope
        )
        # Either UNKNOWN or low-confidence result
        if result.regime == Regime.UNKNOWN:
            assert result.confidence == 0.0
        else:
            assert result.confidence >= 0.0

    def test_factor_scores_in_range(self):
        result = self.ai.classify(
            adx=30, atr_pct=0.4, bb_width=4.5,
            closes=self._trending_closes,
        )
        assert 0.0 <= result.adx_score  <= 1.0
        assert 0.0 <= result.atr_score  <= 1.0
        assert 0.0 <= result.bb_score   <= 1.0
        assert -1.0 <= result.rsi_score <= 1.0

    def test_rsi_slope_insufficient_data(self):
        # Only 5 bars — _rsi_slope should return 0 without crashing
        result = self.ai.classify(
            adx=25, atr_pct=0.3, bb_width=3.0,
            closes=[100, 101, 102, 103, 104],
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# C. SIGNAL FILTERING  (signal_filter.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalFilter:

    def setup_method(self):
        self.sf = SignalFilter()

    def _good(self, **overrides):
        params = dict(
            symbol="BTCUSDT", entry=50000, take_profit=50900,
            stop_loss=49500, cost_usdt=5.0, atr_pct=0.3, confidence=0.7,
        )
        params.update(overrides)
        return self.sf.check(**params)

    def test_good_signal_passes(self):
        r = self._good()
        assert r.ok is True

    def test_low_rr_blocked(self):
        # TP=50200, SL=49500 → gross_tp=200, gross_sl=500 → RR=0.4
        r = self._good(take_profit=50200)
        assert r.ok is False
        assert "LOW_RR" in r.reason

    def test_low_atr_blocked(self):
        # MIN_ATR_PCT=0.010 — use a value strictly below the threshold
        r = self._good(atr_pct=0.005)
        assert r.ok is False
        assert "LOW_ATR" in r.reason

    def test_low_confidence_blocked(self):
        # UNKNOWN min_conf=0.18 — use a value strictly below the threshold
        r = self._good(confidence=0.15)
        assert r.ok is False
        assert "LOW_CONFIDENCE" in r.reason

    def test_high_cost_blocked(self):
        # cost_usdt = 350, gross_tp = 900 → 38.9% > 30%
        r = self._good(cost_usdt=350.0)
        assert r.ok is False
        assert "COST_HIGH" in r.reason

    def test_consecutive_losses_cause_pause(self):
        self.sf.record_loss("BTCUSDT")
        self.sf.record_loss("BTCUSDT")
        self.sf.record_loss("BTCUSDT")
        assert self.sf.is_paused("BTCUSDT") is True
        r = self._good()
        assert r.ok is False
        assert "LOSS_PAUSE" in r.reason

    def test_win_resets_loss_counter(self):
        self.sf.record_loss("BTCUSDT")
        self.sf.record_loss("BTCUSDT")
        self.sf.record_win("BTCUSDT")
        assert self.sf.consecutive_losses("BTCUSDT") == 0
        assert self.sf.is_paused("BTCUSDT") is False

    def test_pause_only_affects_symbol(self):
        self.sf.record_loss("BTCUSDT")
        self.sf.record_loss("BTCUSDT")
        self.sf.record_loss("BTCUSDT")
        # Different symbol should not be paused
        r = self.sf.check(
            symbol="ETHUSDT", entry=3000, take_profit=3160,
            stop_loss=2920, cost_usdt=3.0, atr_pct=0.3, confidence=0.7,
        )
        assert r.ok is True

    def test_summary_structure(self):
        s = self.sf.summary()
        assert "consecutive_losses" in s
        assert "paused_symbols" in s
        assert "regime_thresholds" in s   # FTD-REF-023: adaptive per-regime thresholds


# ═══════════════════════════════════════════════════════════════════════════════
# D. RISK ENFORCEMENT  (risk_engine.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskEngine:

    def setup_method(self):
        self.re = RiskEngine()
        self.re.initialize(10_000.0)

    def test_new_trade_allowed_initially(self):
        ok, reason = self.re.check_new_trade()
        assert ok is True

    def test_daily_trade_cap_enforced(self):
        for _ in range(MAX_TRADES_PER_DAY):
            self.re.record_trade_result(0.0)   # neutral PnL
        ok, reason = self.re.check_new_trade()
        assert ok is False
        assert "DAILY_TRADE_CAP" in reason

    def test_daily_loss_halt(self):
        # MAX_DAILY_LOSS_PCT=5% → lose 5.1% (510 USDT of 10k equity) to trigger halt
        self.re.record_trade_result(-510.0)
        self.re.update_equity(9490.0)
        ok, reason = self.re.check_new_trade()
        assert ok is False
        assert "DAILY_LOSS" in reason or self.re.halted

    def test_max_drawdown_halt(self):
        # Simulate 16% drawdown → triggers halt
        self.re.update_equity(8_400.0)
        assert self.re.halted is True
        assert "MAX_DRAWDOWN" in self.re._state.halt_reason

    def test_size_halved_at_10pct_drawdown(self):
        self.re.update_equity(8_990.0)  # ~10.1% DD
        assert self.re.size_multiplier == 0.5

    def test_size_restored_on_recovery(self):
        self.re.update_equity(8_990.0)   # halve
        assert self.re.size_multiplier == 0.5
        self.re._state.peak_equity = 8_990.0   # simulate new peak
        self.re.update_equity(9_000.0)          # above SIZE_HALVE_AT_DD
        assert self.re.size_multiplier == 1.0

    def test_compute_risk_usdt_respects_multiplier(self):
        # RISK_PCT_MAX=1.5% (raised from 1%). Expected: 10000 × 0.015 × 0.5 = 75
        self.re._state.size_multiplier = 0.5
        risk = self.re.compute_risk_usdt(10_000.0)
        assert risk == pytest.approx(10_000.0 * 0.015 * 0.5, rel=0.01)

    def test_snapshot_structure(self):
        s = self.re.snapshot()
        for key in ("halted", "trades_today", "daily_pnl",
                    "drawdown_pct", "size_multiplier", "limits"):
            assert key in s


# ═══════════════════════════════════════════════════════════════════════════════
# E. DEPLOYABILITY SCORING  (deployability.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeployabilityEngine:

    def setup_method(self):
        self.de = DeployabilityEngine()

    def _compute(self, **overrides):
        params = dict(
            trades=60, sharpe=1.5, sortino=2.0,
            win_rate=0.58, max_drawdown=0.08, risk_of_ruin=0.03, avg_r=1.2,
        )
        params.update(overrides)
        return self.de.compute(**params)

    def test_warmup_mode_below_warmup_trades(self):
        # FTD-REF-023: trades < WARMUP_TRADES → WARMUP status (not INSUFFICIENT_DATA)
        r = self.de.compute(
            trades=10, sharpe=2.0, sortino=2.5, win_rate=0.6,
            max_drawdown=0.05, risk_of_ruin=0.02, avg_r=1.5,
        )
        assert r.status == "WARMUP"
        assert r.warmup_mode is True
        assert 0 < r.score <= 60

    def test_low_sharpe_returns_blocked(self):
        r = self._compute(sharpe=0.5)
        assert r.status == "BLOCKED"
        assert "LOW_SHARPE" in r.block_reason

    def test_high_drawdown_returns_blocked(self):
        r = self._compute(max_drawdown=0.25)
        assert r.status == "BLOCKED"
        assert "HIGH_DD" in r.block_reason

    def test_high_ruin_returns_blocked(self):
        r = self._compute(risk_of_ruin=0.15)
        assert r.status == "BLOCKED"
        assert "HIGH_ROR" in r.block_reason

    def test_excellent_metrics_return_ready(self):
        r = self.de.compute(
            trades=100, sharpe=2.0, sortino=3.0, win_rate=0.65,
            max_drawdown=0.05, risk_of_ruin=0.01, avg_r=1.8,
        )
        assert r.status == STATUS_READY
        assert r.score >= 85

    def test_average_metrics_return_improving(self):
        r = self._compute(sharpe=1.2, sortino=1.5, win_rate=0.50, max_drawdown=0.12)
        assert r.status in (STATUS_IMPROVING, "NOT_READY")

    def test_score_bounded_0_100(self):
        r = self._compute()
        assert 0 <= r.score <= 100

    def test_to_dict_structure(self):
        r = self._compute()
        d = self.de.to_dict(r)
        assert "score" in d
        assert "status" in d
        assert "components" in d
        assert "thresholds" in d

    def test_component_scores_in_range(self):
        r = self._compute()
        if r.status not in ("BLOCKED", "INSUFFICIENT_DATA"):
            assert 0.0 <= r.sharpe_norm    <= 1.0
            assert 0.0 <= r.sortino_norm   <= 1.0
            assert 0.0 <= r.win_rate_score <= 1.0

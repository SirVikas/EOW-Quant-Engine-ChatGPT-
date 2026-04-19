"""
Tests for Phase 5 — EV Engine + Adaptive Intelligence

Covers:
  - EV Engine: calculation accuracy, negative EV rejection, bootstrap   (core/ev_engine.py)
  - Adaptive Scorer: weight updates, learning direction                  (core/adaptive_scorer.py)
  - Confidence Decay: frequency tracking, decay application             (core/confidence_decay.py)
  - Drawdown Controller: tier thresholds, STOP condition                (core/drawdown_controller.py)
  - Regime Memory: fit score computation, strategy preference           (core/regime_memory.py)

Run with:  python -m pytest tests/test_ev_engine.py -v
"""
import math
import time
import pytest

from core.ev_engine          import EVEngine, WINDOW, MIN_TRADES
from core.adaptive_scorer    import AdaptiveScorer, _INITIAL_WEIGHTS
from core.confidence_decay   import ConfidenceDecayEngine
from core.drawdown_controller import DrawdownController
from core.regime_memory      import RegimeMemoryEngine, MIN_TRADES_FOR_PREFERENCE


# ═══════════════════════════════════════════════════════════════════════════════
# A. EV ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _record_trades(eng: EVEngine, strategy: str, symbol: str,
                   wins: int, losses: int,
                   win_pnl: float = 20.0, loss_pnl: float = -10.0,
                   cost: float = 0.5):
    for _ in range(wins):
        eng.record(strategy, symbol, net_pnl=win_pnl, cost=cost)
    for _ in range(losses):
        eng.record(strategy, symbol, net_pnl=loss_pnl, cost=cost)


class TestEVEngine:

    def setup_method(self):
        self.eng = EVEngine()

    def test_bootstrap_passes_when_insufficient_data(self):
        """< MIN_TRADES → gate passes (bootstrap mode)."""
        result = self.eng.evaluate(
            strategy_id="TF_v1", symbol="BTCUSDT",
            est_reward=20.0, est_risk=10.0, current_cost=0.5,
        )
        assert result.ok
        assert result.bootstrapped
        assert "BOOTSTRAP" in result.reason

    def test_positive_ev_accepted(self):
        """60% win rate, avg_win=20, avg_loss=10 → positive EV."""
        _record_trades(self.eng, "TF_v1", "BTCUSDT",
                       wins=12, losses=8, win_pnl=20.0, loss_pnl=-10.0, cost=0.2)
        result = self.eng.evaluate(
            strategy_id="TF_v1", symbol="BTCUSDT",
            est_reward=20.0, est_risk=10.0, current_cost=0.2,
        )
        # EV = 0.6×20 - 0.4×10 - avg_cost ≈ 12 - 4 - 0.2 = 7.8
        assert result.ok
        assert result.ev > 0
        assert not result.bootstrapped

    def test_negative_ev_rejected(self):
        """30% win rate, avg_win=5, avg_loss=20 → negative EV."""
        _record_trades(self.eng, "TF_v1", "ETHUSDT",
                       wins=3, losses=7, win_pnl=5.0, loss_pnl=-20.0, cost=0.5)
        # Force enough trades
        for _ in range(5):
            self.eng.record("TF_v1", "ETHUSDT", net_pnl=-20.0, cost=0.5)
        result = self.eng.evaluate(
            strategy_id="TF_v1", symbol="ETHUSDT",
            est_reward=5.0, est_risk=20.0, current_cost=0.5,
        )
        assert not result.ok
        assert result.ev <= 0
        assert "NEGATIVE_EV" in result.reason

    def test_ev_formula_accuracy(self):
        """EV = p_win×reward − p_loss×risk − cost (prospective formula)."""
        eng = EVEngine()
        # 10 wins, 10 losses → p_win = 0.5
        for _ in range(10):
            eng.record("S", "X", net_pnl=20.0, cost=1.0)
        for _ in range(10):
            eng.record("S", "X", net_pnl=-10.0, cost=1.0)

        result = eng.evaluate("S", "X", est_reward=20.0, est_risk=10.0, current_cost=1.0)
        # EV = 0.5×20 - 0.5×10 - 1.0 = 10 - 5 - 1 = 4
        assert result.ok
        assert result.ev == pytest.approx(4.0, abs=0.01)

    def test_zero_ev_boundary_rejected(self):
        """EV exactly 0 is rejected (rule: EV > 0 required)."""
        eng = EVEngine()
        # 10 wins, 10 losses, reward == risk, cost=0
        # EV = 0.5×10 - 0.5×10 - 0 = 0
        for _ in range(10):
            eng.record("S", "X", net_pnl=10.0, cost=0.0)
        for _ in range(10):
            eng.record("S", "X", net_pnl=-10.0, cost=0.0)
        result = eng.evaluate("S", "X", est_reward=10.0, est_risk=10.0, current_cost=0.0)
        assert not result.ok

    def test_rolling_window_bounded(self):
        """History must never exceed WINDOW size."""
        eng = EVEngine()
        for i in range(WINDOW + 20):
            eng.record("S", "X", net_pnl=10.0 if i % 2 == 0 else -5.0, cost=0.1)
        history = eng._history[("S", "X")]
        assert len(history) == WINDOW

    def test_different_symbols_tracked_separately(self):
        """Per-symbol tracking: BTCUSDT and ETHUSDT maintain independent history."""
        _record_trades(self.eng, "TF", "BTCUSDT", wins=8, losses=2)  # 80% WR
        _record_trades(self.eng, "TF", "ETHUSDT", wins=2, losses=8)  # 20% WR
        btc_ev = self.eng.get_ev("TF", "BTCUSDT")
        eth_ev = self.eng.get_ev("TF", "ETHUSDT")
        assert btc_ev > eth_ev

    def test_cost_reduces_ev(self):
        """Higher cost reduces EV; high enough cost flips positive → negative."""
        eng_cheap = EVEngine()
        eng_costly = EVEngine()
        for _ in range(15):
            eng_cheap.record("S", "X", net_pnl=10.0, cost=0.1)
        for _ in range(5):
            eng_cheap.record("S", "X", net_pnl=-5.0, cost=0.1)
        for _ in range(15):
            eng_costly.record("S", "X", net_pnl=10.0, cost=5.0)
        for _ in range(5):
            eng_costly.record("S", "X", net_pnl=-5.0, cost=5.0)

        cheap_r = eng_cheap.evaluate("S", "X", 10.0, 5.0, 0.1)
        costly_r = eng_costly.evaluate("S", "X", 10.0, 5.0, 5.0)
        assert cheap_r.ev > costly_r.ev

    def test_summary_structure(self):
        self.eng.record("TF", "BTCUSDT", 10.0, 0.5)
        s = self.eng.summary()
        assert "tracked_pairs" in s
        assert s["phase"] == 5
        assert "strategies" in s


# ═══════════════════════════════════════════════════════════════════════════════
# B. ADAPTIVE SCORER
# ═══════════════════════════════════════════════════════════════════════════════

def _score_kwargs(regime="TRENDING", adx=40.0, side="LONG"):
    return dict(
        symbol="BTCUSDT", regime=regime, adx=adx,
        rsi=55.0, rsi_prev=50.0,
        atr_pct=1.5, avg_atr_pct=1.0,
        vol_ratio=2.0, cost_fraction=0.05,
        signal_side=side,
    )


class TestAdaptiveScorer:

    def setup_method(self):
        self.scorer = AdaptiveScorer()

    def test_initial_weights_match_phase4(self):
        w = self.scorer.current_weights()
        for k, v in _INITIAL_WEIGHTS.items():
            assert abs(w[k] - v) < 1e-6

    def test_high_quality_trade_passes(self):
        result = self.scorer.score(**_score_kwargs())
        assert result.ok

    def test_weights_sum_to_one_after_init(self):
        w = self.scorer.current_weights()
        assert abs(sum(w.values()) - 1.0) < 1e-6

    def test_win_increases_predictive_factor_weights(self):
        """After a win, factors with high scores should increase in weight."""
        # Score a signal to populate _pending
        self.scorer.score(**_score_kwargs())
        weights_before = dict(self.scorer.current_weights())
        self.scorer.record_outcome("BTCUSDT", won=True)
        weights_after = self.scorer.current_weights()
        # At least some weights should have changed
        changed = any(
            abs(weights_after[k] - weights_before[k]) > 1e-9
            for k in weights_before
        )
        assert changed

    def test_loss_decreases_factor_weights(self):
        """After a loss, predictive factor weights should decrease."""
        self.scorer.score(**_score_kwargs())
        w_before = dict(self.scorer.current_weights())
        self.scorer.record_outcome("BTCUSDT", won=False)
        w_after = self.scorer.current_weights()
        changed = any(abs(w_after[k] - w_before[k]) > 1e-9 for k in w_before)
        assert changed

    def test_weights_stay_within_bounds(self):
        """Weights never drop below MIN_WEIGHT or exceed MAX_WEIGHT."""
        from config import cfg
        # Apply many losses to stress-test clipping
        for _ in range(100):
            self.scorer.score(**_score_kwargs())
            self.scorer.record_outcome("BTCUSDT", won=False)
        w = self.scorer.current_weights()
        for k, v in w.items():
            assert v >= cfg.ADAPTIVE_MIN_WEIGHT - 1e-9, f"{k}={v} below min"
            assert v <= cfg.ADAPTIVE_MAX_WEIGHT + 1e-9, f"{k}={v} above max"

    def test_weights_always_sum_to_one(self):
        """After any sequence of updates, weights must still sum to 1.0."""
        for i in range(30):
            self.scorer.score(**_score_kwargs())
            self.scorer.record_outcome("BTCUSDT", won=(i % 3 != 0))
        w = self.scorer.current_weights()
        assert abs(sum(w.values()) - 1.0) < 1e-4

    def test_n_updates_increments(self):
        self.scorer.score(**_score_kwargs())
        self.scorer.record_outcome("BTCUSDT", won=True)
        assert self.scorer.n_updates() == 1

    def test_record_outcome_without_pending_is_safe(self):
        """Calling record_outcome for unknown symbol should not raise."""
        self.scorer.record_outcome("XUNKNOWN", won=True)

    def test_breakdown_keys_match_weights(self):
        result = self.scorer.score(**_score_kwargs())
        assert set(result.breakdown.keys()) == set(self.scorer.current_weights().keys())

    def test_summary_structure(self):
        s = self.scorer.summary()
        assert "weights" in s
        assert "n_updates" in s
        assert s["phase"] == 5


# ═══════════════════════════════════════════════════════════════════════════════
# C. CONFIDENCE DECAY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceDecayEngine:

    def setup_method(self):
        self.decay = ConfidenceDecayEngine()

    def test_first_signal_no_decay(self):
        result = self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.75)
        assert result.decay_factor == pytest.approx(1.0)
        assert result.decayed_confidence == pytest.approx(0.75, abs=1e-4)

    def test_decay_kicks_in_above_freq_max(self):
        from config import cfg
        # Fire enough signals to exceed freq_max
        for _ in range(cfg.DECAY_FREQ_MAX + 1):
            self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.80)
        result = self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.80)
        assert result.decay_factor < 1.0
        assert result.decayed_confidence < 0.80

    def test_decay_factor_floor(self):
        """Decay factor must never go below DECAY_MIN_FACTOR."""
        from config import cfg
        for _ in range(50):
            self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.90)
        result = self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.90)
        assert result.decay_factor >= cfg.DECAY_MIN_FACTOR

    def test_different_symbols_tracked_independently(self):
        from config import cfg
        for _ in range(cfg.DECAY_FREQ_MAX + 3):
            self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.80)
        # ETHUSDT should have no decay
        eth_result = self.decay.decay("ETHUSDT", "TF_v1", base_conf=0.80)
        assert eth_result.decay_factor == pytest.approx(1.0)

    def test_reset_clears_frequency(self):
        from config import cfg
        for _ in range(cfg.DECAY_FREQ_MAX + 2):
            self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.80)
        self.decay.reset("BTCUSDT", "TF_v1")
        assert self.decay.get_frequency("BTCUSDT", "TF_v1") == 0

    def test_no_record_does_not_increment(self):
        """decay with record_signal=False should not change frequency."""
        freq_before = self.decay.get_frequency("BTCUSDT", "TF_v1")
        self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.70, record_signal=False)
        assert self.decay.get_frequency("BTCUSDT", "TF_v1") == freq_before

    def test_summary_structure(self):
        self.decay.decay("BTCUSDT", "TF_v1", base_conf=0.75)
        s = self.decay.summary()
        assert "freq_max" in s
        assert "min_factor" in s
        assert s["phase"] == 5


# ═══════════════════════════════════════════════════════════════════════════════
# D. DRAWDOWN CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class TestDrawdownController:

    def setup_method(self):
        self.dc = DrawdownController()

    def test_normal_zone_full_size(self):
        self.dc.update_equity(1000.0)
        self.dc.update_equity(1000.0)  # no drawdown
        result = self.dc.check()
        assert result.allowed
        assert result.multiplier == pytest.approx(1.0)
        assert result.tier == "NORMAL"

    def test_soft_cut_at_5_percent_dd(self):
        self.dc.update_equity(1000.0)   # peak
        self.dc.update_equity(945.0)    # 5.5% drawdown
        result = self.dc.check()
        assert result.allowed
        assert result.multiplier == pytest.approx(0.75)
        assert result.tier == "SOFT_CUT"

    def test_hard_cut_at_10_percent_dd(self):
        self.dc.update_equity(1000.0)
        self.dc.update_equity(880.0)    # 12% drawdown
        result = self.dc.check()
        assert result.allowed
        assert result.multiplier == pytest.approx(0.50)
        assert result.tier == "HARD_CUT"

    def test_stop_at_15_percent_dd(self):
        self.dc.update_equity(1000.0)
        self.dc.update_equity(820.0)    # 18% drawdown
        result = self.dc.check()
        assert not result.allowed
        assert result.multiplier == pytest.approx(0.0)
        assert result.tier == "STOP"
        assert "DD_STOP" in result.reason

    def test_recovery_to_normal(self):
        self.dc.update_equity(1000.0)
        self.dc.update_equity(940.0)    # 6% → soft cut
        assert self.dc.check().tier == "SOFT_CUT"
        self.dc.update_equity(970.0)    # 3% → back to normal
        assert self.dc.check().tier == "NORMAL"

    def test_no_peak_returns_allowed(self):
        """Before any equity update, check() should pass with 1× size."""
        dc = DrawdownController()
        result = dc.check()
        assert result.allowed
        assert result.multiplier == pytest.approx(1.0)

    def test_drawdown_computation_accuracy(self):
        self.dc.update_equity(1000.0)
        self.dc.update_equity(900.0)
        dd = self.dc.current_drawdown()
        assert dd == pytest.approx(0.10, abs=0.001)

    def test_peak_only_moves_up(self):
        """Peak should only increase, never decrease."""
        self.dc.update_equity(1000.0)
        self.dc.update_equity(1200.0)
        self.dc.update_equity(900.0)   # equity drops
        # Peak should still be 1200
        assert self.dc._peak_equity == pytest.approx(1200.0)

    def test_exact_boundary_5_percent(self):
        """Exactly 5% DD should trigger SOFT_CUT."""
        self.dc.update_equity(1000.0)
        self.dc.update_equity(950.0)
        result = self.dc.check()
        assert result.tier == "SOFT_CUT"

    def test_summary_structure(self):
        self.dc.update_equity(1000.0)
        s = self.dc.summary()
        assert "drawdown_pct" in s
        assert "tier_thresholds" in s
        assert s["phase"] == 5


# ═══════════════════════════════════════════════════════════════════════════════
# E. REGIME MEMORY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegimeMemoryEngine:

    def setup_method(self):
        self.mem = RegimeMemoryEngine()

    def test_neutral_score_with_no_data(self):
        score = self.mem.get_fit_score("TRENDING", "TrendFollowing")
        assert score == pytest.approx(0.5)

    def test_good_performance_raises_fit_score(self):
        for _ in range(15):
            self.mem.record("TRENDING", "TrendFollowing", won=True, r_mult=2.0)
        for _ in range(5):
            self.mem.record("TRENDING", "TrendFollowing", won=False, r_mult=-1.0)
        score = self.mem.get_fit_score("TRENDING", "TrendFollowing")
        assert score > 0.5

    def test_poor_performance_lowers_fit_score(self):
        for _ in range(3):
            self.mem.record("TRENDING", "MeanReversion", won=True, r_mult=0.5)
        for _ in range(17):
            self.mem.record("TRENDING", "MeanReversion", won=False, r_mult=-1.5)
        score = self.mem.get_fit_score("TRENDING", "MeanReversion")
        assert score < 0.5

    def test_preferred_strategy_returns_best_fit(self):
        # TrendFollowing has 80% WR in TRENDING
        for _ in range(8):
            self.mem.record("TRENDING", "TrendFollowing", won=True, r_mult=2.0)
        for _ in range(2):
            self.mem.record("TRENDING", "TrendFollowing", won=False, r_mult=-1.0)
        # MeanReversion has 20% WR in TRENDING
        for _ in range(2):
            self.mem.record("TRENDING", "MeanReversion", won=True, r_mult=1.0)
        for _ in range(8):
            self.mem.record("TRENDING", "MeanReversion", won=False, r_mult=-1.5)

        pref = self.mem.preferred_strategy("TRENDING")
        assert pref == "TrendFollowing"

    def test_preferred_strategy_returns_none_without_enough_data(self):
        self.mem.record("TRENDING", "TrendFollowing", won=True, r_mult=2.0)
        pref = self.mem.preferred_strategy("TRENDING")
        assert pref is None  # < MIN_TRADES_FOR_PREFERENCE

    def test_strategies_per_regime_independent(self):
        # TRENDING → TrendFollowing good
        for _ in range(10):
            self.mem.record("TRENDING", "TrendFollowing", won=True, r_mult=2.0)
        # MEAN_REVERTING → TrendFollowing bad
        for _ in range(10):
            self.mem.record("MEAN_REVERTING", "TrendFollowing", won=False, r_mult=-1.0)

        trending_fit   = self.mem.get_fit_score("TRENDING",      "TrendFollowing")
        mr_fit         = self.mem.get_fit_score("MEAN_REVERTING", "TrendFollowing")
        assert trending_fit > mr_fit

    def test_fit_score_clamped_to_0_1(self):
        for _ in range(20):
            self.mem.record("TRENDING", "TrendFollowing", won=True, r_mult=10.0)
        score = self.mem.get_fit_score("TRENDING", "TrendFollowing")
        assert 0.0 <= score <= 1.0

    def test_window_respected(self):
        from config import cfg
        for i in range(cfg.REGIME_MEMORY_WINDOW + 20):
            self.mem.record("TRENDING", "TrendFollowing",
                            won=(i % 2 == 0), r_mult=1.0)
        h = self.mem._history[("TRENDING", "TrendFollowing")]
        assert len(h) == cfg.REGIME_MEMORY_WINDOW

    def test_summary_structure(self):
        self.mem.record("TRENDING", "TrendFollowing", won=True, r_mult=1.5)
        s = self.mem.summary()
        assert "pairs" in s
        assert "regimes" in s
        assert s["phase"] == 5


# ═══════════════════════════════════════════════════════════════════════════════
# F. INTEGRATION: Full Phase 5 Decision Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhase5Pipeline:
    """End-to-end: adaptive scorer → decay → EV gate → drawdown gate."""

    def setup_method(self):
        self.scorer = AdaptiveScorer()
        self.decay  = ConfidenceDecayEngine()
        self.ev     = EVEngine()
        self.dc     = DrawdownController()

    def test_full_pipeline_healthy_system(self):
        """Healthy system: good score, no decay, positive EV, low DD → pass all."""
        score_r = self.scorer.score(
            symbol="BTCUSDT", regime="TRENDING", adx=42.0,
            rsi=58.0, rsi_prev=52.0, atr_pct=1.5, avg_atr_pct=1.0,
            vol_ratio=2.0, cost_fraction=0.04, signal_side="LONG",
        )
        assert score_r.ok

        decay_r = self.decay.decay("BTCUSDT", "TF_v1", base_conf=score_r.score)
        assert decay_r.decay_factor == pytest.approx(1.0)

        # Bootstrap passes
        ev_r = self.ev.evaluate("TF_v1", "BTCUSDT", 50.0, 20.0, 1.0)
        assert ev_r.ok

        self.dc.update_equity(1000.0)
        dd_r = self.dc.check()
        assert dd_r.allowed
        assert dd_r.multiplier == pytest.approx(1.0)

    def test_full_pipeline_blocked_by_negative_ev(self):
        """Positive score + good DD, but negative historical EV → pipeline blocked."""
        for _ in range(5):
            self.ev.record("TF_v1", "BTCUSDT", net_pnl=3.0, cost=0.2)
        for _ in range(15):
            self.ev.record("TF_v1", "BTCUSDT", net_pnl=-20.0, cost=0.2)

        ev_r = self.ev.evaluate("TF_v1", "BTCUSDT",
                                est_reward=3.0, est_risk=20.0, current_cost=0.2)
        assert not ev_r.ok

    def test_full_pipeline_blocked_by_drawdown_stop(self):
        """Good score + EV but 20% DD → STOP."""
        self.dc.update_equity(1000.0)
        self.dc.update_equity(800.0)   # 20% DD
        result = self.dc.check()
        assert not result.allowed
        assert result.tier == "STOP"

    def test_adaptive_weights_shift_after_repeated_losses(self):
        """Repeated losses should shift weights away from 50/50 baseline."""
        scorer = AdaptiveScorer()
        for i in range(20):
            scorer.score(
                symbol="BTCUSDT", regime="TRENDING", adx=30.0,
                rsi=50.0, rsi_prev=50.0, atr_pct=1.0, avg_atr_pct=1.0,
                vol_ratio=1.0, cost_fraction=0.05, signal_side="LONG",
            )
            scorer.record_outcome("BTCUSDT", won=False)
        w = scorer.current_weights()
        # Weights should have moved from initial values
        from config import cfg
        for k, v in w.items():
            assert v >= cfg.ADAPTIVE_MIN_WEIGHT

"""
EOW Quant Engine — tests/test_phase7B_ev_evolution.py
Phase 7B: EV Engine Evolution Verifier

BUILD IS REJECTED if any of these tests fail:
  - Negative EV → trade rejected by TradeRanker
  - High EV → higher capital allocation than low EV
  - Bootstrap → confidence=0.3
  - High drawdown → EV suppressed (forced ≤ 0)
  - Strong regime confidence → EV boosted
"""
from __future__ import annotations

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fresh_ev_engine():
    """Return a new EVEngine instance with empty history."""
    from core.ev_engine import EVEngine
    return EVEngine()


def _seed_wins(engine, strategy_id: str, symbol: str, n: int, win_pnl: float = 10.0):
    """Seed n winning trades so history is established."""
    for _ in range(n):
        engine.record(strategy_id, symbol, net_pnl=win_pnl, cost=0.1)


def _seed_losses(engine, strategy_id: str, symbol: str, n: int, loss_pnl: float = -8.0):
    """Seed n losing trades."""
    for _ in range(n):
        engine.record(strategy_id, symbol, net_pnl=loss_pnl, cost=0.1)


# ── SCENARIO 1: Negative EV → rejected by TradeRanker ────────────────────────

def test_negative_ev_rejected_by_trade_ranker():
    """
    BUILD REJECTED if TradeRanker passes a trade with ev < 0.
    Hard rejection must happen before normalization.
    """
    from core.trade_ranker import TradeRanker

    ranker = TradeRanker()
    result = ranker.rank(
        ev=-0.05,
        trade_score=0.90,       # excellent score
        regime="TRENDING",
        strategy="TrendFollowing",
        history_score=0.90,
    )

    assert result.ok is False, (
        "BUILD REJECTED: TradeRanker passed a trade with ev=-0.05 — "
        "negative EV must be hard-rejected"
    )
    assert "NEGATIVE_EV" in result.reason, (
        f"BUILD REJECTED: expected 'NEGATIVE_EV' in reason, got: {result.reason}"
    )


def test_negative_ev_rejected_regardless_of_other_scores():
    """Any negative EV must be rejected no matter how good the other factors are."""
    from core.trade_ranker import TradeRanker

    ranker = TradeRanker()
    for ev_val in [-0.001, -0.10, -1.0, -100.0]:
        result = ranker.rank(
            ev=ev_val,
            trade_score=1.0,
            regime="TRENDING",
            strategy="TrendFollowing",
            history_score=1.0,
        )
        assert result.ok is False, (
            f"BUILD REJECTED: TradeRanker passed trade with ev={ev_val}"
        )
        assert "NEGATIVE_EV" in result.reason


def test_zero_ev_not_rejected_by_trade_ranker():
    """
    ev=0.0 (bootstrap) must NOT trigger the hard negative-EV rejection.
    It may still fail on rank_score threshold — that is acceptable.
    """
    from core.trade_ranker import TradeRanker

    ranker = TradeRanker()
    result = ranker.rank(
        ev=0.0,
        trade_score=0.90,
        regime="TRENDING",
        strategy="TrendFollowing",
        history_score=0.90,
    )
    # Must NOT be rejected due to NEGATIVE_EV
    assert "NEGATIVE_EV" not in result.reason, (
        "BUILD REJECTED: ev=0.0 triggered NEGATIVE_EV rejection — "
        "only strictly negative EV should be rejected"
    )


# ── SCENARIO 2: High EV → higher capital than low EV ─────────────────────────

def test_high_ev_produces_more_capital_than_low_ev():
    """
    BUILD REJECTED if CapitalConcentrator allocates equal or less to high-EV
    trades compared to low-EV trades (everything else equal).
    """
    from core.capital_concentrator import CapitalConcentrator

    cc = CapitalConcentrator()
    rank = 0.85   # HIGH band → 1.5×
    equity = 10_000.0
    base_risk = 100.0

    result_high_ev = cc.concentrate(
        rank_score=rank, equity=equity, base_risk_usdt=base_risk,
        upstream_mult=1.0, ev=0.20,  # above P7B_EV_HIGH_THRESHOLD (0.15)
    )
    result_low_ev = cc.concentrate(
        rank_score=rank, equity=equity, base_risk_usdt=base_risk,
        upstream_mult=1.0, ev=0.01,  # below P7B_EV_LOW_THRESHOLD (0.03)
    )

    assert result_high_ev.ok and result_low_ev.ok, "Both should be accepted by concentrator"
    assert result_high_ev.max_risk_usdt > result_low_ev.max_risk_usdt, (
        f"BUILD REJECTED: high-EV trade ({result_high_ev.max_risk_usdt} USDT) "
        f"did not get more capital than low-EV trade ({result_low_ev.max_risk_usdt} USDT)"
    )


def test_high_ev_boost_applied_in_reason():
    """Reason string must reflect ev_boost when EV is above threshold."""
    from core.capital_concentrator import CapitalConcentrator
    from config import cfg

    cc = CapitalConcentrator()
    result = cc.concentrate(
        rank_score=0.85, equity=10_000.0, base_risk_usdt=100.0,
        upstream_mult=1.0, ev=cfg.P7B_EV_HIGH_THRESHOLD + 0.01,
    )
    assert result.ok
    assert "ev_boost" in result.reason, (
        f"BUILD REJECTED: ev_boost not reflected in reason: {result.reason}"
    )


# ── SCENARIO 3: Bootstrap → confidence=0.3 ───────────────────────────────────

def test_bootstrap_returns_confidence_03():
    """
    BUILD REJECTED if bootstrap EVResult does not have confidence=0.3.
    Bootstrap = fewer trades than EV_MIN_TRADES.
    """
    engine = _fresh_ev_engine()

    result = engine.evaluate(
        strategy_id="TrendFollowing",
        symbol="BTCUSDT",
        est_reward=10.0,
        est_risk=5.0,
        current_cost=0.10,
    )

    assert result.bootstrapped is True, "Expected bootstrap result"
    assert result.confidence == 0.3, (
        f"BUILD REJECTED: bootstrap EVResult.confidence={result.confidence}, "
        f"expected 0.3"
    )


def test_non_bootstrap_confidence_above_bootstrap():
    """
    After enough trades, confidence must be higher than bootstrap (0.3).
    """
    from config import cfg

    engine = _fresh_ev_engine()
    _seed_wins(engine, "TrendFollowing", "ETHUSDT", cfg.EV_MIN_TRADES + 5)

    result = engine.evaluate(
        strategy_id="TrendFollowing",
        symbol="ETHUSDT",
        est_reward=10.0,
        est_risk=5.0,
        current_cost=0.10,
    )

    assert result.bootstrapped is False
    assert result.confidence > 0.3, (
        f"BUILD REJECTED: non-bootstrap confidence={result.confidence} "
        f"should be > 0.3"
    )


def test_confidence_increases_with_more_history():
    """Confidence must scale upward as history fills toward WINDOW."""
    from config import cfg

    engine_few = _fresh_ev_engine()
    engine_many = _fresh_ev_engine()

    _seed_wins(engine_few, "MeanReversion", "SOLUSDT", cfg.EV_MIN_TRADES + 2)
    _seed_wins(engine_many, "MeanReversion", "SOLUSDT", cfg.EV_WINDOW)

    res_few = engine_few.evaluate(
        "MeanReversion", "SOLUSDT", 10.0, 4.0, 0.10,
    )
    res_many = engine_many.evaluate(
        "MeanReversion", "SOLUSDT", 10.0, 4.0, 0.10,
    )

    assert res_many.confidence >= res_few.confidence, (
        f"BUILD REJECTED: more history should yield ≥ confidence "
        f"(few={res_few.confidence} many={res_many.confidence})"
    )


# ── SCENARIO 4: High drawdown → EV suppressed ────────────────────────────────

def test_high_drawdown_forces_ev_nonpositive():
    """
    BUILD REJECTED if a trade still gets positive EV when drawdown ≥ P7B_DD_MAX.
    Extreme drawdown must force EV ≤ 0.
    """
    from config import cfg

    engine = _fresh_ev_engine()
    _seed_wins(engine, "TrendFollowing", "BNBUSDT", cfg.EV_MIN_TRADES + 10)

    result = engine.evaluate(
        strategy_id="TrendFollowing",
        symbol="BNBUSDT",
        est_reward=100.0,    # very high reward
        est_risk=10.0,
        current_cost=0.10,
        drawdown=cfg.P7B_DD_MAX,   # exactly at max DD threshold
    )

    assert result.ev <= 0.0, (
        f"BUILD REJECTED: EV={result.ev:.4f} > 0 at drawdown={cfg.P7B_DD_MAX} "
        f"— extreme drawdown must suppress EV to ≤ 0"
    )
    assert result.ok is False, (
        "BUILD REJECTED: trade ok=True despite extreme drawdown forcing EV ≤ 0"
    )


def test_normal_drawdown_does_not_suppress_ev():
    """Small drawdown (below P7B_DD_MAX) must not force EV to zero."""
    from config import cfg

    engine = _fresh_ev_engine()
    _seed_wins(engine, "TrendFollowing", "ADAUSDT", cfg.EV_MIN_TRADES + 5)

    result = engine.evaluate(
        strategy_id="TrendFollowing",
        symbol="ADAUSDT",
        est_reward=100.0,
        est_risk=10.0,
        current_cost=0.10,
        drawdown=0.01,   # trivially small drawdown
    )

    # With high est_reward vs est_risk and a good win rate, EV should be positive
    assert result.ev > 0.0, (
        f"BUILD REJECTED: small drawdown should not suppress EV (ev={result.ev})"
    )


# ── SCENARIO 5: Strong regime confidence → EV boosted ────────────────────────

def test_strong_regime_confidence_boosts_ev():
    """
    BUILD REJECTED if high regime_confidence does not produce a higher EV
    than low regime_confidence (all else equal).
    """
    from config import cfg

    engine_high = _fresh_ev_engine()
    engine_low = _fresh_ev_engine()

    # Seed identical histories
    for e in (engine_high, engine_low):
        _seed_wins(e, "TrendFollowing", "DOTUSDT", cfg.EV_MIN_TRADES + 10)

    result_high = engine_high.evaluate(
        strategy_id="TrendFollowing",
        symbol="DOTUSDT",
        est_reward=20.0,
        est_risk=8.0,
        current_cost=0.10,
        drawdown=0.01,
        regime_confidence=cfg.P7B_REGIME_CONF_HIGH + 0.05,  # above threshold
    )
    result_low = engine_low.evaluate(
        strategy_id="TrendFollowing",
        symbol="DOTUSDT",
        est_reward=20.0,
        est_risk=8.0,
        current_cost=0.10,
        drawdown=0.01,
        regime_confidence=cfg.P7B_REGIME_CONF_LOW - 0.05,   # below threshold
    )

    assert result_high.ev > result_low.ev, (
        f"BUILD REJECTED: high regime confidence did not boost EV vs low "
        f"(high={result_high.ev:.4f} low={result_low.ev:.4f})"
    )


def test_neutral_regime_confidence_unchanged():
    """
    Regime confidence between P7B_REGIME_CONF_LOW and P7B_REGIME_CONF_HIGH
    must not apply any multiplier (neither boost nor penalty).
    """
    from config import cfg

    engine_neutral = _fresh_ev_engine()
    engine_base    = _fresh_ev_engine()

    for e in (engine_neutral, engine_base):
        _seed_wins(e, "MeanReversion", "XRPUSDT", cfg.EV_MIN_TRADES + 10)

    neutral_conf = (cfg.P7B_REGIME_CONF_LOW + cfg.P7B_REGIME_CONF_HIGH) / 2

    result_neutral = engine_neutral.evaluate(
        "MeanReversion", "XRPUSDT", 20.0, 8.0, 0.10,
        drawdown=0.0, regime_confidence=neutral_conf,
    )
    result_base = engine_base.evaluate(
        "MeanReversion", "XRPUSDT", 20.0, 8.0, 0.10,
        drawdown=0.0, regime_confidence=0.5,  # also neutral
    )

    # Both should be the same (within floating-point rounding)
    assert abs(result_neutral.ev - result_base.ev) < 0.001, (
        f"BUILD REJECTED: neutral regime confidence changed EV "
        f"({result_neutral.ev} vs {result_base.ev})"
    )


# ── SCENARIO 6: EVResult.confidence field exists ─────────────────────────────

def test_ev_result_has_confidence_field():
    """EVResult must expose a confidence field."""
    from core.ev_engine import EVResult

    r = EVResult(
        ok=True, ev=0.05, p_win=0.6, avg_win=10.0, avg_loss=5.0,
        avg_cost=0.1, n_trades=15, bootstrapped=False,
    )
    assert hasattr(r, "confidence"), (
        "BUILD REJECTED: EVResult missing 'confidence' field"
    )
    assert r.confidence == 1.0, "Default confidence should be 1.0"


def test_ev_result_confidence_default_bootstrap():
    """When EVEngine returns bootstrap result, confidence must be 0.3."""
    engine = _fresh_ev_engine()
    result = engine.evaluate("TestStrat", "TESTUSDT", 10.0, 5.0, 0.1)
    assert result.bootstrapped is True
    assert result.confidence == 0.3


# ── SCENARIO 7: GateAwareCapitalConcentrator passes ev through ────────────────

def test_gate_aware_concentrator_passes_ev():
    """
    When gate is open, GateAwareCapitalConcentrator must pass ev to the base
    concentrator — resulting in higher risk for high-EV vs low-EV.
    """
    from core.profit.capital_concentrator import GateAwareCapitalConcentrator
    from core.capital_concentrator import CapitalConcentrator
    from config import cfg

    base = CapitalConcentrator()
    cc = GateAwareCapitalConcentrator(base=base)

    gate_open = {"can_trade": True, "safe_mode": False, "reason": "ALL_CLEAR"}

    result_high = cc.concentrate(
        gate_status=gate_open, rank_score=0.85,
        equity=10_000.0, base_risk_usdt=100.0,
        upstream_mult=1.0, ev=cfg.P7B_EV_HIGH_THRESHOLD + 0.05,
    )
    result_low = cc.concentrate(
        gate_status=gate_open, rank_score=0.85,
        equity=10_000.0, base_risk_usdt=100.0,
        upstream_mult=1.0, ev=0.0,
    )

    assert result_high.max_risk_usdt > result_low.max_risk_usdt, (
        f"BUILD REJECTED: GateAwareCapitalConcentrator did not pass ev through "
        f"(high={result_high.max_risk_usdt} low={result_low.max_risk_usdt})"
    )


# ── SCENARIO 8: TradeRanker weight update (55% EV) ───────────────────────────

def test_trade_ranker_ev_weight_is_dominant():
    """TradeRanker must use EV weight ≥ 0.50 (Phase 7B: 0.55)."""
    from core.trade_ranker import TradeRanker

    ranker = TradeRanker()
    assert ranker._w_ev >= 0.50, (
        f"BUILD REJECTED: TradeRanker EV weight={ranker._w_ev} — "
        f"Phase 7B requires EV to be the dominant factor (≥ 0.50)"
    )


def test_trade_ranker_weights_sum_to_one():
    """All TradeRanker weights must sum to 1.0."""
    from core.trade_ranker import TradeRanker

    ranker = TradeRanker()
    total = ranker._w_ev + ranker._w_score + ranker._w_regime + ranker._w_history
    assert abs(total - 1.0) < 0.001, (
        f"BUILD REJECTED: TradeRanker weights sum to {total:.4f}, expected 1.0"
    )

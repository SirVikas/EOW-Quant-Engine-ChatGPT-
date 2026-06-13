"""
Regression: PAPER_SPEED RSI governor honors BYPASS_ALL_GATES (v1.90.0).

The RSI governor was the only gate in the PAPER_SPEED fallback path that did not
honor BYPASS_ALL_GATES, blocking ~60% of fallback signals (the dominant no-trade
reason) and starving the engine to ~0 trades in learning/calibration runs. Under
BYPASS, RSI-LEVEL blocks are re-admitted using the SMA momentum direction; toxic
contexts and the lean gate (gates 1-3) remain active.

This test exercises the real OpportunityEcology decision and the exact predicate
applied in main.py's on_tick fallback.
"""
from core.signal_ecology.opportunity_ecology import (
    opportunity_ecology,
    EcologyDecision,
)


def _readmit(dec, bypass, above_sma):
    """Mirror of the main.py on_tick re-admission predicate."""
    ps_side = dec.rsi_side if (dec.approved and dec.rsi_side) else None
    if ps_side is None and bypass and dec.rsi_blocked and dec.context_type != "TOXIC":
        ps_side = "LONG" if above_sma else "SHORT"
    return ps_side


def _blocked_trending_long():
    # rsi 65 > TRENDING band (~44.5) → governor blocks an above-SMA long
    return opportunity_ecology.evaluate_opportunity(
        regime="TRENDING", rsi_val=65.0, rsi_prev=64.0, above_sma=True,
        utc_hour=12, strategy_id="TrendFollowing_PAPER_SPEED", symbol="BTCUSDT",
        rsi_history=[63.0, 64.0, 65.0],
    )


def test_rsi_block_is_detectable_and_not_toxic():
    dec = _blocked_trending_long()
    assert dec.approved is False
    assert dec.rsi_blocked is True
    assert dec.context_type != "TOXIC"


def test_bypass_readmits_rsi_block_as_momentum_side():
    dec = _blocked_trending_long()
    assert _readmit(dec, bypass=True, above_sma=True) == "LONG"
    assert _readmit(dec, bypass=True, above_sma=False) == "SHORT"


def test_gated_mode_leaves_rsi_block_in_place():
    dec = _blocked_trending_long()
    assert _readmit(dec, bypass=False, above_sma=True) is None


def test_toxic_context_respected_even_under_bypass():
    tox = EcologyDecision(
        approved=False, block_reason="CONTEXT_TOXIC", size_multiplier=0.0,
        rsi_blocked=False, rsi_side="LONG", rsi_block_reason="", context_type="TOXIC",
        context_boost_mult=0.0, recovery_mode="NONE", recovery_size_mult=1.0,
        symbol="X", regime="TRENDING", utc_hour=12, strategy_id="s", rsi_val=65.0,
        survival_rate=0.0, drought_seconds=0.0,
    )
    assert _readmit(tox, bypass=True, above_sma=True) is None

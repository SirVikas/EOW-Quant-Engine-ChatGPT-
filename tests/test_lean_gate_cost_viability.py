"""
Regression: lean-gate economic-viability gate (Gate 3b, v1.91.0).

The dominant loss driver was cost-dominated geometry: stops at ~0.2% with a
round-trip cost (2×taker + 2×slippage ≈ 0.14%) eating ~70% of every 1R risked,
so even gross winners booked net losses (Fee Destruction 150%). Gate 3b rejects
any trade whose stop is smaller than MIN_SL_TO_COST_RATIO × round-trip cost.

Uses the actual fill geometry from the 2026-06-13 06:21 UTC report.
"""
from config import cfg
from core.lean_gate import lean_gate


def _check(entry, stop_loss, take_profit):
    # notional/streak/dd chosen so only Gate 1/2/3b can bind
    return lean_gate.check(
        entry=entry, stop_loss=stop_loss, take_profit=take_profit,
        notional=entry * 100, consecutive_losses=0, session_dd_pct=0.0,
    )


def test_cost_dominated_trade_is_blocked_at_default_ratio():
    # DOTUSDT from report: entry 0.9670, SL 0.9647 → 0.238% stop, cost ~0.14%
    # ratio = 0.238 / 0.14 ≈ 1.7 < default 3.0 → must block
    assert cfg.MIN_SL_TO_COST_RATIO == 3.0
    res = _check(0.9670, 0.9647, 0.9757)
    assert res.execute is False
    assert "COST_DOMINATED" in res.reason


def test_viable_wide_stop_trade_passes():
    # Same entry but stop 0.6% away (well above 3×cost=0.42%); TP keeps RR high
    entry = 0.9670
    sl = entry * (1 - 0.006)       # 0.6% stop
    tp = entry * (1 + 0.02)         # RR ~3.3
    res = _check(entry, sl, tp)
    assert res.execute is True, res.reason


def test_dial_lowering_restores_volume():
    # Lowering the dial to 1.0 should re-admit the cost-dominated DOT trade
    original = cfg.MIN_SL_TO_COST_RATIO
    try:
        cfg.MIN_SL_TO_COST_RATIO = 1.0  # min SL = 0.14%; DOT's 0.238% now clears
        res = _check(0.9670, 0.9647, 0.9757)
        assert res.execute is True, res.reason
    finally:
        cfg.MIN_SL_TO_COST_RATIO = original


def test_gate_active_even_under_bypass():
    # Economic-integrity gate is NOT a risk gate — it stays on in BYPASS mode.
    res = lean_gate.check(
        entry=0.9670, stop_loss=0.9647, take_profit=0.9757,
        notional=96.7, consecutive_losses=0, session_dd_pct=0.0,
        bypass_risk_gates=True,
    )
    assert res.execute is False
    assert "COST_DOMINATED" in res.reason

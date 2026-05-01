from core.risk_engine import RiskEngine


def test_ror_advisory_not_blocking():
    # RoR is ADVISORY — it reduces position size but never blocks trading.
    r = RiskEngine()
    r.initialize(1000)
    r.update_risk_of_ruin(0.5)
    ok, _ = r.check_new_trade()
    assert ok is True   # RoR never halts; only reduces size_multiplier


def test_drawdown_killswitch_at_15pct():
    r = RiskEngine()
    r.initialize(1000)
    r.update_equity(850)  # 15% DD
    ok, reason = r.check_new_trade()
    assert ok is False
    assert "MAX_DRAWDOWN" in reason

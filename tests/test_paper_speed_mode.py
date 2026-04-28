from core.risk_engine import RiskEngine


def test_paper_speed_mode_bypasses_daily_trade_cap():
    r = RiskEngine()
    r.initialize(1000.0)
    r._state.trades_today = 10_000  # stress throughput scenario

    allowed, reason = r.check_new_trade()

    assert allowed is True
    assert reason == ""


def test_paper_speed_mode_bypasses_halt_block():
    r = RiskEngine()
    r.initialize(1000.0)
    r._state.halted = True
    r._state.halt_reason = "MAX_DRAWDOWN(16.9%>=15%)"

    allowed, reason = r.check_new_trade()

    assert allowed is True
    assert reason == ""

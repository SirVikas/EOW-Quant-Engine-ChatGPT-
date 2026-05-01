"""Tests for audit-remediation controls added from observation report."""

from core.profit_guard import ProfitGuard
from core.market_data import MarketDataProvider


def test_profit_guard_hard_stop_requires_all_conditions():
    pg = ProfitGuard()

    blocked, reason = pg.hard_stop_required(
        profit_factor=0.85,
        n_trades=20,
        consecutive_losses=8,
    )
    assert blocked is True
    assert "PROFIT_GUARD_HARD_STOP" in reason


def test_profit_guard_hard_stop_not_triggered_with_small_sample():
    pg = ProfitGuard()

    blocked, reason = pg.hard_stop_required(
        profit_factor=0.60,
        n_trades=5,
        consecutive_losses=10,
    )
    assert blocked is False
    assert reason == ""


def test_symbol_validation_rejects_blocked_and_non_ascii():
    assert MarketDataProvider._is_valid_symbol("BTCUSDT") is True
    assert MarketDataProvider._is_valid_symbol("PEPEUSDT") is False
    assert MarketDataProvider._is_valid_symbol("BTC💥USDT") is False

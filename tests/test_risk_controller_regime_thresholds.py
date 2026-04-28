from core.pnl_calculator import PurePnLCalculator
from core.risk_controller import RiskController
from utils.capital_scaler import CapitalScaler


def _controller() -> RiskController:
    scaler = CapitalScaler()
    pnl = PurePnLCalculator()
    return RiskController(pnl, scaler)


def test_mean_reverting_borderline_trade_is_not_overblocked_by_required_r():
    rc = _controller()

    # Crafted so rr_after_cost lands just above 1.05 in a low-volatility setup.
    ok, detail = rc.get_trade_decision(
        side="LONG",
        entry=100.0,
        take_profit=101.01,
        stop_loss=99.2,
        qty=25.0,
        current_volatility=0.20,
        regime="MEAN_REVERTING",
    )

    assert detail["rr_after_cost"] > 1.00
    assert detail["required_r"] < detail["rr_after_cost"]
    assert ok is True


def test_regime_base_r_defaults_match_documented_thresholds():
    rc = _controller()

    assert rc._regime_base_r("TRENDING") == 1.20
    assert rc._regime_base_r("MEAN_REVERTING") == 1.05
    assert rc._regime_base_r("VOLATILITY_EXPANSION") == 1.15

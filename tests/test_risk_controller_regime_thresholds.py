from core.pnl_calculator import PurePnLCalculator
from core.risk_controller import RiskController
from utils.capital_scaler import CapitalScaler


def _controller() -> RiskController:
    scaler = CapitalScaler()
    pnl = PurePnLCalculator()
    return RiskController(pnl, scaler)


def test_mean_reverting_borderline_trade_is_not_overblocked_by_required_r():
    rc = _controller()

    # Crafted so rr_after_cost lands around ~1.43 in a low-volatility setup.
    # In normal mode this should fail vs MR base threshold (1.80),
    # but under dry-spell tier-3 relaxation it should pass.
    ok, detail = rc.get_trade_decision(
        side="LONG",
        entry=100.0,
        take_profit=101.27,
        stop_loss=99.2,
        qty=25.0,
        current_volatility=0.20,
        regime="MEAN_REVERTING",
        minutes_no_trade=0.0,
    )

    assert detail["rr_after_cost"] > 1.35
    assert detail["required_r"] == detail["required_r_raw"]
    assert detail["required_r"] > detail["rr_after_cost"]
    assert ok is False

    ok_relaxed, relaxed = rc.get_trade_decision(
        side="LONG",
        entry=100.0,
        take_profit=101.27,
        stop_loss=99.2,
        qty=25.0,
        current_volatility=0.20,
        regime="MEAN_REVERTING",
        minutes_no_trade=30.0,  # >= T3
    )
    assert relaxed["required_r_relax"] > 0
    assert relaxed["required_r"] < detail["required_r"]
    assert relaxed["required_r"] < relaxed["rr_after_cost"]
    assert ok_relaxed is True

def test_regime_base_r_defaults_match_documented_thresholds():
    rc = _controller()

    assert rc._regime_base_r("TRENDING") == 1.50
    assert rc._regime_base_r("MEAN_REVERTING") == 1.80
    assert rc._regime_base_r("VOLATILITY_EXPANSION") == 1.50


def test_required_r_relaxation_respects_hard_floor():
    rc = _controller()
    _, detail = rc.get_trade_decision(
        side="LONG",
        entry=100.0,
        take_profit=102.0,
        stop_loss=99.0,
        qty=10.0,
        current_volatility=0.20,
        regime="MEAN_REVERTING",
        minutes_no_trade=120.0,  # far beyond T3
    )

    assert detail["required_r_relax"] > 0
    assert detail["required_r"] >= 1.05

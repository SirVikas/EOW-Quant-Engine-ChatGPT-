from core.pnl_calculator import PurePnLCalculator
from core.risk_controller import RiskController
from utils.capital_scaler import CapitalScaler


def _rc() -> RiskController:
    return RiskController(PurePnLCalculator(), CapitalScaler())


def test_dry_spell_relaxes_required_r_but_not_below_floor():
    # TRENDING (base_r=1.20) is used because MEAN_REVERTING's base (1.05) now
    # sits at the hard floor, where relaxation has no observable effect.
    # rr_after_cost lands ≈1.10: blocked at 1.20, allowed once relaxed to 1.05.
    rc = _rc()
    kwargs = dict(
        side="LONG",
        entry=100.0,
        take_profit=101.04,
        stop_loss=99.2,
        qty=25.0,
        current_volatility=0.20,
        regime="TRENDING",
    )

    ok_normal, d0 = rc.get_trade_decision(minutes_no_trade=0.0, **kwargs)
    ok_relaxed, d1 = rc.get_trade_decision(minutes_no_trade=120.0, **kwargs)

    assert ok_normal is False
    assert d1["required_r_relax"] > 0
    assert d1["required_r"] < d0["required_r"]
    assert d1["required_r"] >= 1.05
    assert ok_relaxed is True

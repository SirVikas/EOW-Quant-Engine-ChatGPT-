from core.analytics import compute_full_analytics, deployability_index, risk_of_ruin
from core.guardian import _estimate_ror


def test_compute_full_analytics_uses_zero_ror_during_early_warmup():
    out = compute_full_analytics(
        pnl_trades=[],
        initial_capital=1000.0,
        session_stats={"win_rate": 0.0, "max_drawdown_pct": 0.0, "sharpe_ratio": 0.0},
        healer_snapshot={"recent_events": [], "ws_stale_cycles": 0},
        lake_stats={"trades": 0, "candles": 0},
        genome_state={"promotion_log": [], "generation": 0},
        redis_ok=False,
        persistence_ok=True,
    )
    assert out["risk_of_ruin_pct"] == 0.0


def test_deployability_rr_edge_runtime_fallback_awards_points_without_promotions():
    out = deployability_index(
        healer_snapshot={"recent_events": [], "ws_stale_cycles": 1},
        lake_stats={"trades": 0, "candles": 0},
        genome_state={"promotion_log": [], "generation": 0},
        runtime_rr={"avg_r_multiple": 0.7, "win_rate": 0.6, "trades": 24},
    )
    rr = out["breakdown"]["rr_edge"]
    assert rr["score"] == 25
    assert rr["avg_r_multiple"] == 0.7


def test_risk_of_ruin_perfect_win_rate_is_not_100_percent():
    assert risk_of_ruin(win_rate=1.0, avg_r_win=1.2, avg_r_loss=1.0, account_units=20) == 0.0


def test_guardian_ror_perfect_win_rate_is_not_100_percent():
    assert _estimate_ror(win_rate=1.0, avg_r_win=1.2, avg_r_loss=1.0, account_units=20) == 0.0


def test_risk_of_ruin_negative_edge_caps_below_100_for_ui_safety():
    ror = risk_of_ruin(win_rate=0.49, avg_r_win=1.0, avg_r_loss=1.1, account_units=20)
    assert ror == 99.99


def test_guardian_ror_negative_edge_caps_below_100_for_ui_safety():
    ror = _estimate_ror(win_rate=0.49, avg_r_win=1.0, avg_r_loss=1.1, account_units=20)
    assert ror == 99.99

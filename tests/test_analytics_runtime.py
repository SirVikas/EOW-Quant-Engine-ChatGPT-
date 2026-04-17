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


def test_compute_full_analytics_ignores_zero_r_trades_for_ror_win_rate():
    pnl_trades = (
        [{"net_pnl": 10.0, "r_multiple": 1.0} for _ in range(4)]
        + [{"net_pnl": -5.0, "r_multiple": -0.5}]
        + [{"net_pnl": 0.0, "r_multiple": 0.0} for _ in range(15)]
    )

    out = compute_full_analytics(
        pnl_trades=pnl_trades,
        initial_capital=1000.0,
        # Legacy session win-rate includes breakeven trades as non-wins.
        session_stats={"win_rate": 20.0, "max_drawdown_pct": 5.0, "sharpe_ratio": 0.5},
        healer_snapshot={"recent_events": [], "ws_stale_cycles": 0},
        lake_stats={"trades": 20, "candles": 100},
        genome_state={"promotion_log": [], "generation": 1},
        redis_ok=True,
        persistence_ok=True,
    )

    assert out["risk_of_ruin_pct"] < 100.0

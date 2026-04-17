from core.analytics import compute_full_analytics


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

    assert out["risk_of_ruin_pct"] == 0.0
    assert out["risk_of_ruin_debug"]["status"] == "WARMUP"
    assert out["risk_of_ruin_debug"]["reason"] == "INSUFFICIENT_VALID_R_SAMPLE"


def test_compute_full_analytics_ror_active_after_sufficient_sample():
    pnl_trades = (
        [{"net_pnl": 10.0, "r_multiple": 1.0} for _ in range(14)]
        + [{"net_pnl": -8.0, "r_multiple": -0.8} for _ in range(6)]
    )
    out = compute_full_analytics(
        pnl_trades=pnl_trades,
        initial_capital=1000.0,
        session_stats={"win_rate": 70.0, "max_drawdown_pct": 5.0, "sharpe_ratio": 0.5},
        healer_snapshot={"recent_events": [], "ws_stale_cycles": 0},
        lake_stats={"trades": 20, "candles": 100},
        genome_state={"promotion_log": [], "generation": 1},
        redis_ok=True,
        persistence_ok=True,
    )

    assert out["risk_of_ruin_debug"]["status"] == "ACTIVE"
    assert out["risk_of_ruin_pct"] < 100.0

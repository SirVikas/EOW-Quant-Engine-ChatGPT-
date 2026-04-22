"""
FTD-008 — Edge Engine Verifier
Run: python -m pytest tests/verify_edge_engine.py -v
     OR: python tests/verify_edge_engine.py

Checks that all FTD-008 components are importable and behave correctly
at module level before the full engine starts.
"""
import sys
import os

# Allow running from project root without install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Component presence checks ─────────────────────────────────────────────────

def test_edge_filter_active():
    from core.edge_filter import has_minimum_edge, check_edge, EdgeFilterResult
    print("[VERIFY] Edge filter (FTD-008 §1) active")

    class _Sig:
        score = 0.75
        rr    = 2.5

    assert has_minimum_edge(_Sig()), "has_minimum_edge should pass for score=0.75 rr=2.5"

    class _Weak:
        score = 0.50
        rr    = 1.0

    assert not has_minimum_edge(_Weak()), "has_minimum_edge should block score=0.50 rr=1.0"

    result = check_edge(_Weak())
    assert not result.ok
    assert "SCORE_BELOW_MIN" in result.reason or "RR_BELOW_MIN" in result.reason
    print("  ✓ has_minimum_edge / check_edge working")


def test_ev_phased_logic_active():
    from core.ev_engine import is_ev_reliable, is_trade_allowed
    print("[VERIFY] EV phased logic (FTD-008 §2) active")

    assert not is_ev_reliable(10),  "10 trades should not be reliable"
    assert not is_ev_reliable(29),  "29 trades should not be reliable"
    assert     is_ev_reliable(30),  "30 trades should be reliable"
    assert     is_ev_reliable(100), "100 trades should be reliable"

    # Bootstrap phase — EV ignored
    assert is_trade_allowed(ev=-5.0, trade_count=10), \
        "Negative EV must be allowed in bootstrap (<30 trades)"
    assert is_trade_allowed(ev=0.0, trade_count=29), \
        "Zero EV must be allowed in bootstrap (<30 trades)"

    # Live phase — EV must be positive
    assert     is_trade_allowed(ev=0.01,  trade_count=30), "Positive EV must pass"
    assert not is_trade_allowed(ev=0.0,   trade_count=30), "Zero EV must be blocked"
    assert not is_trade_allowed(ev=-1.0,  trade_count=50), "Negative EV must be blocked"
    print("  ✓ is_ev_reliable / is_trade_allowed working")


def test_ranking_active():
    from core.trade_ranker import rank_trades
    print("[VERIFY] Trade ranking (FTD-008 §3) active")

    class _Sig:
        def __init__(self, score, ev, rr):
            self.score = score
            self.ev    = ev
            self.rr    = rr

    signals = [
        _Sig(score=0.72, ev=0.10, rr=2.1),
        _Sig(score=0.90, ev=0.05, rr=2.0),
        _Sig(score=0.80, ev=0.20, rr=3.0),
    ]
    ranked = rank_trades(signals)
    assert ranked[0].score == 0.90, "Highest score should rank first"
    assert len(ranked) == 3
    print("  ✓ rank_trades working")


def test_explore_control_active():
    from core.exploration_engine import allow_explore
    print("[VERIFY] Explore control (FTD-008 §4) active")

    assert not allow_explore("BOOTING", trades_last_30m=0), \
        "Must block when not LIVE"
    assert not allow_explore("LIVE",    trades_last_30m=1), \
        "Must block when trades active in last 30m"
    assert     allow_explore("LIVE",    trades_last_30m=0), \
        "Must allow when LIVE and idle"
    print("  ✓ allow_explore working")


def test_genome_filter_active():
    from core.genome_engine import is_strategy_allowed
    print("[VERIFY] Genome filter (FTD-008 §5) active")

    class _Strat:
        def __init__(self, trades, oos_pf):
            self.trades = trades
            self.oos_pf = oos_pf

    assert not is_strategy_allowed(_Strat(trades=10,  oos_pf=1.5)), \
        "Must reject strategy with < 30 trades"
    assert not is_strategy_allowed(_Strat(trades=50,  oos_pf=1.1)), \
        "Must reject strategy with oos_pf ≤ 1.2"
    assert not is_strategy_allowed(_Strat(trades=0,   oos_pf=0.0)), \
        "Must reject strategy with 0 trades"
    assert     is_strategy_allowed(_Strat(trades=30,  oos_pf=1.3)), \
        "Must allow strategy with ≥30 trades and oos_pf > 1.2"
    assert     is_strategy_allowed(_Strat(trades=100, oos_pf=2.0)), \
        "Must allow proven strategy"
    print("  ✓ is_strategy_allowed working")


def test_trade_frequency_active():
    from core.trade_frequency import can_trade
    from config import cfg
    print("[VERIFY] Trade frequency gate (FTD-008 §6) active")

    assert     can_trade(0, 0),  "Fresh session should be allowed"
    assert     can_trade(cfg.MAX_TRADES_PER_HOUR - 1, cfg.MAX_TRADES_PER_DAY - 1), \
        "One below both limits should pass"
    assert not can_trade(cfg.MAX_TRADES_PER_HOUR, 0), \
        "At hourly limit should block"
    assert not can_trade(0, cfg.MAX_TRADES_PER_DAY), \
        "At daily limit should block"
    print(
        f"  ✓ can_trade working "
        f"(hourly={cfg.MAX_TRADES_PER_HOUR} daily={cfg.MAX_TRADES_PER_DAY})"
    )


def test_cost_guard_active():
    from core.cost_guard import is_cost_valid, check_cost
    from config import cfg
    print("[VERIFY] Cost guard (FTD-008 §7) active")

    profit = 100.0
    low_cost  = profit * cfg.MAX_COST_FRACTION * 0.5   # 50% of limit → ok
    high_cost = profit * cfg.MAX_COST_FRACTION * 1.5   # 150% of limit → block

    assert     is_cost_valid(profit, low_cost),  "Low cost should pass"
    assert not is_cost_valid(profit, high_cost), "High cost should block"
    assert not is_cost_valid(0.0,    1.0),        "Zero profit should block"
    assert not is_cost_valid(-5.0,   1.0),        "Negative profit should block"

    r = check_cost(profit, high_cost)
    assert not r.ok
    assert "COST_TOO_HIGH" in r.reason
    print("  ✓ is_cost_valid / check_cost working")


def test_equity_snapshot_active():
    from core.equity_snapshot import EquitySnapshotManager
    import tempfile, os
    print("[VERIFY] Equity snapshot (qFTD-009) active")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_snap.json")
        mgr = EquitySnapshotManager(path=path)

        # save + load round-trip
        mgr.save(equity=987.65, trade_count=42, session_id="test")
        snap = mgr.load()
        assert snap is not None
        assert abs(snap.equity - 987.65) < 0.001
        assert snap.trade_count == 42

        # validation: within tolerance
        assert mgr.validate(987.65, 987.65),  "Identical values must pass"
        assert mgr.validate(987.65, 990.00),  "< 1% gap must pass"
        assert not mgr.validate(987.65, 900.00), "> 1% gap must fail"

        # restore_or_replay with valid snapshot
        restored = mgr.restore_or_replay(
            replay_equity=987.0,
            replay_trade_count=42,
        )
        assert abs(restored - 987.65) < 0.001, \
            "Within-tolerance snapshot should be preferred"

    print("  ✓ EquitySnapshotManager working")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_edge_filter_active,
        test_ev_phased_logic_active,
        test_ranking_active,
        test_explore_control_active,
        test_genome_filter_active,
        test_trade_frequency_active,
        test_cost_guard_active,
        test_equity_snapshot_active,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            print(f"  ✗ FAILED {t.__name__}: {exc}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"FTD-008 / qFTD-009 Verification: {passed}/{passed+failed} passed")
    if failed:
        sys.exit(1)
    print("All edge engine components verified. System ready.")

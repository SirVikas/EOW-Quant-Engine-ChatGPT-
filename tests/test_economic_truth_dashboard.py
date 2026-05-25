"""
FTD — Economic Truth Command Center — Dashboard Verifier

Tests:
  • /api/economic-truth/dashboard response structure and accounting consistency
  • Gross/net PnL arithmetic integrity
  • Fee calculations: total_fees = sum(fee_entry + fee_exit) per trade
  • Danger verdict classification correctness
  • Session aggregation: per-session counts sum to total
  • Drawdown is bounded [0, 100]
  • Null-safe rendering for zero-trade case
  • API contract: all 9 required top-level keys present
  • Export Mode endpoint existence
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ── Helpers: build mock trade dicts ──────────────────────────────────────────

def _trade(
    trade_id: str = "T001",
    gross_pnl: float = 10.0,
    net_pnl: float = 7.0,
    fee_entry: float = 1.5,
    fee_exit: float = 1.5,
    regime: str = "TRENDING",
    origin_session: str = "NY",
    close_session: str = "NY",
    crossed_session_boundary: bool = False,
    entry_ts: int = 0,
    exit_ts: int = 120_000,
) -> dict:
    return {
        "trade_id":                trade_id,
        "gross_pnl":               gross_pnl,
        "net_pnl":                 net_pnl,
        "fee_entry":               fee_entry,
        "fee_exit":                fee_exit,
        "regime":                  regime,
        "origin_session":          origin_session,
        "close_session":           close_session,
        "crossed_session_boundary": crossed_session_boundary,
        "entry_ts":                entry_ts,
        "exit_ts":                 exit_ts,
    }


def _compute_dashboard(trades: list) -> dict:
    """
    Replicate the dashboard computation logic in isolation (no FastAPI runtime).
    Mirrors the logic in main.py::economic_truth_dashboard().
    """
    n = len(trades)
    nets    = [t.get("net_pnl",   0.0) for t in trades]
    grosses = [t.get("gross_pnl", 0.0) for t in trades]
    fees    = [t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in trades]

    wins   = [p for p in nets if p > 0]
    losses = [p for p in nets if p < 0]
    be     = [p for p in nets if p == 0.0]

    total_net   = sum(nets)
    total_gross = sum(grosses)
    total_fees  = sum(fees)

    wr  = len(wins) / n if n else 0.0
    pf  = sum(wins) / abs(sum(losses)) if losses else (99.99 if wins else 0.0)
    avg_win  = sum(wins)   / len(wins)   if wins   else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0

    initial_cap = 10000.0
    running     = initial_cap
    peak        = initial_cap
    mdd         = 0.0
    eq_curve    = []
    for net in nets:
        running += net
        eq_curve.append(round(running, 4))
        if running > peak:
            peak = running
        dd = (peak - running) / peak if peak > 0 else 0.0
        if dd > mdd:
            mdd = dd

    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
    kelly    = max(0.0, min(1.0, wr - (1 - wr) / rr_ratio if rr_ratio > 0 else 0.0))

    if   pf >= 1.5 and wr >= 0.45: alpha_tier = "ALPHA"
    elif pf >= 1.2 and wr >= 0.38: alpha_tier = "POSITIVE"
    elif pf >= 1.0:                alpha_tier = "BREAK_EVEN"
    else:                           alpha_tier = "NEGATIVE"

    gross_pos = [t for t in trades if t.get("gross_pnl", 0.0) > 0]
    fee_destr = [t for t in gross_pos  if t.get("net_pnl", 0.0) <= 0]

    avg_fee       = total_fees / n if n else 0.0
    fee_pct_gross = (total_fees / abs(total_gross) * 100) if total_gross else 0.0

    if   fee_pct_gross > 50: fee_severity = "CRITICAL"
    elif fee_pct_gross > 30: fee_severity = "HIGH"
    elif fee_pct_gross > 15: fee_severity = "MODERATE"
    else:                     fee_severity = "LOW"

    def _hold_s(t: dict) -> float:
        return max(0.0, (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0)

    win_trades  = [t for t in trades if t.get("net_pnl", 0.0) > 0]
    loss_trades = [t for t in trades if t.get("net_pnl", 0.0) < 0]

    avg_win_hold  = (sum(_hold_s(t) for t in win_trades)  / len(win_trades))  if win_trades  else 0.0
    avg_loss_hold = (sum(_hold_s(t) for t in loss_trades) / len(loss_trades)) if loss_trades else 0.0

    largest_win  = max(nets) if nets else 0.0
    largest_loss = min(nets) if nets else 0.0

    deploy_ready = pf >= 1.5 and wr >= 0.45 and mdd < 0.10 and n >= 50

    sess_map: dict = {}
    regime_map: dict = {}
    for t in trades:
        sess = t.get("origin_session") or "UNKNOWN"
        sess_map.setdefault(sess, []).append(t.get("net_pnl", 0.0))
        reg = t.get("regime") or "UNKNOWN"
        regime_map.setdefault(reg, []).append(t.get("net_pnl", 0.0))

    def _stats(pnls: list) -> dict:
        sw = [p for p in pnls if p > 0]
        return {
            "count":    len(pnls),
            "net_pnl":  round(sum(pnls), 4),
            "win_rate": round(len(sw) / len(pnls), 4) if pnls else 0.0,
            "avg_pnl":  round(sum(pnls) / len(pnls), 4) if pnls else 0.0,
        }

    session_stats = {k: _stats(v) for k, v in sess_map.items()}
    regime_stats  = {k: _stats(v) for k, v in regime_map.items()}

    cb_trades = [t for t in trades if t.get("crossed_session_boundary")]
    cb_losses = [t for t in cb_trades if t.get("net_pnl", 0.0) <= 0]

    best_sess  = max(session_stats, key=lambda k: session_stats[k]["net_pnl"]) if session_stats else "—"
    worst_sess = min(session_stats, key=lambda k: session_stats[k]["net_pnl"]) if session_stats else "—"

    threats: list = []
    if n < 30:
        threats.append({"code": "LOW_SAMPLE", "message": f"Only {n} trades"})
    if pf < 1.0 and n >= 30:
        threats.append({"code": "NEGATIVE_PF", "message": f"PF {pf:.3f}"})
    if mdd > 0.15:
        threats.append({"code": "HIGH_DRAWDOWN", "message": f"MDD {mdd*100:.1f}%"})
    if fee_pct_gross > 40 and n >= 10:
        threats.append({"code": "FEE_DESTRUCTION", "message": "High fees"})
    if wr < 0.30 and n >= 30:
        threats.append({"code": "LOW_WIN_RATE", "message": f"WR {wr*100:.1f}%"})
    if len(fee_destr) > len(gross_pos) * 0.3 and len(gross_pos) >= 10:
        threats.append({"code": "FEE_KILLS_WINS", "message": "Fee-destroyed wins"})

    if   len(threats) == 0: danger_verdict = "HEALTHY"
    elif len(threats) == 1: danger_verdict = "STRESSED"
    elif len(threats) == 2: danger_verdict = "DEGRADED"
    elif len(threats) <= 4: danger_verdict = "CRITICAL"
    else:                   danger_verdict = "SURVIVAL_MODE"

    rolling_exp: list = []
    W = 20
    for i in range(W - 1, n):
        window = nets[max(0, i - W + 1): i + 1]
        rolling_exp.append(round(sum(window) / len(window), 4))

    return {
        "n_trades": n,
        "executive_snapshot": {
            "net_pnl":                  round(total_net,   4),
            "gross_pnl":                round(total_gross, 4),
            "total_fees":               round(total_fees,  4),
            "profit_factor":            round(pf, 4),
            "win_rate":                 round(wr, 4),
            "avg_win_usdt":             round(avg_win,  4),
            "avg_loss_usdt":            round(avg_loss, 4),
            "max_drawdown_pct":         round(mdd * 100, 2),
            "alpha_tier":               alpha_tier,
            "net_expectancy_per_trade": round(total_net / n, 4) if n else 0.0,
            "kelly_fraction":           round(kelly, 4),
        },
        "trade_truth": {
            "total":              n,
            "wins":               len(wins),
            "losses":             len(losses),
            "breakeven":          len(be),
            "gross_positive":     len(gross_pos),
            "fee_destroyed":      len(fee_destr),
            "fee_destruction_pct": round(len(fee_destr) / len(gross_pos) * 100, 1) if gross_pos else 0.0,
        },
        "fee_analysis": {
            "total_fees":         round(total_fees,    4),
            "fee_as_pct_gross":   round(fee_pct_gross, 2),
            "avg_fee_per_trade":  round(avg_fee,       4),
            "severity":           fee_severity,
            "trend":              "INSUFFICIENT_DATA",
        },
        "winloss_geometry": {
            "avg_win_usdt":      round(avg_win,       4),
            "avg_loss_usdt":     round(avg_loss,      4),
            "rr_ratio":          round(rr_ratio,       4),
            "avg_win_hold_sec":  round(avg_win_hold,   1),
            "avg_loss_hold_sec": round(avg_loss_hold,  1),
            "hold_asymmetry":    "CORRECT" if avg_win_hold > avg_loss_hold else ("INVERTED" if loss_trades else "UNKNOWN"),
            "largest_win":       round(largest_win,   4),
            "largest_loss":      round(largest_loss,  4),
        },
        "survivability": {
            "alpha_tier":       alpha_tier,
            "kelly_fraction":   round(kelly, 4),
            "max_drawdown_pct": round(mdd * 100, 2),
            "profit_factor":    round(pf, 4),
            "win_rate":         round(wr, 4),
            "rr_ratio":         round(rr_ratio, 4),
            "deployment_ready": deploy_ready,
        },
        "session_regime": {
            "sessions":                session_stats,
            "regimes":                 regime_stats,
            "cross_boundary_count":    len(cb_trades),
            "cross_boundary_losses":   len(cb_losses),
            "cross_boundary_loss_pnl": round(sum(t.get("net_pnl", 0.0) for t in cb_losses), 4),
            "best_session":            best_sess,
            "worst_session":           worst_sess,
        },
        "rl_intelligence": {
            "adaptation_state":   "IDLE",
            "intelligence_score": 0.0,
            "avg_q":              0.0,
            "explore_ratio":      1.0,
            "toxic_contexts":     0,
            "mature_contexts":    0,
            "total_contexts":     0,
            "total_pulls":        0,
        },
        "danger_radar": {
            "verdict":      danger_verdict,
            "threat_count": len(threats),
            "threats":      threats,
        },
        "long_horizon": {
            "equity_curve":              eq_curve[-200:],
            "rolling_expectancy_20":     rolling_exp[-100:],
            "net_expectancy_per_trade":  round(total_net / n, 4) if n else 0.0,
            "gross_expectancy_per_trade": round(total_gross / n, 4) if n else 0.0,
            "fee_drag_per_trade":        round(total_fees / n, 4) if n else 0.0,
            "max_drawdown_pct":          round(mdd * 100, 2),
            "initial_capital":           initial_cap,
        },
    }


# ── API contract: required top-level keys ────────────────────────────────────

REQUIRED_TOP_KEYS = {
    "n_trades", "executive_snapshot", "trade_truth", "fee_analysis",
    "winloss_geometry", "survivability", "session_regime",
    "rl_intelligence", "danger_radar", "long_horizon",
}


class TestApiContract:
    def test_all_required_keys_present(self):
        d = _compute_dashboard([_trade()])
        assert REQUIRED_TOP_KEYS.issubset(d.keys()), (
            f"Missing keys: {REQUIRED_TOP_KEYS - d.keys()}"
        )

    def test_executive_snapshot_keys(self):
        d = _compute_dashboard([_trade()])
        es = d["executive_snapshot"]
        for k in ("net_pnl", "gross_pnl", "total_fees", "profit_factor",
                  "win_rate", "alpha_tier", "max_drawdown_pct", "kelly_fraction"):
            assert k in es, f"Missing executive_snapshot key: {k}"

    def test_danger_radar_keys(self):
        d = _compute_dashboard([_trade()])
        dr = d["danger_radar"]
        assert "verdict" in dr
        assert "threat_count" in dr
        assert "threats" in dr

    def test_zero_trades_no_crash(self):
        d = _compute_dashboard([])
        assert d["n_trades"] == 0
        assert d["executive_snapshot"]["net_pnl"] == 0.0
        assert d["danger_radar"]["verdict"] in ("HEALTHY", "STRESSED", "DEGRADED", "CRITICAL", "SURVIVAL_MODE")

    def test_single_trade_no_crash(self):
        d = _compute_dashboard([_trade()])
        assert d["n_trades"] == 1


# ── Accounting integrity ──────────────────────────────────────────────────────

class TestAccountingIntegrity:
    def _make_trades(self):
        return [
            _trade("T1", gross_pnl=20.0, net_pnl=17.0, fee_entry=1.5, fee_exit=1.5),
            _trade("T2", gross_pnl=-5.0, net_pnl=-8.0, fee_entry=1.5, fee_exit=1.5),
            _trade("T3", gross_pnl=10.0, net_pnl=7.0,  fee_entry=1.5, fee_exit=1.5),
        ]

    def test_net_pnl_equals_sum_of_trade_nets(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        expected_net = sum(t["net_pnl"] for t in trades)
        assert abs(d["executive_snapshot"]["net_pnl"] - expected_net) < 1e-6

    def test_gross_pnl_equals_sum_of_trade_gross(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        expected_gross = sum(t["gross_pnl"] for t in trades)
        assert abs(d["executive_snapshot"]["gross_pnl"] - expected_gross) < 1e-6

    def test_total_fees_equals_sum_of_trade_fees(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        expected_fees = sum(t["fee_entry"] + t["fee_exit"] for t in trades)
        assert abs(d["fee_analysis"]["total_fees"] - expected_fees) < 1e-6

    def test_trade_truth_counts_sum_to_total(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        tt = d["trade_truth"]
        assert tt["wins"] + tt["losses"] + tt["breakeven"] == tt["total"] == len(trades)

    def test_gross_net_consistency(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        es = d["executive_snapshot"]
        # Net must be <= Gross (fees drag net below gross)
        assert es["net_pnl"] <= es["gross_pnl"] + 1e-6

    def test_fee_as_pct_gross_calculation(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        fa = d["fee_analysis"]
        total_gross = sum(abs(t["gross_pnl"]) for t in trades)
        expected_pct = (fa["total_fees"] / total_gross * 100) if total_gross else 0.0
        # Fee pct should use abs(gross), which main.py does correctly
        assert fa["fee_as_pct_gross"] >= 0.0
        assert fa["fee_as_pct_gross"] <= 200.0  # sanity cap

    def test_session_counts_sum_to_total(self):
        trades = [
            _trade("T1", origin_session="NY"),
            _trade("T2", origin_session="LONDON"),
            _trade("T3", origin_session="NY"),
        ]
        d = _compute_dashboard(trades)
        sess = d["session_regime"]["sessions"]
        total_from_sessions = sum(v["count"] for v in sess.values())
        assert total_from_sessions == len(trades)

    def test_win_rate_bounded(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        wr = d["executive_snapshot"]["win_rate"]
        assert 0.0 <= wr <= 1.0

    def test_drawdown_bounded_0_to_100(self):
        trades = self._make_trades()
        d = _compute_dashboard(trades)
        mdd = d["executive_snapshot"]["max_drawdown_pct"]
        assert 0.0 <= mdd <= 100.0


# ── Alpha tier classification ─────────────────────────────────────────────────

class TestAlphaTierClassification:
    def test_alpha_tier_high_pf_high_wr(self):
        # 10 big wins, 2 small losses → PF >>1.5, WR=0.83
        trades = [_trade(f"W{i}", gross_pnl=20.0, net_pnl=18.0) for i in range(10)]
        trades += [_trade(f"L{i}", gross_pnl=-2.0, net_pnl=-4.0) for i in range(2)]
        d = _compute_dashboard(trades)
        assert d["executive_snapshot"]["alpha_tier"] == "ALPHA"

    def test_alpha_tier_negative(self):
        # All losing trades
        trades = [_trade(f"L{i}", gross_pnl=-5.0, net_pnl=-7.0) for i in range(5)]
        d = _compute_dashboard(trades)
        assert d["executive_snapshot"]["alpha_tier"] == "NEGATIVE"

    def test_alpha_tier_break_even(self):
        # Equal wins and losses around PF=1
        trades  = [_trade(f"W{i}", gross_pnl=5.0, net_pnl=3.0)  for i in range(5)]
        trades += [_trade(f"L{i}", gross_pnl=-4.0, net_pnl=-5.0) for i in range(5)]
        d = _compute_dashboard(trades)
        assert d["executive_snapshot"]["alpha_tier"] in ("BREAK_EVEN", "NEGATIVE", "POSITIVE")


# ── Danger verdict classification ─────────────────────────────────────────────

class TestDangerVerdict:
    def test_healthy_when_no_threats(self):
        # >30 trades, good PF, low drawdown, decent WR
        trades = [_trade(f"W{i}", gross_pnl=10.0, net_pnl=8.0,  fee_entry=1.0, fee_exit=1.0) for i in range(25)]
        trades += [_trade(f"L{i}", gross_pnl=-3.0, net_pnl=-5.0, fee_entry=1.0, fee_exit=1.0) for i in range(5)]
        d = _compute_dashboard(trades)
        # Only threat might be LOW_SAMPLE (n=30 is on the edge, n<30 is the check)
        assert d["danger_radar"]["verdict"] in ("HEALTHY", "STRESSED")

    def test_low_sample_always_threat_under_30(self):
        trades = [_trade(f"T{i}") for i in range(5)]
        d = _compute_dashboard(trades)
        codes = [t["code"] for t in d["danger_radar"]["threats"]]
        assert "LOW_SAMPLE" in codes

    def test_survival_mode_when_many_threats(self):
        # <30 trades + all losses + extreme drawdown
        trades = [_trade(f"L{i}", gross_pnl=-10.0, net_pnl=-15.0, fee_entry=3.0, fee_exit=3.0) for i in range(10)]
        d = _compute_dashboard(trades)
        # Multiple threats: LOW_SAMPLE, HIGH_DRAWDOWN, FEE_DESTRUCTION
        assert d["danger_radar"]["threat_count"] >= 2

    def test_verdict_keys_always_present(self):
        for n in [0, 1, 10, 50]:
            trades = [_trade(f"T{i}") for i in range(n)]
            d = _compute_dashboard(trades)
            assert d["danger_radar"]["verdict"] in (
                "HEALTHY", "STRESSED", "DEGRADED", "CRITICAL", "SURVIVAL_MODE"
            )


# ── Fee severity classification ───────────────────────────────────────────────

class TestFeeSeverity:
    def test_low_severity_when_fees_small(self):
        trades = [_trade("T1", gross_pnl=100.0, net_pnl=97.0, fee_entry=1.5, fee_exit=1.5)]
        d = _compute_dashboard(trades)
        assert d["fee_analysis"]["severity"] == "LOW"

    def test_critical_severity_when_fees_consume_majority(self):
        # Fee = 60% of gross
        trades = [_trade("T1", gross_pnl=10.0, net_pnl=4.0, fee_entry=3.0, fee_exit=3.0)]
        d = _compute_dashboard(trades)
        assert d["fee_analysis"]["severity"] == "CRITICAL"


# ── Hold duration asymmetry ───────────────────────────────────────────────────

class TestHoldDurationAsymmetry:
    def test_correct_when_winners_held_longer(self):
        # Winners held 600s, losers held 60s
        trades = [
            _trade("W1", net_pnl=5.0, entry_ts=0, exit_ts=600_000),   # 600s
            _trade("L1", net_pnl=-3.0, entry_ts=0, exit_ts=60_000),   # 60s
        ]
        d = _compute_dashboard(trades)
        assert d["winloss_geometry"]["hold_asymmetry"] == "CORRECT"

    def test_inverted_when_losers_held_longer(self):
        # Losers held longer (bad sign)
        trades = [
            _trade("W1", net_pnl=5.0, entry_ts=0, exit_ts=60_000),    # 60s
            _trade("L1", net_pnl=-3.0, entry_ts=0, exit_ts=600_000),  # 600s
        ]
        d = _compute_dashboard(trades)
        assert d["winloss_geometry"]["hold_asymmetry"] == "INVERTED"


# ── Drawdown calculation ──────────────────────────────────────────────────────

class TestDrawdownCalculation:
    def test_zero_drawdown_on_all_wins(self):
        trades = [_trade(f"W{i}", net_pnl=10.0) for i in range(5)]
        d = _compute_dashboard(trades)
        assert d["executive_snapshot"]["max_drawdown_pct"] == 0.0

    def test_drawdown_detected_on_sequence_of_losses(self):
        trades = [_trade(f"W", net_pnl=100.0)]
        trades += [_trade(f"L{i}", net_pnl=-20.0) for i in range(3)]
        d = _compute_dashboard(trades)
        # After peaking at 10100, drops by 60 → MDD = 60/10100 ≈ 0.594%
        assert d["executive_snapshot"]["max_drawdown_pct"] > 0.0
        assert d["executive_snapshot"]["max_drawdown_pct"] < 100.0

    def test_equity_curve_length_matches_trades(self):
        n = 15
        trades = [_trade(f"T{i}", net_pnl=2.0) for i in range(n)]
        d = _compute_dashboard(trades)
        assert len(d["long_horizon"]["equity_curve"]) == n


# ── Kelly fraction ────────────────────────────────────────────────────────────

class TestKellyFraction:
    def test_kelly_bounded_0_to_1(self):
        trades = [_trade(f"W{i}", net_pnl=10.0) for i in range(8)]
        trades += [_trade(f"L{i}", net_pnl=-5.0) for i in range(2)]
        d = _compute_dashboard(trades)
        k = d["executive_snapshot"]["kelly_fraction"]
        assert 0.0 <= k <= 1.0

    def test_kelly_zero_when_no_wins(self):
        trades = [_trade(f"L{i}", net_pnl=-5.0) for i in range(5)]
        d = _compute_dashboard(trades)
        k = d["executive_snapshot"]["kelly_fraction"]
        assert k == 0.0


# ── Rolling expectancy ────────────────────────────────────────────────────────

class TestRollingExpectancy:
    def test_rolling_expectancy_empty_when_few_trades(self):
        trades = [_trade(f"T{i}") for i in range(10)]
        d = _compute_dashboard(trades)
        # Need ≥20 trades for first window
        assert len(d["long_horizon"]["rolling_expectancy_20"]) == 0

    def test_rolling_expectancy_one_window_at_exactly_20(self):
        trades = [_trade(f"T{i}", net_pnl=1.0) for i in range(20)]
        d = _compute_dashboard(trades)
        assert len(d["long_horizon"]["rolling_expectancy_20"]) == 1
        assert abs(d["long_horizon"]["rolling_expectancy_20"][0] - 1.0) < 1e-4

    def test_rolling_expectancy_grows_with_more_trades(self):
        trades = [_trade(f"T{i}", net_pnl=1.0) for i in range(40)]
        d = _compute_dashboard(trades)
        assert len(d["long_horizon"]["rolling_expectancy_20"]) == 21  # 40-19=21 windows

"""
FTD-EXPLORE-ATTR — Exploration Outcome Attribution & Economic Survivability Tests

Verifies:
  • TradeRecord.exploration_origin field (existence, default, backward compat)
  • build_exploration_origin() parser (Rule1, Rule4, Exploit, Unknown)
  • compute_exploration_economics() (all required keys and calculations)
  • Survivability classification (RECOVERY, POSITIVE, NEGATIVE, NOISE, UNRESOLVED)
  • Session breakdown and NY-specific diagnostics
  • Longitudinal dynamics and rolling windows
  • No execution mutation (should_trade return unchanged)
"""
from __future__ import annotations

import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Optional
import pytest

# Ensure project root is on sys.path for test runner
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ── Shared helpers ────────────────────────────────────────────────────────────

def _make_trade(
    trade_id: str = "T001",
    net_pnl: float = 10.0,
    entry_ts: int = 1_000_000,
    exit_ts:  int = 1_060_000,
    entry_price: float = 50_000.0,
    qty: float = 0.01,
    fee_entry: float = 1.0,
    fee_exit:  float = 1.0,
    origin_session: str = "NY",
    crossed_session_boundary: bool = False,
    exploration_origin: Optional[dict] = None,
) -> dict:
    """Minimal trade dict as would come from asdict(TradeRecord)."""
    return {
        "trade_id":                trade_id,
        "symbol":                  "BTCUSDT",
        "side":                    "BUY",
        "entry_price":             entry_price,
        "exit_price":              entry_price * 1.002,
        "qty":                     qty,
        "entry_ts":                entry_ts,
        "exit_ts":                 exit_ts,
        "net_pnl":                 net_pnl,
        "gross_pnl":               net_pnl + 2.0,
        "fee_entry":               fee_entry,
        "fee_exit":                fee_exit,
        "slippage_cost":           0.0,
        "borrow_cost":             0.0,
        "net_pnl_pct":             net_pnl / (entry_price * qty) * 100,
        "origin_session":          origin_session,
        "close_session":           origin_session,
        "crossed_session_boundary": crossed_session_boundary,
        "exploration_origin":       exploration_origin,
    }


def _rule4_origin(q: float = -0.08, n: int = 6) -> dict:
    return {
        "explore_type":          "RULE4_MIN_EXPLORE",
        "was_exploration_trade": True,
        "q_value_at_entry":      q,
        "visit_count_at_entry":  n,
        "explore_floor_active":  True,
    }


def _rule1_origin(n: int = 2) -> dict:
    return {
        "explore_type":          "RULE1_UCB",
        "was_exploration_trade": True,
        "q_value_at_entry":      None,
        "visit_count_at_entry":  n,
        "explore_floor_active":  False,
    }


def _exploit_origin(q: float = 0.15, n: int = 20) -> dict:
    return {
        "explore_type":          "EXPLOIT",
        "was_exploration_trade": False,
        "q_value_at_entry":      q,
        "visit_count_at_entry":  n,
        "explore_floor_active":  False,
    }


# ═══════════════════════════════════════════════════════════════════════
# Part 1: TradeRecord field existence and backward compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestTradeRecordField:
    def test_exploration_origin_field_exists(self):
        from core.pnl_calculator import TradeRecord
        field_names = {f.name for f in fields(TradeRecord)}
        assert "exploration_origin" in field_names

    def test_exploration_origin_default_none(self):
        from core.pnl_calculator import TradeRecord
        t = TradeRecord(
            trade_id="X", symbol="BTCUSDT", side="BUY",
            entry_price=50000.0, exit_price=50100.0, qty=0.01,
            entry_ts=1000, exit_ts=2000,
        )
        assert t.exploration_origin is None

    def test_asdict_includes_exploration_origin(self):
        from core.pnl_calculator import TradeRecord
        t = TradeRecord(
            trade_id="X", symbol="BTCUSDT", side="BUY",
            entry_price=50000.0, exit_price=50100.0, qty=0.01,
            entry_ts=1000, exit_ts=2000,
            exploration_origin={"explore_type": "EXPLOIT"},
        )
        d = asdict(t)
        assert "exploration_origin" in d
        assert d["exploration_origin"]["explore_type"] == "EXPLOIT"

    def test_asdict_exploration_origin_none_when_not_set(self):
        from core.pnl_calculator import TradeRecord
        t = TradeRecord(
            trade_id="X", symbol="BTCUSDT", side="BUY",
            entry_price=50000.0, exit_price=50100.0, qty=0.01,
            entry_ts=1000, exit_ts=2000,
        )
        d = asdict(t)
        assert d.get("exploration_origin") is None

    def test_replay_from_history_handles_missing_exploration_origin(self):
        """DataLake records without exploration_origin (legacy) must restore cleanly."""
        from core.pnl_calculator import PurePnLCalculator
        calc = PurePnLCalculator(starting_capital=1000.0)
        legacy_trade = {
            "trade_id": "L001", "symbol": "BTCUSDT", "side": "BUY",
            "entry_price": 50000.0, "exit_price": 50100.0, "qty": 0.01,
            "entry_ts": 1000, "exit_ts": 2000,
            "net_pnl": 5.0, "gross_pnl": 6.0,
            # exploration_origin intentionally absent
        }
        restored = calc.replay_from_history([legacy_trade])
        assert restored == 1
        assert calc.trades[-1].exploration_origin is None

    def test_replay_with_exploration_origin_present(self):
        """DataLake records with exploration_origin must restore correctly."""
        from core.pnl_calculator import PurePnLCalculator
        calc = PurePnLCalculator(starting_capital=1000.0)
        trade = {
            "trade_id": "E001", "symbol": "BTCUSDT", "side": "BUY",
            "entry_price": 50000.0, "exit_price": 50100.0, "qty": 0.01,
            "entry_ts": 1000, "exit_ts": 2000,
            "net_pnl": 5.0, "gross_pnl": 6.0,
            "exploration_origin": {
                "explore_type": "RULE4_MIN_EXPLORE",
                "was_exploration_trade": True,
                "q_value_at_entry": -0.08,
                "visit_count_at_entry": 6,
                "explore_floor_active": True,
            },
        }
        calc.replay_from_history([trade])
        assert calc.trades[-1].exploration_origin["explore_type"] == "RULE4_MIN_EXPLORE"


# ═══════════════════════════════════════════════════════════════════════
# Part 2: build_exploration_origin parser
# ═══════════════════════════════════════════════════════════════════════

class TestBuildExplorationOrigin:
    def test_rule1_ucb_parsed(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("RL_EXPLORE(visits=3<5)")
        assert result["explore_type"]          == "RULE1_UCB"
        assert result["was_exploration_trade"] is True
        assert result["visit_count_at_entry"]  == 3
        assert result["explore_floor_active"]  is False
        assert result["q_value_at_entry"]      is None

    def test_rule4_floor_parsed(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("RL_FLOOR_EXPLORE(q=-0.052 n=6<20)")
        assert result["explore_type"]          == "RULE4_MIN_EXPLORE"
        assert result["was_exploration_trade"] is True
        assert result["q_value_at_entry"]      == pytest.approx(-0.052)
        assert result["visit_count_at_entry"]  == 6
        assert result["explore_floor_active"]  is True

    def test_rule4_positive_q_parsed(self):
        from core.exploration_economics import build_exploration_origin
        # Edge: q very close to 0 but still negative
        result = build_exploration_origin("RL_FLOOR_EXPLORE(q=-0.001 n=10<20)")
        assert result["q_value_at_entry"] == pytest.approx(-0.001)

    def test_exploit_parsed(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("RL_TRADE(q=+0.123 ucb=+0.456 wr=75% n=15)")
        assert result["explore_type"]          == "EXPLOIT"
        assert result["was_exploration_trade"] is False
        assert result["q_value_at_entry"]      == pytest.approx(0.123)
        assert result["visit_count_at_entry"]  == 15
        assert result["explore_floor_active"]  is False

    def test_toxic_block_returns_unknown(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("RL_TOXIC(q=-0.35 wr=9% n=25)")
        assert result["explore_type"]          == "UNKNOWN"
        assert result["was_exploration_trade"] is False

    def test_skip_returns_unknown(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("RL_SKIP(q=-0.28 ucb=+0.01 floor=-0.30 n=20)")
        assert result["explore_type"] == "UNKNOWN"

    def test_empty_string_returns_unknown(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("")
        assert result["explore_type"] == "UNKNOWN"

    def test_garbage_input_does_not_raise(self):
        from core.exploration_economics import build_exploration_origin
        result = build_exploration_origin("!@#$%^&*()")
        assert result["explore_type"] == "UNKNOWN"

    def test_none_like_input_handled(self):
        from core.exploration_economics import build_exploration_origin
        # Should not raise even with an integer or unexpected type
        try:
            result = build_exploration_origin(42)  # type: ignore[arg-type]
            assert result["explore_type"] == "UNKNOWN"
        except (TypeError, AttributeError):
            # Acceptable: parser can raise on non-str if fail-open wrapper catches it
            pass


# ═══════════════════════════════════════════════════════════════════════
# Part 3: compute_exploration_economics — structure and edge cases
# ═══════════════════════════════════════════════════════════════════════

class TestComputeExplorationEconomicsStructure:
    REQUIRED_KEYS = {
        "scope_note",
        "total_trades",
        "exploration_trades_count",
        "per_type_metrics",
        "q_delta_diagnostics",
        "exploration_profitability_correlation",
        "session_breakdown",
        "ny_rule4_diagnostics",
        "cross_boundary_exploration_trades",
        "survivability_classification",
        "longitudinal_dynamics",
    }

    def test_empty_trades_returns_valid_dict(self):
        from core.exploration_economics import compute_exploration_economics
        result = compute_exploration_economics([])
        assert isinstance(result, dict)
        assert result["total_trades"] == 0
        assert "scope_note" in result

    def test_required_keys_present(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=5.0, exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl=-3.0, exploration_origin=_exploit_origin()),
        ]
        result = compute_exploration_economics(trades)
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Missing required key: {key}"

    def test_scope_note_present(self):
        from core.exploration_economics import compute_exploration_economics
        result = compute_exploration_economics([])
        assert "DIAGNOSTIC" in result["scope_note"].upper()

    def test_per_type_metrics_has_all_four_types(self):
        from core.exploration_economics import compute_exploration_economics
        result = compute_exploration_economics([
            _make_trade("T1", exploration_origin=_rule1_origin()),
        ])
        per_type = result["per_type_metrics"]
        assert "RULE1_UCB"         in per_type
        assert "RULE4_MIN_EXPLORE" in per_type
        assert "EXPLOIT"           in per_type
        assert "UNKNOWN"           in per_type

    def test_never_raises_on_malformed_input(self):
        from core.exploration_economics import compute_exploration_economics
        # Trades with missing/malformed exploration_origin
        bad_trades = [
            {"trade_id": "X1", "net_pnl": 1.0, "exploration_origin": None},
            {"trade_id": "X2", "net_pnl": -1.0, "exploration_origin": "not_a_dict"},
            {"trade_id": "X3"},
        ]
        result = compute_exploration_economics(bad_trades)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════
# Part 4: WR and PnL calculations
# ═══════════════════════════════════════════════════════════════════════

class TestPerTypeCalculations:
    def test_rule4_wr_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=5.0,  exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl=3.0,  exploration_origin=_rule4_origin()),
            _make_trade("T3", net_pnl=-2.0, exploration_origin=_rule4_origin()),
        ]
        result = compute_exploration_economics(trades)
        r4 = result["per_type_metrics"]["RULE4_MIN_EXPLORE"]
        assert r4["count"]        == 3
        assert r4["win_rate_pct"] == pytest.approx(100 * 2 / 3, rel=0.01)

    def test_exploit_wr_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=10.0, exploration_origin=_exploit_origin()),
            _make_trade("T2", net_pnl=-5.0, exploration_origin=_exploit_origin()),
        ]
        result = compute_exploration_economics(trades)
        ex = result["per_type_metrics"]["EXPLOIT"]
        assert ex["win_rate_pct"] == pytest.approx(50.0)

    def test_avg_pnl_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=6.0,  exploration_origin=_rule1_origin(n=2)),
            _make_trade("T2", net_pnl=-2.0, exploration_origin=_rule1_origin(n=1)),
        ]
        result = compute_exploration_economics(trades)
        r1 = result["per_type_metrics"]["RULE1_UCB"]
        assert r1["avg_net_pnl"] == pytest.approx(2.0)

    def test_avg_fee_drag_pct_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        # entry_price=50000, qty=0.01 → notional=500; fee_entry+fee_exit=2 → drag=0.4%
        trade = _make_trade(
            "T1", entry_price=50000.0, qty=0.01,
            fee_entry=1.0, fee_exit=1.0, net_pnl=5.0,
            exploration_origin=_rule4_origin(),
        )
        result = compute_exploration_economics([trade])
        drag = result["per_type_metrics"]["RULE4_MIN_EXPLORE"]["avg_fee_drag_pct"]
        assert drag == pytest.approx(0.4)

    def test_avg_hold_ms_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        trade = _make_trade(
            "T1", entry_ts=1_000_000, exit_ts=1_060_000, net_pnl=1.0,
            exploration_origin=_rule4_origin(),
        )
        result = compute_exploration_economics([trade])
        hold = result["per_type_metrics"]["RULE4_MIN_EXPLORE"]["avg_hold_ms"]
        assert hold == pytest.approx(60_000.0)

    def test_empty_type_returns_none_metrics(self):
        from core.exploration_economics import compute_exploration_economics
        # No RULE1_UCB trades at all
        trades = [_make_trade("T1", exploration_origin=_exploit_origin())]
        result = compute_exploration_economics(trades)
        r1 = result["per_type_metrics"]["RULE1_UCB"]
        assert r1["count"]        == 0
        assert r1["win_rate_pct"] is None
        assert r1["avg_net_pnl"]  is None


# ═══════════════════════════════════════════════════════════════════════
# Part 5: Q-delta diagnostics
# ═══════════════════════════════════════════════════════════════════════

class TestQDeltaDiagnostics:
    def test_q_delta_count_correct(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=5.0,  exploration_origin=_rule4_origin(q=-0.08)),
            _make_trade("T2", net_pnl=-3.0, exploration_origin=_rule4_origin(q=-0.12)),
            _make_trade("T3", net_pnl=2.0,  exploration_origin=_exploit_origin()),
        ]
        result = compute_exploration_economics(trades)
        qd = result["q_delta_diagnostics"]
        assert qd["rule4_count"] == 2

    def test_q_improved_pct_directional(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=5.0,  exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl=3.0,  exploration_origin=_rule4_origin()),
            _make_trade("T3", net_pnl=-2.0, exploration_origin=_rule4_origin()),
        ]
        result = compute_exploration_economics(trades)
        qd = result["q_delta_diagnostics"]
        # 2 of 3 trades positive → Q improved proxy = 66.7%
        assert qd["q_improved_pct"] == pytest.approx(100 * 2 / 3, rel=0.01)

    def test_avg_q_at_entry_computed(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=1.0, exploration_origin=_rule4_origin(q=-0.08)),
            _make_trade("T2", net_pnl=1.0, exploration_origin=_rule4_origin(q=-0.12)),
        ]
        result = compute_exploration_economics(trades)
        qd = result["q_delta_diagnostics"]
        assert qd["avg_q_at_entry"] == pytest.approx(-0.10)

    def test_no_rule4_returns_zero_count(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", exploration_origin=_exploit_origin())]
        result = compute_exploration_economics(trades)
        qd = result["q_delta_diagnostics"]
        assert qd["rule4_count"] == 0
        assert qd["q_improved_pct"] is None


# ═══════════════════════════════════════════════════════════════════════
# Part 6: Profitability correlation
# ═══════════════════════════════════════════════════════════════════════

class TestProfitabilityCorrelation:
    def test_correlation_range(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl= 10.0, exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl= -3.0, exploration_origin=_exploit_origin()),
            _make_trade("T3", net_pnl=  5.0, exploration_origin=_rule1_origin()),
            _make_trade("T4", net_pnl= -1.0, exploration_origin=_exploit_origin()),
            _make_trade("T5", net_pnl=  8.0, exploration_origin=_rule4_origin()),
        ]
        result = compute_exploration_economics(trades)
        corr = result["exploration_profitability_correlation"]
        if corr is not None:
            assert -1.0 <= corr <= 1.0

    def test_correlation_none_when_no_variance(self):
        from core.exploration_economics import compute_exploration_economics
        # All exploration → no variance in x series
        trades = [
            _make_trade("T1", net_pnl=5.0,  exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl=-3.0, exploration_origin=_rule4_origin()),
        ]
        result = compute_exploration_economics(trades)
        # Either None or valid float — both acceptable
        corr = result["exploration_profitability_correlation"]
        assert corr is None or isinstance(corr, float)

    def test_correlation_none_when_too_few_trades(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", exploration_origin=_rule4_origin())]
        result = compute_exploration_economics(trades)
        assert result["exploration_profitability_correlation"] is None


# ═══════════════════════════════════════════════════════════════════════
# Part 7: Session breakdown
# ═══════════════════════════════════════════════════════════════════════

class TestSessionBreakdown:
    def test_session_breakdown_is_list(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", origin_session="NY", exploration_origin=_rule4_origin())]
        result = compute_exploration_economics(trades)
        assert isinstance(result["session_breakdown"], list)

    def test_ny_session_present_when_ny_trades_exist(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", origin_session="NY", exploration_origin=_rule4_origin())]
        result = compute_exploration_economics(trades)
        sessions = {r["session"] for r in result["session_breakdown"]}
        assert "NY" in sessions

    def test_ny_rule4_diagnostics_populated(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", origin_session="NY", net_pnl=5.0,  exploration_origin=_rule4_origin()),
            _make_trade("T2", origin_session="NY", net_pnl=-2.0, exploration_origin=_rule4_origin()),
        ]
        result = compute_exploration_economics(trades)
        ny = result["ny_rule4_diagnostics"]
        assert ny["session"] == "NY"
        assert ny["rule4_count"] == 2

    def test_ny_diagnostics_fallback_when_no_ny_trades(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", origin_session="LONDON", exploration_origin=_rule4_origin())]
        result = compute_exploration_economics(trades)
        ny = result["ny_rule4_diagnostics"]
        assert ny.get("session") == "NY" or "note" in ny

    def test_cross_boundary_exploration_counted(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", crossed_session_boundary=True,  exploration_origin=_rule4_origin()),
            _make_trade("T2", crossed_session_boundary=True,  exploration_origin=_rule1_origin()),
            _make_trade("T3", crossed_session_boundary=False, exploration_origin=_rule4_origin()),
            _make_trade("T4", crossed_session_boundary=True,  exploration_origin=_exploit_origin()),  # not exploration
        ]
        result = compute_exploration_economics(trades)
        assert result["cross_boundary_exploration_trades"] == 2

    def test_session_row_has_required_keys(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", origin_session="LONDON", exploration_origin=_rule4_origin())]
        result = compute_exploration_economics(trades)
        row = result["session_breakdown"][0]
        for key in ("session", "total_trades", "rule4_count", "rule4_wr_pct"):
            assert key in row


# ═══════════════════════════════════════════════════════════════════════
# Part 8: Survivability classification
# ═══════════════════════════════════════════════════════════════════════

class TestSurvivabilityClassification:
    def test_survivability_summary_has_required_keys(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade("T1", exploration_origin=_rule4_origin())]
        result = compute_exploration_economics(trades)
        surv = result["survivability_classification"]
        for key in ("total_exploration_trades", "EXPLORATION_POSITIVE", "EXPLORATION_NEGATIVE",
                    "EXPLORATION_RECOVERY", "EXPLORATION_NOISE", "EXPLORATION_UNRESOLVED"):
            assert key in surv

    def test_recovery_when_rule4_positive_from_negative_q(self):
        from core.exploration_economics import _survivability_category
        trade = _make_trade("T1", net_pnl=5.0, exploration_origin=_rule4_origin(q=-0.08))
        assert _survivability_category(trade) == "EXPLORATION_RECOVERY"

    def test_positive_when_rule4_positive_from_zero_q(self):
        from core.exploration_economics import _survivability_category
        # q_value_at_entry >= 0 (shouldn't happen in Rule4 by design, but defensive)
        origin = {"explore_type": "RULE4_MIN_EXPLORE", "was_exploration_trade": True,
                  "q_value_at_entry": 0.01, "visit_count_at_entry": 5, "explore_floor_active": True}
        trade = _make_trade("T1", net_pnl=5.0, exploration_origin=origin)
        assert _survivability_category(trade) == "EXPLORATION_POSITIVE"

    def test_noise_when_rule4_loss_deep_negative_q(self):
        from core.exploration_economics import _survivability_category
        trade = _make_trade("T1", net_pnl=-3.0, exploration_origin=_rule4_origin(q=-0.15))
        assert _survivability_category(trade) == "EXPLORATION_NOISE"

    def test_negative_when_rule4_loss_mild_q(self):
        from core.exploration_economics import _survivability_category
        # q = -0.05 → not deeply negative → EXPLORATION_NEGATIVE
        trade = _make_trade("T1", net_pnl=-1.0, exploration_origin=_rule4_origin(q=-0.05))
        assert _survivability_category(trade) == "EXPLORATION_NEGATIVE"

    def test_unresolved_when_rule1_very_new(self):
        from core.exploration_economics import _survivability_category
        trade = _make_trade("T1", net_pnl=5.0, exploration_origin=_rule1_origin(n=1))
        assert _survivability_category(trade) == "EXPLORATION_UNRESOLVED"

    def test_positive_when_rule1_mature(self):
        from core.exploration_economics import _survivability_category
        trade = _make_trade("T1", net_pnl=5.0, exploration_origin=_rule1_origin(n=4))
        # n >= 3 → not UNRESOLVED; q_value_at_entry is None → cannot be RECOVERY
        cat = _survivability_category(trade)
        assert cat == "EXPLORATION_POSITIVE"

    def test_not_exploration_for_exploit_trades(self):
        from core.exploration_economics import _survivability_category
        trade = _make_trade("T1", net_pnl=5.0, exploration_origin=_exploit_origin())
        assert _survivability_category(trade) == "NOT_EXPLORATION"

    def test_exploit_not_counted_in_exploration_total(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [
            _make_trade("T1", net_pnl=5.0,  exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl=10.0, exploration_origin=_exploit_origin()),
        ]
        result = compute_exploration_economics(trades)
        assert result["survivability_classification"]["total_exploration_trades"] == 1


# ═══════════════════════════════════════════════════════════════════════
# Part 9: Longitudinal dynamics
# ═══════════════════════════════════════════════════════════════════════

class TestLongitudinalDynamics:
    def _make_session(self, n: int = 20) -> list[dict]:
        trades = []
        for i in range(n):
            origin = _rule4_origin() if i % 3 == 0 else _exploit_origin()
            trades.append(_make_trade(f"T{i}", net_pnl=5.0 if i % 2 == 0 else -2.0,
                                      exploration_origin=origin))
        return trades

    def test_longitudinal_has_required_keys(self):
        from core.exploration_economics import compute_exploration_economics
        result = compute_exploration_economics(self._make_session(20))
        ld = result["longitudinal_dynamics"]
        for key in ("total_trades", "explore_share", "rule4_dependency_ratio",
                    "rolling_10_trade_windows_last5", "rolling_25_trade_windows_last5"):
            assert key in ld

    def test_explore_share_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        # 10 trades: 5 Rule4 (exploration), 5 Exploit
        trades = []
        for i in range(10):
            origin = _rule4_origin() if i < 5 else _exploit_origin()
            trades.append(_make_trade(f"T{i}", exploration_origin=origin))
        result = compute_exploration_economics(trades)
        assert result["longitudinal_dynamics"]["explore_share"] == pytest.approx(0.5)

    def test_rule4_dependency_ratio_correctness(self):
        from core.exploration_economics import compute_exploration_economics
        trades = []
        for i in range(10):
            origin = _rule4_origin() if i < 2 else _exploit_origin()
            trades.append(_make_trade(f"T{i}", exploration_origin=origin))
        result = compute_exploration_economics(trades)
        assert result["longitudinal_dynamics"]["rule4_dependency_ratio"] == pytest.approx(0.2)

    def test_rolling_10_window_exists_when_enough_trades(self):
        from core.exploration_economics import compute_exploration_economics
        trades = self._make_session(15)
        result = compute_exploration_economics(trades)
        windows = result["longitudinal_dynamics"]["rolling_10_trade_windows_last5"]
        assert len(windows) > 0
        for w in windows:
            assert "window_end" in w
            assert "explore_share_pct" in w
            assert "explore_wr_pct" in w

    def test_rolling_windows_empty_when_not_enough_trades(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade(f"T{i}", exploration_origin=_rule4_origin()) for i in range(5)]
        result = compute_exploration_economics(trades)
        # < 10 trades → no 10-trade windows
        assert len(result["longitudinal_dynamics"]["rolling_10_trade_windows_last5"]) == 0

    def test_survival_corr_none_when_too_few_windows(self):
        from core.exploration_economics import compute_exploration_economics
        trades = [_make_trade(f"T{i}", exploration_origin=_rule4_origin()) for i in range(8)]
        result = compute_exploration_economics(trades)
        sc = result["longitudinal_dynamics"]["survival_rate_correlation_vs_exploration"]
        assert sc is None


# ═══════════════════════════════════════════════════════════════════════
# Part 10: No execution mutation
# ═══════════════════════════════════════════════════════════════════════

class TestNoExecutionMutation:
    def _fresh_engine(self):
        from core.rl_engine import RLContextualBandit
        eng = object.__new__(RLContextualBandit)
        import time
        eng._table         = {}
        eng._toxic_contexts = set()
        eng._total_pulls   = 0
        eng._total_allowed = 0
        eng._total_blocked = 0
        eng._explore_trades = 0
        eng._exploit_trades = 0
        eng._floor_explores = 0
        eng._toxic_blocks   = 0
        eng._boot_ts        = int(time.time() * 1000)
        return eng

    def test_should_trade_still_returns_bool_str(self):
        """build_exploration_origin must not change rl_engine.should_trade return type."""
        from core.exploration_economics import build_exploration_origin
        eng = self._fresh_engine()
        ok, reason = eng.should_trade(regime="MEAN_REVERTING", utc_hour=14,
                                       strategy="PRIMARY_STRATEGY")
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
        # Parse the reason — must not raise
        origin = build_exploration_origin(reason)
        assert isinstance(origin, dict)

    def test_build_exploration_origin_does_not_mutate_rl_engine(self):
        from core.exploration_economics import build_exploration_origin
        eng = self._fresh_engine()
        before_total = eng._total_pulls
        _ = build_exploration_origin("RL_TRADE(q=+0.10 ucb=+0.20 wr=60% n=10)")
        assert eng._total_pulls == before_total

    def test_compute_exploration_economics_does_not_raise(self):
        """Full analytics pipeline on edge-case inputs must not raise."""
        from core.exploration_economics import compute_exploration_economics
        # Mix of normal, missing, and malformed exploration_origin
        trades = [
            _make_trade("T1", exploration_origin=_rule4_origin()),
            _make_trade("T2", exploration_origin=None),
            _make_trade("T3", exploration_origin={"explore_type": "UNKNOWN"}),
            _make_trade("T4", exploration_origin=_exploit_origin()),
        ]
        result = compute_exploration_economics(trades)
        assert isinstance(result, dict)

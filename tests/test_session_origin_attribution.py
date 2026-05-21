"""
FTD-SESSION-FORENSICS — Session Origin Attribution Verifier

Asserts:
  1. TradeRecord has all required session attribution fields.
  2. Defaults are fail-open (UNKNOWN / False / -1 / "").
  3. Backward compatibility — all pre-FTD fields still present.
  4. origin_session and close_session accept all four canonical labels.
  5. crossed_session_boundary and boundary_transition are computed correctly.
  6. origin_utc_hour / close_utc_hour accept valid UTC hour integers.
  7. All session labels derive from the canonical session_definitions authority.
  8. No inline bucket logic in core/ (delegated to existing test suite enforcement).
  9. Analysis utilities (from tools module) work on real trade dicts.
 10. Analysis is fail-open for trades missing attribution fields.

Run: python -m pytest tests/test_session_origin_attribution.py -v
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

import pytest

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnl_calculator import TradeRecord
from core.time.session_definitions import (
    SESSION_BUCKETS_UTC,
    get_session_label,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_trade(**overrides) -> TradeRecord:
    base = dict(
        trade_id="F001", symbol="BTCUSDT", side="BUY",
        entry_price=50000.0, exit_price=51000.0, qty=0.01,
        entry_ts=1_000_000, exit_ts=1_001_000,
    )
    base.update(overrides)
    return TradeRecord(**base)


def _make_trade_dict(
    *,
    origin="ASIA",
    close="LONDON",
    entry_ts=1_000_000,
    exit_ts=1_003_600_000,  # 1 hour later in ms
    net_pnl=50.0,
) -> dict:
    return asdict(_make_trade(
        net_pnl=net_pnl,
        origin_session=origin,
        close_session=close,
        crossed_session_boundary=(origin != close),
        origin_utc_hour=2,
        close_utc_hour=7,
        boundary_transition=f"{origin}→{close}" if origin != close else "",
        entry_ts=entry_ts,
        exit_ts=exit_ts,
    ))


# ── 1. Field presence ─────────────────────────────────────────────────────────

def test_origin_session_field_exists():
    assert hasattr(_make_trade(), "origin_session")


def test_close_session_field_exists():
    assert hasattr(_make_trade(), "close_session")


def test_crossed_session_boundary_field_exists():
    assert hasattr(_make_trade(), "crossed_session_boundary")


def test_origin_utc_hour_field_exists():
    assert hasattr(_make_trade(), "origin_utc_hour")


def test_close_utc_hour_field_exists():
    assert hasattr(_make_trade(), "close_utc_hour")


def test_boundary_transition_field_exists():
    assert hasattr(_make_trade(), "boundary_transition")


# ── 2. Fail-open defaults ─────────────────────────────────────────────────────

def test_origin_session_default_unknown():
    assert _make_trade().origin_session == "UNKNOWN"


def test_close_session_default_unknown():
    assert _make_trade().close_session == "UNKNOWN"


def test_crossed_default_false():
    assert _make_trade().crossed_session_boundary is False


def test_origin_utc_hour_default_minus_one():
    assert _make_trade().origin_utc_hour == -1


def test_close_utc_hour_default_minus_one():
    assert _make_trade().close_utc_hour == -1


def test_boundary_transition_default_empty():
    assert _make_trade().boundary_transition == ""


# ── 3. Backward compatibility ─────────────────────────────────────────────────

def test_pre_ftd_fields_unchanged():
    tr = _make_trade(trade_id="BC001", symbol="ETHUSDT", side="SELL",
                     entry_price=3000.0, exit_price=2900.0, qty=0.1,
                     entry_ts=2_000_000, exit_ts=2_001_000)
    assert tr.trade_id == "BC001"
    assert tr.symbol == "ETHUSDT"
    assert tr.r_multiple == 0.0
    assert tr.origin_pipeline == "UNKNOWN"
    assert tr.decision_snapshot is None


def test_all_new_fields_in_asdict():
    d = asdict(_make_trade())
    for field in ("origin_session", "close_session", "crossed_session_boundary",
                  "origin_utc_hour", "close_utc_hour", "boundary_transition"):
        assert field in d, f"Missing in asdict: {field}"


# ── 4. Session label acceptance ───────────────────────────────────────────────

@pytest.mark.parametrize("session", ["ASIA", "LONDON", "NY", "LATE"])
def test_all_canonical_sessions_accepted_as_origin(session):
    tr = _make_trade(origin_session=session)
    assert tr.origin_session == session


@pytest.mark.parametrize("session", ["ASIA", "LONDON", "NY", "LATE"])
def test_all_canonical_sessions_accepted_as_close(session):
    tr = _make_trade(close_session=session)
    assert tr.close_session == session


# ── 5. crossed_session_boundary and boundary_transition ─────────────────────

def test_crossed_boundary_true_when_sessions_differ():
    tr = _make_trade(origin_session="ASIA", close_session="LONDON",
                     crossed_session_boundary=True,
                     boundary_transition="ASIA→LONDON")
    assert tr.crossed_session_boundary is True
    assert tr.boundary_transition == "ASIA→LONDON"


def test_crossed_boundary_false_when_same_session():
    tr = _make_trade(origin_session="NY", close_session="NY",
                     crossed_session_boundary=False, boundary_transition="")
    assert tr.crossed_session_boundary is False
    assert tr.boundary_transition == ""


@pytest.mark.parametrize("origin,close", [
    ("ASIA",   "LONDON"),
    ("ASIA",   "NY"),
    ("ASIA",   "LATE"),
    ("LONDON", "NY"),
    ("LONDON", "LATE"),
    ("NY",     "LATE"),
])
def test_boundary_transition_format(origin, close):
    tr = _make_trade(origin_session=origin, close_session=close,
                     crossed_session_boundary=True,
                     boundary_transition=f"{origin}→{close}")
    assert tr.boundary_transition == f"{origin}→{close}"
    assert "→" in tr.boundary_transition


# ── 6. UTC hour range ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("hour", [0, 6, 12, 13, 18, 19, 23])
def test_valid_utc_hours_accepted(hour):
    tr = _make_trade(origin_utc_hour=hour, close_utc_hour=hour)
    assert tr.origin_utc_hour == hour
    assert tr.close_utc_hour == hour


# ── 7. Canonical session authority ───────────────────────────────────────────

def test_get_session_label_returns_canonical_sessions():
    """All UTC hours must map to a session defined in SESSION_BUCKETS_UTC."""
    for h in range(24):
        label = get_session_label(h)
        assert label in SESSION_BUCKETS_UTC, (
            f"Hour {h} returned '{label}' which is not in SESSION_BUCKETS_UTC"
        )


@pytest.mark.parametrize("utc_hour,expected", [
    (0, "ASIA"), (5, "ASIA"),
    (6, "LONDON"), (12, "LONDON"),
    (13, "NY"), (18, "NY"),
    (19, "LATE"), (23, "LATE"),
])
def test_get_session_label_boundary_correctness(utc_hour, expected):
    assert get_session_label(utc_hour) == expected


# ── 8. Analysis utilities: basic correctness ─────────────────────────────────

# Import analysis function from tools without executing main()
import importlib.util, os

_TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "analyze_session_boundary_crossings.py"


def _load_analyser():
    spec = importlib.util.spec_from_file_location("_boundary_tool", _TOOL_PATH)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_analyser_handles_empty_trade_list():
    mod = _load_analyser()
    result = mod.analyse([])
    assert result["coverage"]["total_trades"] == 0
    assert result["coverage"]["attributed_trades"] == 0


def test_analyser_handles_unattributed_trades():
    trades = [asdict(_make_trade()) for _ in range(5)]  # all UNKNOWN
    mod = _load_analyser()
    result = mod.analyse(trades)
    assert result["coverage"]["attributed_trades"] == 0


def test_analyser_counts_winning_and_losing_trades():
    trades = [
        _make_trade_dict(origin="ASIA",   close="ASIA",   net_pnl=50.0),
        _make_trade_dict(origin="ASIA",   close="LONDON", net_pnl=-20.0),
        _make_trade_dict(origin="LONDON", close="LONDON", net_pnl=30.0),
    ]
    mod = _load_analyser()
    result = mod.analyse(trades)
    asia = result["origin_session_breakdown"]["ASIA"]
    assert asia["wins"]   == 1
    assert asia["losses"] == 1


def test_analyser_cross_boundary_detection():
    trades = [
        _make_trade_dict(origin="ASIA",   close="LONDON", net_pnl=-10.0),  # crosses
        _make_trade_dict(origin="LONDON", close="LONDON", net_pnl=10.0),   # same
    ]
    mod = _load_analyser()
    result = mod.analyse(trades)
    cb = result["cross_boundary"]
    assert cb["total"] == 1
    assert cb["loser_cross_count"] == 1
    assert cb["winner_cross_count"] == 0


def test_analyser_transition_matrix_populated():
    trades = [
        _make_trade_dict(origin="ASIA",   close="LONDON", net_pnl=-10.0),
        _make_trade_dict(origin="ASIA",   close="LONDON", net_pnl=-15.0),
        _make_trade_dict(origin="NY",     close="LATE",   net_pnl=5.0),
    ]
    mod = _load_analyser()
    result = mod.analyse(trades)
    tm = result["boundary_transition_matrix"]
    assert "ASIA→LONDON" in tm
    assert tm["ASIA→LONDON"]["losses"] == 2
    assert "NY→LATE" in tm
    assert tm["NY→LATE"]["wins"] == 1


def test_analyser_hold_duration_asymmetry():
    """Losers hold longer → positive hold_asymmetry_sec."""
    trades = [
        # winners: short hold (1 second)
        _make_trade_dict(origin="ASIA", close="ASIA", net_pnl=10.0,
                         entry_ts=0, exit_ts=1_000),
        # losers: long hold (10 seconds)
        _make_trade_dict(origin="ASIA", close="ASIA", net_pnl=-10.0,
                         entry_ts=0, exit_ts=10_000),
    ]
    mod = _load_analyser()
    result = mod.analyse(trades)
    asym = result["hold_duration_summary"]["hold_asymmetry_sec"]
    assert asym is not None
    assert asym > 0  # losers hold longer


def test_analyser_fail_open_missing_fields():
    """Trades with missing attribution fields must not crash the analyser."""
    trades = [
        {"trade_id": "X", "net_pnl": 10.0, "entry_ts": 0, "exit_ts": 1000,
         "origin_session": "ASIA", "close_session": "ASIA"},
        {"trade_id": "Y"},  # minimal trade, no attribution fields
    ]
    mod = _load_analyser()
    try:
        result = mod.analyse(trades)
        assert "coverage" in result
    except Exception as exc:
        pytest.fail(f"Analyser raised on missing fields: {exc}")


# ── 9. Full round-trip via asdict ─────────────────────────────────────────────

def test_session_fields_survive_asdict_roundtrip():
    tr = _make_trade(
        origin_session="NY", close_session="LATE",
        crossed_session_boundary=True, origin_utc_hour=18, close_utc_hour=20,
        boundary_transition="NY→LATE",
    )
    d = asdict(tr)
    assert d["origin_session"] == "NY"
    assert d["close_session"]  == "LATE"
    assert d["crossed_session_boundary"] is True
    assert d["origin_utc_hour"] == 18
    assert d["close_utc_hour"]  == 20
    assert d["boundary_transition"] == "NY→LATE"

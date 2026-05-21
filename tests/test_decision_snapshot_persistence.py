"""
FTD-DECISION-SNAP — Decision Snapshot Persistence Verifier

Asserts:
  1. TradeRecord.decision_snapshot field is present with correct default.
  2. Backward compatibility: all pre-FTD fields remain accessible.
  3. Partial snapshots (missing subsystem fields) are accepted without error.
  4. Suppression events append correctly to JSONL log.
  5. Suppression log is append-only across multiple instances.
  6. Suppression log is fail-open (bad path never raises).
  7. Every suppression event contains all required schema fields.
  8. Pipeline detection in suppression events is correct.
  9. Session label in suppression events is correct.
 10. Snapshot RL block and ecology block have expected structures.

Run: python -m pytest tests/test_decision_snapshot_persistence.py -v
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from core.pnl_calculator import TradeRecord
from core.persistence.suppression_log import SuppressionEventLog


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_trade(**kwargs) -> TradeRecord:
    defaults = dict(
        trade_id="T001", symbol="BTCUSDT", side="BUY",
        entry_price=50000.0, exit_price=51000.0, qty=0.01,
        entry_ts=1_000_000, exit_ts=1_000_100,
    )
    defaults.update(kwargs)
    return TradeRecord(**defaults)


# ── 1. Field presence and defaults ───────────────────────────────────────────

def test_decision_snapshot_field_exists():
    tr = _make_trade()
    assert hasattr(tr, "decision_snapshot")


def test_decision_snapshot_default_is_none():
    tr = _make_trade()
    assert tr.decision_snapshot is None


def test_decision_snapshot_shows_in_asdict():
    tr = _make_trade()
    d = asdict(tr)
    assert "decision_snapshot" in d
    assert d["decision_snapshot"] is None


# ── 2. Backward compatibility ─────────────────────────────────────────────────

def test_all_pre_ftd_fields_still_present():
    tr = _make_trade(trade_id="BW001", symbol="ETHUSDT", side="SELL",
                     entry_price=3000.0, exit_price=2900.0, qty=0.1,
                     entry_ts=2_000_000, exit_ts=2_000_200)
    assert tr.trade_id == "BW001"
    assert tr.symbol == "ETHUSDT"
    assert tr.is_short is False
    assert tr.gross_pnl == 0.0
    assert tr.net_pnl == 0.0
    assert tr.r_multiple == 0.0
    assert tr.origin_pipeline == "UNKNOWN"
    assert tr.decision_snapshot is None


def test_origin_pipeline_field_still_defaults_unknown():
    tr = _make_trade()
    assert tr.origin_pipeline == "UNKNOWN"


# ── 3. Snapshot acceptance ───────────────────────────────────────────────────

def test_full_snapshot_accepted():
    snap = {
        "pipeline": "PAPER_SPEED",
        "utc_hour": 14,
        "session_label": "NY",
        "rl": {
            "context": "MEAN_REVERTING|NY|MeanReversion",
            "q_value": -0.142,
            "n_visits": 22,
            "ev_floor": -0.30,
            "approved": True,
            "reason": "RL_TRADE",
        },
        "ecology": {
            "verdict": "PASS",
            "block_reason": None,
            "regime": "MEAN_REVERTING",
            "rsi_value": 27.4,
            "context_type": "PROFITABLE",
            "boost_mult": 1.25,
            "survival_rate": 0.73,
            "size_multiplier": 1.0,
        },
        "alpha_context": {
            "boost_mult": 1.25,
            "context_type": "PROFITABLE",
            "boost_reason": "embedded_in_ecology_decision",
        },
    }
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["pipeline"] == "PAPER_SPEED"
    assert tr.decision_snapshot["rl"]["q_value"] == -0.142
    assert tr.decision_snapshot["ecology"]["verdict"] == "PASS"
    assert tr.decision_snapshot["ecology"]["rsi_value"] == 27.4


def test_partial_snapshot_accepted():
    """Missing subsystem blocks are valid — fail-open contract."""
    snap = {"pipeline": "PRIMARY_STRATEGY", "utc_hour": 7}
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["pipeline"] == "PRIMARY_STRATEGY"
    assert "ecology" not in tr.decision_snapshot
    assert "rl" not in tr.decision_snapshot


def test_empty_snapshot_accepted():
    tr = _make_trade(decision_snapshot={})
    assert tr.decision_snapshot == {}


def test_snapshot_with_only_session_fields():
    snap = {"pipeline": "PRIMARY_STRATEGY", "utc_hour": 6, "session_label": "LONDON"}
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["session_label"] == "LONDON"


# ── 4. Snapshot RL block structure ────────────────────────────────────────────

def test_rl_block_has_required_keys():
    rl = {
        "context": "TRENDING|LONDON|TrendFollowing",
        "q_value": 0.12,
        "n_visits": 8,
        "ev_floor": -0.30,
        "approved": True,
        "reason": "RL_TRADE",
    }
    snap = {"pipeline": "PRIMARY_STRATEGY", "utc_hour": 7, "rl": rl}
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["rl"]["ev_floor"] == -0.30
    assert tr.decision_snapshot["rl"]["approved"] is True
    assert tr.decision_snapshot["rl"]["n_visits"] == 8


def test_rl_block_q_value_none_is_valid():
    """Cold-start contexts have no q_value — None is acceptable."""
    rl = {"context": "X|Y|Z", "q_value": None, "n_visits": 0,
          "ev_floor": -0.30, "approved": True, "reason": "RL_EXPLORE"}
    snap = {"pipeline": "PRIMARY_STRATEGY", "utc_hour": 3, "rl": rl}
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["rl"]["q_value"] is None


# ── 5. Snapshot ecology block: NOT_EVALUATED for PRIMARY_STRATEGY ─────────────

def test_ecology_not_evaluated_for_primary_strategy():
    snap = {
        "pipeline": "PRIMARY_STRATEGY",
        "utc_hour": 14,
        "ecology": {
            "verdict": "NOT_EVALUATED",
            "reason": "PRIMARY_STRATEGY signals bypass ecology gate",
        },
    }
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["ecology"]["verdict"] == "NOT_EVALUATED"


def test_ecology_pass_for_paper_speed():
    snap = {
        "pipeline": "PAPER_SPEED",
        "utc_hour": 3,
        "ecology": {
            "verdict": "PASS",
            "regime": "MEAN_REVERTING",
            "rsi_value": 29.1,
        },
    }
    tr = _make_trade(decision_snapshot=snap)
    assert tr.decision_snapshot["ecology"]["verdict"] == "PASS"


# ── 6. Pipeline + snapshot consistency ───────────────────────────────────────

def test_origin_pipeline_matches_snapshot_pipeline():
    snap = {"pipeline": "PAPER_SPEED", "utc_hour": 2, "session_label": "ASIA"}
    tr = _make_trade(origin_pipeline="PAPER_SPEED", decision_snapshot=snap)
    assert tr.origin_pipeline == tr.decision_snapshot["pipeline"]


# ── 7. Suppression event log — basic ─────────────────────────────────────────

def test_suppression_log_creates_file(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    log.record(gate="RL_GATE", symbol="BTCUSDT", strategy="MeanReversion",
               regime="MEAN_REVERTING", utc_hour=14, reason="RL_SKIP(q=-0.35)")
    assert (tmp_path / "sup.jsonl").exists()


def test_suppression_log_event_is_valid_json(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    log.record(gate="RL_GATE", symbol="BTCUSDT", strategy="MeanReversion",
               regime="MEAN_REVERTING", utc_hour=14, reason="RL_SKIP")
    line = (tmp_path / "sup.jsonl").read_text().strip()
    event = json.loads(line)
    assert isinstance(event, dict)


def test_suppression_log_required_schema_fields(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    log.record(gate="LEAN_GATE", symbol="ETHUSDT", strategy="TrendFollowing",
               regime="TRENDING", utc_hour=9)
    event = json.loads((tmp_path / "sup.jsonl").read_text().strip())
    for field in ("utc_ts", "symbol", "strategy", "pipeline", "gate", "session", "regime"):
        assert field in event, f"Required field missing: {field}"


def test_suppression_log_multiple_events_appended(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    for i in range(5):
        log.record(gate="LEAN_GATE", symbol="ETHUSDT", strategy="TrendFollowing",
                   regime="TRENDING", utc_hour=6, reason=f"reason_{i}")
    lines = (tmp_path / "sup.jsonl").read_text().strip().splitlines()
    assert len(lines) == 5


# ── 8. Pipeline detection in suppression events ───────────────────────────────

def test_paper_speed_pipeline_detected(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    log.record(gate="ECOLOGY", symbol="BTCUSDT",
               strategy="MeanReversion_PAPER_SPEED",
               regime="MEAN_REVERTING", utc_hour=2)
    event = json.loads((tmp_path / "sup.jsonl").read_text().strip())
    assert event["pipeline"] == "PAPER_SPEED"


def test_primary_strategy_pipeline_detected(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    log.record(gate="RL_GATE", symbol="BTCUSDT",
               strategy="TrendFollowing",
               regime="TRENDING", utc_hour=14)
    event = json.loads((tmp_path / "sup.jsonl").read_text().strip())
    assert event["pipeline"] == "PRIMARY_STRATEGY"


# ── 9. Session label in suppression events ────────────────────────────────────

@pytest.mark.parametrize("utc_hour,expected_session", [
    (0,  "ASIA"), (5, "ASIA"),
    (6,  "LONDON"), (12, "LONDON"),
    (13, "NY"), (18, "NY"),
    (19, "LATE"), (23, "LATE"),
])
def test_suppression_session_label(tmp_path, utc_hour, expected_session):
    log = SuppressionEventLog(path=tmp_path / f"sup_{utc_hour}.jsonl")
    log.record(gate="TEST", symbol="X", strategy="S",
               regime="TRENDING", utc_hour=utc_hour)
    event = json.loads((tmp_path / f"sup_{utc_hour}.jsonl").read_text().strip())
    assert event["session"] == expected_session


# ── 10. Append-only and fail-open guarantees ─────────────────────────────────

def test_suppression_log_append_only_across_instances(tmp_path):
    log_path = tmp_path / "sup.jsonl"
    log1 = SuppressionEventLog(path=log_path)
    log1.record(gate="RL_GATE", symbol="A", strategy="S", regime="R", utc_hour=0)
    log2 = SuppressionEventLog(path=log_path)
    log2.record(gate="LEAN_GATE", symbol="B", strategy="S", regime="R", utc_hour=1)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["gate"] == "RL_GATE"
    assert json.loads(lines[1])["gate"] == "LEAN_GATE"


def test_suppression_log_fail_open_bad_path():
    """SuppressionEventLog.record() must never raise, even with an impossible path."""
    bad_log = SuppressionEventLog(path=Path("/root/nonexistent_dir/sup.jsonl"))
    try:
        bad_log.record(gate="TEST", symbol="X", strategy="Y",
                       regime="Z", utc_hour=0, reason="test")
    except Exception as exc:
        pytest.fail(f"Suppression log raised unexpectedly: {exc}")


def test_suppression_log_empty_reason_is_ok(tmp_path):
    log = SuppressionEventLog(path=tmp_path / "sup.jsonl")
    log.record(gate="DRAWDOWN_CONTROLLER", symbol="SOLUSDT",
               strategy="TrendFollowing", regime="TRENDING", utc_hour=20)
    event = json.loads((tmp_path / "sup.jsonl").read_text().strip())
    assert "reason" in event
    assert event["reason"] == ""

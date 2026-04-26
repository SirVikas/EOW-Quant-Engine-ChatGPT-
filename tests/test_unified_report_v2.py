"""
Tests for FTD-025B-URX-V2: Unified Report Engine v2.

Spec requirements (all must pass):
  ✔ No empty sections
  ✔ Signal count matches trade logic
  ✔ Rejection reasons exist
  ✔ Learning memory not empty
  ✔ Root cause present
  ✔ Action plan generated
"""
import pytest
from core.reporting.unified_report_engine_v2 import generate_full_report_v2


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _minimal_data(**overrides) -> dict:
    """Minimal valid data dict for report generation."""
    base = {
        "generated_at": "2026-04-26 00:00:00 UTC",
        "trade_flow": {
            "total_signals":          15,
            "total_trades":            2,
            "total_skips":            13,
            "rejection_rate_pct":     86.7,
            "signals_per_hour":       30.0,
            "trades_per_hour":         4.0,
            "minutes_since_last_trade": 5.0,
            "top_rejection_reasons":  {"LOW_SCORE": 8, "ATR_TOO_LOW": 5},
        },
        "mins_idle": 5.0,
        "thresholds": {
            "tier":             "NORMAL",
            "score_min":         0.58,
            "volume_multiplier": 1.0,
            "af_state":         "NORMAL",
        },
        "session_stats": {
            "n_trades":          2,
            "win_rate":         50.0,
            "profit_factor":     1.25,
            "avg_win_usdt":      2.50,
            "avg_loss_usdt":    -1.80,
            "total_net_pnl":     0.70,
            "total_fees_paid":   0.30,
            "initial_capital": 1000.0,
            "final_equity":   1000.70,
        },
        "capital": {
            "max_capital_pct":    0.05,
            "daily_risk_cap":     0.03,
            "daily_risk_used":    0.02,
            "daily_risk_remaining": 0.01,
        },
        "risk": {
            "halted":        False,
            "halt_reason":   None,
            "graceful_stop": False,
        },
        "gate": {
            "can_trade": True,
            "reason":    "ALL_CLEAR",
        },
        "errors": [],
        "learning_memory": {
            "status":                    "ACTIVE",
            "memory_records":             0,
            "total_patterns":             0,
            "formed_patterns":            0,
            "negative_memory_permanent":  0,
            "negative_memory_temporary":  0,
        },
        "ct_scan": {},
        "ai_brain": {
            "mode":     "NORMAL",
            "decision": "MONITOR — assess next candle",
        },
        "drawdown": {
            "state":                  "NORMAL",
            "current_drawdown_pct":   0.0,
            "max_drawdown_pct":       5.0,
            "size_multiplier":        1.0,
        },
        "activator": {
            "tier":   "NORMAL",
            "active": False,
        },
        "edge_engine": {
            "strategies": {},
        },
        "thoughts": [],
    }
    base.update(overrides)
    return base


# ── Core requirement tests ────────────────────────────────────────────────────

def test_report_is_non_empty():
    report = generate_full_report_v2(_minimal_data())
    assert len(report) > 500, "Report too short — likely missing content"


def test_all_11_sections_present():
    report = generate_full_report_v2(_minimal_data())
    for i in range(1, 12):
        assert f"## {i}." in report, f"Section {i} missing from report"


def test_no_section_is_empty():
    report = generate_full_report_v2(_minimal_data())
    sections = report.split("## ")
    for section in sections[1:]:  # skip header
        title_end = section.find("\n")
        body = section[title_end:].strip()
        assert len(body) > 10, f"Section '{section[:40]}...' appears empty"


def test_signal_flow_shows_rejection_reasons():
    data = _minimal_data()
    report = generate_full_report_v2(data)
    # Section 2 must mention rejection reasons
    assert "LOW_SCORE" in report or "ATR_TOO_LOW" in report or "Top Rejection Reasons" in report


def test_signal_count_matches_trade_logic():
    data = _minimal_data()
    report = generate_full_report_v2(data)
    # Signals generated (15) and skips (13) appear in section 2
    assert "15" in report
    assert "13" in report


def test_learning_memory_section_not_empty():
    report = generate_full_report_v2(_minimal_data())
    # Section 7 must contain a status line
    assert "ACTIVE" in report or "learning engine" in report.lower()


def test_root_cause_section_present():
    report = generate_full_report_v2(_minimal_data())
    assert "PRIMARY CAUSE" in report
    assert "SECONDARY CAUSE" in report


def test_action_plan_has_all_three_horizons():
    report = generate_full_report_v2(_minimal_data())
    assert "IMMEDIATE" in report
    assert "SHORT TERM" in report
    assert "LONG TERM" in report


def test_developer_export_has_structured_block():
    report = generate_full_report_v2(_minimal_data())
    # Section 11 must contain a code block
    assert "```" in report


# ── Scenario: system in loss ──────────────────────────────────────────────────

def test_loss_scenario_triggers_pf_alert():
    data = _minimal_data()
    data["session_stats"].update({
        "n_trades":       131,
        "win_rate":       48.9,
        "profit_factor":  0.37,
        "avg_win_usdt":   1.25,
        "avg_loss_usdt": -3.25,
        "total_net_pnl": -137.43,
        "total_fees_paid": 45.77,
    })
    report = generate_full_report_v2(data)
    assert "LOW PROFIT FACTOR" in report or "0.37" in report
    assert "LOSS" in report


def test_idle_scenario_triggers_dry_spell_alert():
    data = _minimal_data(mins_idle=130.0)
    data["trade_flow"]["minutes_since_last_trade"] = 130.0
    report = generate_full_report_v2(data)
    assert "IDLE" in report or "dry" in report.lower() or "130" in report


# ── Scenario: system blocked ──────────────────────────────────────────────────

def test_blocked_gate_shows_in_executive_snapshot():
    data = _minimal_data()
    data["gate"] = {"can_trade": False, "reason": "INDICATORS_NOT_READY"}
    report = generate_full_report_v2(data)
    assert "BLOCKED" in report


def test_halted_system_shows_halt_alert():
    data = _minimal_data()
    data["risk"]["halted"] = True
    data["risk"]["halt_reason"] = "DRAWDOWN_STOP"
    report = generate_full_report_v2(data)
    assert "HALT" in report


# ── Scenario: TIER_3 relaxation ──────────────────────────────────────────────

def test_tier3_shows_in_thresholds_and_decision():
    data = _minimal_data(mins_idle=35.0)
    data["thresholds"].update({
        "tier":             "TIER_3",
        "score_min":         0.42,
        "volume_multiplier": 0.20,
        "af_state":         "RELAX",
    })
    report = generate_full_report_v2(data)
    assert "TIER_3" in report
    assert "RELAX" in report


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_data_does_not_raise():
    # Should not crash even with an empty dict
    report = generate_full_report_v2({})
    assert len(report) > 100


def test_recurring_error_shows_in_alerts():
    errors = [
        {"code": "DATA_002", "extra": "ATR_TOO_LOW(0.009%<0.01%)"}
        for _ in range(10)
    ]
    data = _minimal_data()
    data["errors"] = errors
    report = generate_full_report_v2(data)
    assert "DATA_002" in report or "ATR_TOO_LOW" in report


def test_negative_memory_shows_warning():
    data = _minimal_data()
    data["learning_memory"]["formed_patterns"] = 3
    data["learning_memory"]["negative_memory_permanent"] = 2
    report = generate_full_report_v2(data)
    assert "banned" in report.lower() or "permanent" in report.lower()

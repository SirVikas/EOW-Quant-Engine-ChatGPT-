"""
Tests for FTD-025B-URX-V2 + FTD-025C-TRUTH-LAYER-V1: Unified Report Engine v2.

Spec requirements (all must pass):
  ✔ No empty sections
  ✔ Signal count matches trade logic
  ✔ Rejection reasons exist
  ✔ Learning memory not empty
  ✔ Root cause present
  ✔ Action plan generated
  ✔ [FTD-025C] Contradiction detection
  ✔ [FTD-025C] Root cause forced when signals>0 & trades=0
  ✔ [FTD-025C] Capital idle missed opportunity logic
  ✔ [FTD-025C] Session/historical separation
  ✔ [FTD-025C] Alert generation correctness
"""
import pytest
from core.reporting.unified_report_engine_v2 import generate_full_report_v2
from core.reporting.truth_engine import (
    detect_contradictions,
    validate_signal_flow,
    split_metrics,
    analyze_capital_efficiency,
    resolve_root_cause,
    generate_alerts,
    process as truth_process,
)


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


# ── FTD-025C: Truth Engine unit tests ────────────────────────────────────────

def _sleep_mode_data(**overrides) -> dict:
    """Data matching the live unified_report_v2_1777172458 scenario (SLEEP_MODE block)."""
    base = _minimal_data()
    base["trade_flow"].update({
        "total_signals": 13,
        "total_trades":  0,
        "total_skips":   6,
        "rejection_rate_pct": 100.0,
        "signals_per_hour": 13.0,
        "trades_per_hour":   0.0,
        "minutes_since_last_trade": 0.6,
        "top_rejection_reasons": {"SLEEP_MODE": 6},
    })
    base["mins_idle"] = 0.6
    base["session_stats"].update({
        "n_trades":        0,
        "win_rate":       48.9,
        "profit_factor":   0.37,
        "avg_win_usdt":    1.24,
        "avg_loss_usdt":  -3.20,
        "total_net_pnl": -137.43,
        "total_fees_paid": 45.77,
    })
    base.update(overrides)
    return base


def test_contradiction_signals_no_trades_detected():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    ids = [c["id"] for c in contradictions]
    assert "SIGNALS_NO_TRADES" in ids, "SIGNALS_NO_TRADES contradiction must be detected"


def test_contradiction_gating_block_invisible_detected():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    ids = [c["id"] for c in contradictions]
    assert "GATING_BLOCK_INVISIBLE" in ids, "GATING_BLOCK_INVISIBLE contradiction must be detected"


def test_contradiction_session_historical_mix_detected():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    ids = [c["id"] for c in contradictions]
    assert "SESSION_HISTORICAL_MIX" in ids, (
        "SESSION_HISTORICAL_MIX must be detected when n_trades=0 but win_rate populated"
    )


def test_root_cause_forced_when_signals_no_trades():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    rc = resolve_root_cause(data, contradictions)
    assert rc["has_issue"] is True, "Root cause must flag an issue when signals>0 and trades=0"
    assert "SLEEP_MODE" in rc["primary"], "Root cause must name SLEEP_MODE as the blocking cause"
    assert "No critical root cause identified" not in rc["primary"]


def test_root_cause_never_empty_with_contradictions():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    assert len(contradictions) > 0, "Contradictions must exist in sleep mode scenario"
    rc = resolve_root_cause(data, contradictions)
    assert rc["primary"] is not None and len(rc["primary"]) > 0


def test_capital_idle_missed_opportunity_when_signals_blocked():
    data = _sleep_mode_data()
    result = analyze_capital_efficiency(data)
    assert result["missed_opportunity"] is True, (
        "missed_opportunity must be True when signals>0 but trades=0"
    )
    assert "SLEEP_MODE" in result["missed_reason"]


def test_capital_idle_no_missed_when_no_signals():
    data = _minimal_data()
    data["trade_flow"]["total_signals"] = 0
    data["trade_flow"]["total_trades"]  = 0
    result = analyze_capital_efficiency(data)
    assert result["missed_opportunity"] is False


def test_session_historical_split_is_mixed():
    data = _sleep_mode_data()
    result = split_metrics(data)
    assert result["is_mixed"] is True, (
        "is_mixed must be True when session trades=0 but historical win_rate populated"
    )
    assert result["session"]["n_trades"] == 0
    assert result["historical"]["win_rate"] == 48.9


def test_session_historical_split_not_mixed_normal():
    data = _minimal_data()
    result = split_metrics(data)
    assert result["is_mixed"] is False, "Normal scenario (trades=2) must not be mixed"


def test_alert_no_trade_alert_generated_for_sleep_mode():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    alerts = generate_alerts(data, contradictions)
    types = [a["type"] for a in alerts]
    assert "NO_TRADE_ALERT" in types, "NO_TRADE_ALERT must be generated when trades=0 and signals>0"


def test_alert_signal_rejection_spike_for_sleep_mode():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    alerts = generate_alerts(data, contradictions)
    titles_combined = " ".join(a["title"] for a in alerts)
    assert "SLEEP_MODE" in titles_combined


def test_alert_contradiction_detected_for_mixed_metrics():
    data = _sleep_mode_data()
    contradictions = detect_contradictions(data)
    alerts = generate_alerts(data, contradictions)
    types = [a["type"] for a in alerts]
    assert "CONTRADICTION_DETECTED" in types


def test_report_shows_blocked_not_active_when_sleep_mode():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "BLOCKED" in report, (
        "Executive snapshot must show BLOCKED (not ACTIVE) when SLEEP_MODE blocks all signals"
    )
    assert "SLEEP_MODE" in report


def test_report_root_cause_names_sleep_mode():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "SLEEP_MODE" in report
    assert "No critical root cause identified" not in report


def test_report_capital_missed_opportunity_is_not_none():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "None — system actively trading or recently traded" not in report, (
        "Missed Opportunity must not say 'None' when signals are blocked by SLEEP_MODE"
    )


def test_report_historical_stats_labeled_when_mixed():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "HISTORICAL" in report or "historical" in report.lower(), (
        "Report must label stats as historical when session_trades=0 but stats are populated"
    )


def test_truth_process_does_not_mutate_original():
    data = _sleep_mode_data()
    original_keys = set(data.keys())
    _ = truth_process(data)
    assert "_truth" not in data, "truth_process must not mutate the original data dict"
    assert set(data.keys()) == original_keys


def test_validate_signal_flow_execution_gap():
    data = _sleep_mode_data()
    sf = validate_signal_flow(data)
    assert sf["execution_gap"] == 13
    assert sf["dominant_block"] == "SLEEP_MODE"
    assert sf["dominant_count"] == 6


# ── FTD-025CD: Intelligence Layer unit tests ──────────────────────────────────

from core.reporting.intelligence_layer import (
    analyze_execution,
    explain_decision,
    capital_analysis,
    learning_analysis,
    enhanced_alerts,
    enrich,
)


def test_intelligence_layer_enrich_adds_intel_key():
    data = truth_process(_minimal_data())
    enriched = enrich(data)
    assert "_intel" in enriched, "_intel key must exist after enrich()"
    assert "execution" in enriched["_intel"]
    assert "decision"  in enriched["_intel"]
    assert "capital"   in enriched["_intel"]
    assert "learning"  in enriched["_intel"]
    assert "alerts"    in enriched["_intel"]


def test_analyze_execution_gap_correct_for_sleep_mode():
    data = truth_process(_sleep_mode_data())
    result = analyze_execution(data)
    assert result["has_gap"] is True
    assert result["execution_gap"] == "13 → 0"
    assert result["dominant_block"] == "SLEEP_MODE"


def test_analyze_execution_no_gap_when_trades_exist():
    data = truth_process(_minimal_data())
    result = analyze_execution(data)
    assert result["has_gap"] is False
    assert result["execution_gap"] == "None"


def test_explain_decision_returns_why_no_trade():
    data = truth_process(_sleep_mode_data())
    result = explain_decision(data)
    assert result["why_no_trade"] is not None
    assert len(result["why_no_trade"]) > 10
    assert result["missing_condition"] is not None
    assert result["next_trigger"] is not None


def test_capital_analysis_missed_opportunity_when_blocked():
    data = truth_process(_sleep_mode_data())
    result = capital_analysis(data)
    assert result["missed_opportunity"] is True
    assert result["capital_idle"] > 0
    assert "%" in result["capital_idle_pct_str"]


def test_capital_analysis_no_missed_when_no_signals():
    data = _minimal_data()
    data["trade_flow"]["total_signals"] = 0
    data["trade_flow"]["total_trades"]  = 0
    data = truth_process(data)
    result = capital_analysis(data)
    assert result["missed_opportunity"] is False


def test_learning_analysis_returns_valid_structure():
    data = _minimal_data()
    result = learning_analysis(data)
    assert "top_patterns"     in result
    assert "failure_patterns" in result
    assert "confidence"       in result
    assert isinstance(result["confidence"], float)


def test_enhanced_alerts_has_no_execution_alert_when_signals_blocked():
    data = truth_process(_sleep_mode_data())
    alerts = enhanced_alerts(data)
    types = {a["type"] for a in alerts}
    assert "NO_TRADE_ALERT" in types or "NO_EXECUTION_ALERT" in types, (
        "NO_EXECUTION or NO_TRADE alert must be present when signals>0 and trades=0"
    )


def test_enhanced_alerts_has_signal_block_alert():
    data = truth_process(_sleep_mode_data())
    alerts = enhanced_alerts(data)
    types = {a["type"] for a in alerts}
    assert "SIGNAL_REJECTION_SPIKE" in types or "SIGNAL_BLOCK_ALERT" in types, (
        "SIGNAL_BLOCK alert must be present when rejection reasons exist and trades=0"
    )


def test_enhanced_alerts_has_contradiction_alert():
    data = truth_process(_sleep_mode_data())
    alerts = enhanced_alerts(data)
    types = {a["type"] for a in alerts}
    assert "CONTRADICTION_DETECTED" in types or "CONTRADICTION_ALERT" in types, (
        "CONTRADICTION alert must be present when contradictions are detected"
    )


def test_enrich_sets_execution_gap_top_level_when_blocked():
    data = truth_process(_sleep_mode_data())
    enriched = enrich(data)
    assert enriched.get("execution_gap") == "13 → 0", (
        "top-level execution_gap must be '13 → 0' when signals=13 and trades=0"
    )
    assert enriched.get("primary_issue") == "NO EXECUTION — signals blocked"


def test_enrich_does_not_inject_execution_gap_when_trades_normal():
    data = truth_process(_minimal_data())
    enriched = enrich(data)
    assert "execution_gap" not in enriched or enriched.get("execution_gap") is None, (
        "execution_gap must not be injected when trades are executing normally"
    )


def test_enrich_does_not_mutate_input():
    data = truth_process(_sleep_mode_data())
    original_keys = set(data.keys())
    _ = enrich(data)
    assert "_intel" not in data, "enrich() must not mutate the input dict"
    assert set(data.keys()) == original_keys


def test_report_shows_pass_rate_and_reject_rate():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "Pass Rate" in report,   "Signal Flow section must show Pass Rate"
    assert "Reject Rate" in report, "Signal Flow section must show Reject Rate"


def test_report_shows_what_needed_in_decision_section():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "WHAT NEEDED" in report, "Decision Intelligence section must contain WHAT NEEDED block"


def test_report_shows_developer_summary():
    data = _sleep_mode_data()
    report = generate_full_report_v2(data)
    assert "Developer Summary" in report, "Developer Export section must contain Developer Summary"
    assert "- Issue:" in report
    assert "- Fix:" in report


def test_report_capital_idle_100_pct_when_signals_blocked():
    data = _sleep_mode_data()
    result = capital_analysis(truth_process(data))
    assert result["capital_idle"] > 90.0, (
        "Capital idle should be near 100% when no trades executed"
    )

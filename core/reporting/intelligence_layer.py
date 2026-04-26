"""
EOW Quant Engine — FTD-025CD-TRUTH+INTEL-V1
Intelligence Depth Layer: Execution + Decision + Capital + Learning analysis.

Pipeline position: truth_engine.process() → intelligence_layer.enrich() → generate_report

Each module answers a different question:
  analyze_execution  → WHAT happened in signal→trade pipeline
  explain_decision   → WHY no trade, WHAT is missing
  capital_analysis   → WHERE did capital go / where was it idle
  learning_analysis  → WHAT patterns exist, confidence level
  enhanced_alerts    → WHAT alerts are guaranteed present
"""
from __future__ import annotations

from typing import Any


def _g(d: dict, *keys, default: Any = None) -> Any:
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d if d is not None else default


# ── Modules ───────────────────────────────────────────────────────────────────

def analyze_execution(data: dict) -> dict:
    """Execution gap, dominant block, pass/reject rates from truth engine signal_flow."""
    truth = data.get("_truth", {})
    sf    = truth.get("signal_flow", {})
    tf    = data.get("trade_flow", {})

    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)

    exec_gap_n  = sf.get("execution_gap", max(signals - trades, 0))
    dom_blk     = sf.get("dominant_block")
    dom_cnt     = sf.get("dominant_count", 0)
    pass_rate   = sf.get("pct_signals_passed",   0.0)
    reject_rate = sf.get("pct_signals_rejected", 0.0)

    # has_gap is True only when execution is COMPLETELY blocked (trades=0 with signals present)
    complete_block = signals > 0 and trades == 0
    execution_gap_str = f"{signals} → {trades}" if complete_block else "None"

    return {
        "execution_gap":    execution_gap_str,
        "execution_gap_n":  exec_gap_n,
        "dominant_block":   dom_blk or "NONE",
        "dominant_count":   dom_cnt,
        "pass_rate":        round(pass_rate,   1),
        "reject_rate":      round(reject_rate, 1),
        "has_gap":          complete_block,
    }


def explain_decision(data: dict) -> dict:
    """WHY no trade, WHAT condition is missing, WHAT would trigger next execution."""
    truth  = data.get("_truth", {})
    de     = truth.get("decision_enhance", {})
    rc     = truth.get("root_cause", {})
    thresh = data.get("thresholds", {})

    why_no_trade      = (
        de.get("why_no_execution")
        or rc.get("primary", "System operating normally")
    )
    missing_condition = (
        de.get("what_condition_missing")
        or "None — all conditions met"
    )
    next_trigger = (
        de.get("what_triggers_execution")
        or f"Signal passes all gates AND score ≥ {thresh.get('score_min', 0.58):.3f}"
    )

    # FTD-034: AI decision must reflect execution reality
    tf      = data.get("trade_flow", {})
    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)

    if signals > 0 and trades == 0:
        decision        = "BLOCKED"
        decision_reason = "NO_EXECUTION — signals not passing gates"
    else:
        decision        = "MONITOR"
        decision_reason = ""

    return {
        "why_no_trade":      why_no_trade,
        "missing_condition": missing_condition,
        "next_trigger":      next_trigger,
        "decision":          decision,
        "decision_reason":   decision_reason,
    }


def capital_analysis(data: dict) -> dict:
    """Capital used vs idle; definitive missed-opportunity diagnosis."""
    truth     = data.get("_truth", {})
    cap_check = truth.get("capital_check", {})
    ss        = data.get("session_stats", {})

    initial = _g(ss, "initial_capital", default=1000.0)
    pnl     = _g(ss, "total_net_pnl",   default=0.0)
    fees    = _g(ss, "total_fees_paid", default=0.0)

    deployed = abs(pnl + fees) / max(initial, 1) * 100
    idle     = 100.0 - min(deployed, 100.0)

    missed_opp = cap_check.get("missed_opportunity", False)
    reason     = cap_check.get("missed_reason", "None — system actively trading")

    return {
        "capital_used":         round(deployed, 2),
        "capital_idle":         round(idle,     2),
        "capital_idle_pct_str": f"{idle:.1f}%",
        "missed_opportunity":   missed_opp,
        "reason":               reason,
    }


def learning_analysis(data: dict) -> dict:
    """Pattern formation rate, failure patterns, rough confidence metric."""
    mem = data.get("learning_memory", {})

    total_patterns  = mem.get("total_patterns",            0)
    formed_patterns = mem.get("formed_patterns",           0)
    neg_perm        = mem.get("negative_memory_permanent", 0)
    neg_temp        = mem.get("negative_memory_temporary", 0)

    failure_patterns = neg_perm + neg_temp
    confidence = (
        round(formed_patterns / total_patterns * 100, 1)
        if total_patterns > 0
        else 0.0
    )

    return {
        "top_patterns":     formed_patterns,
        "failure_patterns": failure_patterns,
        "confidence":       confidence,
        "has_bans":         neg_perm > 0,
    }


def enhanced_alerts(data: dict) -> list[dict]:
    """
    Build guaranteed alert list.

    Ensures the following alerts are ALWAYS present when conditions warrant:
      NO_EXECUTION_ALERT  — signals > 0 and trades = 0
      SIGNAL_BLOCK_ALERT  — rejection reasons present with no trades
      CONTRADICTION_ALERT — contradictions detected by truth engine
    """
    truth       = data.get("_truth", {})
    base_alerts = list(truth.get("alerts", []))
    existing    = {a.get("type") for a in base_alerts}

    tf      = data.get("trade_flow", {})
    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)
    reasons = tf.get("top_rejection_reasons", {})

    # NO_EXECUTION_ALERT
    if signals > 0 and trades == 0 and "NO_TRADE_ALERT" not in existing:
        top_block = (
            max(reasons.items(), key=lambda x: x[1])[0]
            if reasons else "GATING"
        )
        base_alerts.insert(0, {
            "type":   "NO_EXECUTION_ALERT",
            "title":  f"NO EXECUTION — {signals} signal(s) blocked",
            "cause":  f"Dominant block: {top_block}",
            "impact": "Zero trades executed despite active signal flow",
            "fix":    f"Review {top_block} threshold; check tier/score configuration",
        })
        existing.add("NO_EXECUTION_ALERT")

    # SIGNAL_BLOCK_ALERT
    if reasons and trades == 0 and "SIGNAL_REJECTION_SPIKE" not in existing:
        top_reason, top_cnt = max(reasons.items(), key=lambda x: x[1])
        base_alerts.append({
            "type":   "SIGNAL_BLOCK_ALERT",
            "title":  f"SIGNAL BLOCK — {top_reason} ({top_cnt} rejection(s))",
            "cause":  f"{top_reason} gating all signals in current window",
            "impact": f"{top_cnt} trade opportunity(s) missed",
            "fix":    f"Investigate {top_reason} condition and threshold settings",
        })
        existing.add("SIGNAL_BLOCK_ALERT")

    # CONTRADICTION_ALERT
    contradictions = truth.get("contradictions", [])
    if contradictions and "CONTRADICTION_DETECTED" not in existing:
        ids = ", ".join(c["id"] for c in contradictions)
        base_alerts.append({
            "type":   "CONTRADICTION_ALERT",
            "title":  f"CONTRADICTION DETECTED ({len(contradictions)} found)",
            "cause":  f"Logical inconsistencies: {ids}",
            "impact": "Report accuracy degraded without truth correction",
            "fix":    "Truth engine corrected data — report reflects resolved state",
        })

    return base_alerts


# ── Public API ────────────────────────────────────────────────────────────────

def enrich(data: dict) -> dict:
    """
    Intelligence Layer main entry point.

    Adds '_intel' key to the (non-mutated) data dict with deep analysis.
    Also injects top-level 'execution_gap' and 'primary_issue' when signals
    are present but no trades executed, as required by FTD-025CD Part 2.

    Must be called AFTER truth_engine.process().
    Pipeline: raw → truth_engine.process() → intelligence_layer.enrich() → generate_report
    """
    exec_intel  = analyze_execution(data)
    dec_intel   = explain_decision(data)
    cap_intel   = capital_analysis(data)
    learn_intel = learning_analysis(data)
    alerts      = enhanced_alerts(data)

    tf      = data.get("trade_flow", {})
    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)

    result = dict(data)

    # FTD-025CD Part 2 — contradiction enforcement: inject top-level fields
    if signals > 0 and trades == 0:
        result["execution_gap"] = f"{signals} → 0"
        result["primary_issue"] = "NO EXECUTION — signals blocked"

    result["_intel"] = {
        "execution": exec_intel,
        "decision":  dec_intel,
        "capital":   cap_intel,
        "learning":  learn_intel,
        "alerts":    alerts,
    }
    return result

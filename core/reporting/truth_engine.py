"""
EOW Quant Engine — FTD-025C-TRUTH-LAYER-V1
Truth Engine: Contradiction Detection + Root Cause Resolution

Ensures reports are truthful, not cosmetic.
Pipeline: collect_data → truth_engine.process() → corrected_data → generate_report

Truth > Formatting. Clarity > Completeness. Actionability > Data volume.
"""
from __future__ import annotations

from typing import Any


def _g(d: dict, *keys, default: Any = None) -> Any:
    """Safe nested get."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d if d is not None else default


# ── Core components ───────────────────────────────────────────────────────────

def detect_contradictions(data: dict) -> list[dict]:
    """
    Scan report data for logical contradictions.

    DETECTS:
      signals > 0 AND trades = 0
      capital_idle > 70% AND trades = 0
      rejection reasons exist BUT root cause masked
      PF < 1 BUT n_trades = 0 (stats look historical)
      session_trades = 0 BUT win_rate populated (session/historical mix)
    """
    contradictions: list[dict] = []

    tf = data.get("trade_flow", {})
    ss = data.get("session_stats", {})

    signals  = tf.get("total_signals", 0)
    trades   = tf.get("total_trades",  0)
    reasons  = tf.get("top_rejection_reasons", {})
    n_trades = ss.get("n_trades",      0)
    pf       = ss.get("profit_factor", 0.0)
    win_rate = ss.get("win_rate",      0.0)
    avg_win  = ss.get("avg_win_usdt",  0.0)

    if signals > 0 and trades == 0:
        contradictions.append({
            "id":       "SIGNALS_NO_TRADES",
            "desc":     f"Signals generated ({signals}) but zero trades executed in window",
            "severity": "HIGH",
        })

    if reasons and trades == 0:
        top_reason = max(reasons.items(), key=lambda x: x[1])[0]
        contradictions.append({
            "id":         "GATING_BLOCK_INVISIBLE",
            "desc":       f"Signals blocked by {top_reason} — not surfaced as root cause",
            "severity":   "HIGH",
            "top_reason": top_reason,
        })

    if 0 < pf < 1.0:
        contradictions.append({
            "id":       "LOW_PF_MASKED",
            "desc":     f"Profit factor {pf:.2f} < 1.0 — system in loss but may not be flagged",
            "severity": "MEDIUM",
        })

    if n_trades == 0 and (win_rate > 0 or avg_win != 0):
        contradictions.append({
            "id":       "SESSION_HISTORICAL_MIX",
            "desc":     "Session trades=0 but win_rate/avg_win populated — historical stats in session display",
            "severity": "MEDIUM",
        })

    return contradictions


def validate_signal_flow(data: dict) -> dict:
    """
    Compute accurate signal flow: execution gap, dominant block, pass/reject rates.
    """
    tf = data.get("trade_flow", {})

    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)
    skips   = tf.get("total_skips",   0)
    reasons = tf.get("top_rejection_reasons", {})

    pct_rejected = (skips  / signals * 100) if signals > 0 else 0.0
    pct_passed   = (trades / signals * 100) if signals > 0 else 0.0
    execution_gap = signals - trades

    dominant_block = None
    dominant_count = 0
    if reasons:
        dominant_block, dominant_count = max(reasons.items(), key=lambda x: x[1])

    return {
        "pct_signals_rejected": pct_rejected,
        "pct_signals_passed":   pct_passed,
        "execution_gap":        execution_gap,
        "dominant_block":       dominant_block,
        "dominant_count":       dominant_count,
    }


def split_metrics(data: dict) -> dict:
    """
    Separate session metrics (current window) from historical lifetime metrics.
    MUST NEVER MIX.
    """
    tf = data.get("trade_flow",    {})
    ss = data.get("session_stats", {})

    session_trades = tf.get("total_trades", 0)
    hist_n         = ss.get("n_trades",     0)
    win_rate       = ss.get("win_rate",     0.0)
    avg_win        = ss.get("avg_win_usdt", 0.0)

    # Mixed when session has 0 trades but historical stats are populated
    is_mixed = session_trades == 0 and (win_rate > 0 or avg_win != 0)

    session = {
        "n_trades": session_trades,
        "is_active": session_trades > 0,
    }

    historical = {
        "n_trades":      hist_n,
        "win_rate":      win_rate,
        "avg_win":       avg_win,
        "avg_loss":      ss.get("avg_loss_usdt",  0.0),
        "total_pnl":     ss.get("total_net_pnl",  0.0),
        "total_fees":    ss.get("total_fees_paid", 0.0),
        "profit_factor": ss.get("profit_factor",  0.0),
    }

    return {
        "session":    session,
        "historical": historical,
        "is_mixed":   is_mixed,
    }


def analyze_capital_efficiency(data: dict) -> dict:
    """
    Compute true capital efficiency.
    IF trades=0 AND signals>0 → missed_opportunity=True, reason=gating/filtering.
    """
    tf  = data.get("trade_flow",    {})
    ss  = data.get("session_stats", {})

    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)
    reasons = tf.get("top_rejection_reasons", {})
    initial = ss.get("initial_capital", 1000.0)
    pnl     = ss.get("total_net_pnl",   0.0)
    fees    = ss.get("total_fees_paid", 0.0)

    deployed_pct = abs(pnl + fees) / max(initial, 1) * 100
    idle_pct     = 100.0 - min(deployed_pct, 100.0)

    missed_opportunity = False
    missed_reason = "None"

    if trades == 0 and signals > 0:
        missed_opportunity = True
        top_block = (
            max(reasons.items(), key=lambda x: x[1])[0]
            if reasons else "unknown gating"
        )
        missed_reason = (
            f"Signals available ({signals}) but execution blocked by {top_block}"
        )

    return {
        "deployed_pct":       deployed_pct,
        "idle_pct":           idle_pct,
        "missed_opportunity": missed_opportunity,
        "missed_reason":      missed_reason,
    }


def resolve_root_cause(data: dict, contradictions: list[dict]) -> dict:
    """
    Determine root cause with strict priority chain.
    NEVER returns empty root cause if contradictions exist.

    Priority:
      1. GATING BLOCK (SLEEP_MODE / LOW_SCORE / RR_FAIL)
      2. SIGNAL QUALITY failure
      3. RISK BLOCK (halt)
      4. NEGATIVE EXPECTANCY (≥10 trades)
      5. SIGNAL SCARCITY (idle >60 min)
      6. CONTRADICTION OVERRIDE
      7. TRUE NO-OPPORTUNITY
    """
    tf     = data.get("trade_flow",    {})
    ss     = data.get("session_stats", {})
    risk   = data.get("risk",          {})
    thresh = data.get("thresholds",    {})

    signals  = tf.get("total_signals", 0)
    trades   = tf.get("total_trades",  0)
    reasons  = tf.get("top_rejection_reasons", {})
    pf       = ss.get("profit_factor", 0.0)
    n_trades = ss.get("n_trades",      0)
    avg_win  = ss.get("avg_win_usdt",  0.0)
    avg_loss = ss.get("avg_loss_usdt", 0.0)
    halted   = _g(risk, "halted",      default=False)
    mins     = data.get("mins_idle",   0.0)

    primary   = None
    secondary: list[str] = []

    # Priority 1: Gating block — signals exist but all rejected
    if signals > 0 and trades == 0 and reasons:
        top_reason, top_count = max(reasons.items(), key=lambda x: x[1])
        total_r = sum(reasons.values()) or 1
        pct = top_count / total_r * 100
        primary = (
            f"**Trade execution blocked by {top_reason}** despite {signals} active signal(s) "
            f"({top_count}/{total_r} rejections = {pct:.0f}%). "
            f"Signal pipeline is functional — gating layer is the blocker."
        )
        for rsn, cnt in sorted(reasons.items(), key=lambda x: -x[1]):
            if rsn != top_reason and cnt > 0:
                secondary.append(f"{rsn}: {cnt} additional signal(s) blocked")

    # Priority 2: Signal quality failure (signals but no reasons recorded)
    elif signals > 0 and trades == 0:
        primary = (
            f"**Signal quality failure** — {signals} signal(s) generated but none passed "
            f"the full quality chain (score_min={thresh.get('score_min', '?')}). "
            f"Market conditions may not align with strategy criteria."
        )

    # Priority 3: Risk kill-switch
    elif halted:
        halt_rsn = _g(risk, "halt_reason", default="unknown")
        primary = (
            f"**Risk kill-switch active** — system halted, zero execution possible. "
            f"Halt reason: {halt_rsn}."
        )

    # Priority 4: Negative expectancy (statistically significant sample)
    elif 0 < pf < 1.0 and n_trades >= 10:
        ratio = abs(avg_loss / avg_win) if avg_win else 0
        primary = (
            f"**Negative expectancy (PF={pf:.2f})** — avg loss {ratio:.1f}× avg win. "
            f"Signal pipeline functioning; structural problem is insufficient reward-to-risk."
        )
        secondary.append(
            f"Avg loss ({avg_loss:.2f}) > avg win ({avg_win:.2f}) across {n_trades} trades"
        )

    # Priority 5: Signal scarcity / idle
    elif mins > 60:
        primary = (
            f"**Signal scarcity ({mins:.0f} min idle)** — Trade Activator "
            f"tier={thresh.get('tier', '?')} score_min={thresh.get('score_min', '?'):.3f}, "
            f"no signal clearing the full quality chain. "
            f"Market conditions do not match any strategy's entry criteria."
        )

    # Priority 6: Contradictions present but no higher-priority cause matched
    elif contradictions:
        ids = ", ".join(c["id"] for c in contradictions)
        primary = (
            f"**Unresolved contradictions detected**: {ids}. "
            f"System state requires investigation."
        )

    # Priority 7: Genuine no-issue
    else:
        primary = (
            "**No critical root cause identified** — system operating within normal parameters."
        )

    has_issue = "No critical root cause identified" not in (primary or "")

    return {
        "primary":   primary,
        "secondary": secondary,
        "has_issue": has_issue,
    }


def generate_alerts(data: dict, contradictions: list[dict]) -> list[dict]:
    """
    Generate actionable alerts including contradiction-based alerts.

    Alert types: NO_TRADE_ALERT, SLEEP_MODE_BLOCK, SIGNAL_REJECTION_SPIKE,
                 CAPITAL_IDLE_HIGH, CONTRADICTION_DETECTED, HALT_ACTIVE,
                 LOW_PROFIT_FACTOR, HIGH_FEE_DRAG, RECURRING_ERROR.
    """
    ss     = data.get("session_stats", {})
    tf     = data.get("trade_flow",    {})
    risk   = data.get("risk",          {})
    errors = data.get("errors",        [])
    mins   = data.get("mins_idle",     0.0)

    pf       = _g(ss, "profit_factor",  default=0.0)
    avg_win  = _g(ss, "avg_win_usdt",   default=0.0)
    avg_loss = _g(ss, "avg_loss_usdt",  default=0.0)
    fees     = _g(ss, "total_fees_paid",default=0.0)
    pnl      = _g(ss, "total_net_pnl",  default=0.0)
    n_trades = _g(ss, "n_trades",       default=0)
    halted   = _g(risk, "halted",       default=False)
    signals  = tf.get("total_signals",  0)
    trades   = tf.get("total_trades",   0)
    reasons  = tf.get("top_rejection_reasons", {})
    gross    = abs(pnl) + fees

    alerts: list[dict] = []

    if halted:
        alerts.append({
            "type":   "HALT_ACTIVE",
            "title":  "HALT ACTIVE",
            "cause":  "Risk kill-switch triggered",
            "impact": "Zero new trades until manually cleared",
            "fix":    "Resolve halt condition; call /api/risk/resume",
        })

    if signals > 0 and trades == 0:
        top_block = (
            max(reasons.items(), key=lambda x: x[1])[0]
            if reasons else "GATING"
        )
        alerts.append({
            "type":   "NO_TRADE_ALERT",
            "title":  f"NO TRADES EXECUTED ({signals} signal(s) blocked)",
            "cause":  f"All signals rejected — dominant block: {top_block}",
            "impact": "Zero execution despite active signal flow",
            "fix":    f"Investigate {top_block} condition; check threshold configuration",
        })

    if reasons:
        top_reason, top_count = max(reasons.items(), key=lambda x: x[1])
        alerts.append({
            "type":   "SIGNAL_REJECTION_SPIKE",
            "title":  f"{top_reason} BLOCK ({top_count} rejection(s))",
            "cause":  f"{top_reason} gating all signals in current window",
            "impact": f"{top_count} trade opportunity(s) missed",
            "fix":    f"Review {top_reason} conditions and threshold settings",
        })

    if 0 < pf < 1.0 and n_trades >= 10:
        ratio = abs(avg_loss / avg_win) if avg_win else 0
        alerts.append({
            "type":   "LOW_PROFIT_FACTOR",
            "title":  f"LOW PROFIT FACTOR ({pf:.2f})",
            "cause":  f"Avg loss ({avg_loss:.2f}) is {ratio:.1f}× avg win ({avg_win:.2f})",
            "impact": f"Expected loss per cycle on current RR structure",
            "fix":    "Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0",
        })

    if fees > 0 and gross > 0:
        fee_pct = fees / gross * 100
        if fee_pct > 20:
            alerts.append({
                "type":   "HIGH_FEE_DRAG",
                "title":  f"HIGH FEE DRAG ({fee_pct:.0f}% of gross)",
                "cause":  "Small-notional trades × maker/taker fee 0.1%",
                "impact": f"Fees consuming ${fees:.2f} of gross turnover",
                "fix":    "Increase MIN_NOTIONAL_USDT; reduce trade frequency",
            })

    if mins > 60:
        alerts.append({
            "type":   "CAPITAL_IDLE_HIGH",
            "title":  f"TRADE DRY-SPELL ({mins:.0f} min)",
            "cause":  "No signal clearing all quality gates",
            "impact": "Capital idle; Trade Activator relaxing filters",
            "fix":    "Check Alpha Engine signal quality; inspect top rejection reasons",
        })

    for c in contradictions:
        if c["id"] == "SESSION_HISTORICAL_MIX":
            alerts.append({
                "type":   "CONTRADICTION_DETECTED",
                "title":  "SESSION/HISTORICAL METRICS MIXED",
                "cause":  "Session trades=0 but historical stats displayed without label",
                "impact": "Performance section shows lifetime stats, not current session",
                "fix":    "Performance stats below are HISTORICAL (lifetime), not current session",
            })

    err_counts: dict[str, int] = {}
    for e in errors:
        code = e.get("code", "UNKNOWN")
        err_counts[code] = err_counts.get(code, 0) + 1
    for code, count in sorted(err_counts.items(), key=lambda x: -x[1]):
        if count >= 3:
            alerts.append({
                "type":   "RECURRING_ERROR",
                "title":  f"RECURRING ERROR: {code} ({count} times)",
                "cause":  "Repeated indicator quality failure",
                "impact": "Affected symbols blocked from evaluation",
                "fix":    "Check ATR/ADX thresholds for affected symbol",
            })
            break

    return alerts


def enhance_decision_reasoning(data: dict, root_cause: dict) -> dict:
    """
    Add WHY signals rejected, WHY no execution, WHAT condition missing,
    WHAT would trigger execution.
    """
    tf     = data.get("trade_flow",    {})
    thresh = data.get("thresholds",    {})
    ss     = data.get("session_stats", {})

    signals  = tf.get("total_signals", 0)
    trades   = tf.get("total_trades",  0)
    reasons  = tf.get("top_rejection_reasons", {})
    score_mn = thresh.get("score_min", 0.58)
    pf       = ss.get("profit_factor", 0.0)
    n_tr     = ss.get("n_trades",      0)

    why_rejected    = None
    why_no_exec     = None
    what_missing    = None
    what_triggers   = None

    if signals > 0 and trades == 0 and reasons:
        top_reason, _ = max(reasons.items(), key=lambda x: x[1])
        why_rejected  = f"Signals rejected due to {top_reason} gating condition"
        why_no_exec   = f"Execution blocked by {top_reason} — signals exist but cannot proceed to order"
        what_missing  = f"{top_reason} condition must be cleared for trade execution"
        what_triggers = (
            f"Signal passes {top_reason} check AND score ≥ {score_mn:.3f} AND risk gate CLEAR"
        )

    elif signals == 0:
        why_rejected  = "No signals generated — no market setups detected in current window"
        why_no_exec   = "No signals to execute — Alpha Engine found no qualifying patterns"
        what_missing  = "Strategy entry criteria must be met for signal generation"
        what_triggers = (
            f"Strategy pattern match AND score ≥ {score_mn:.3f} AND market regime compatible"
        )

    if pf > 0 and pf < 1.0 and n_tr >= 10 and what_triggers:
        what_triggers += (
            f" | NOTE: PF={pf:.2f} < 1.0 — review RR structure before aggressive execution"
        )

    return {
        "why_signals_rejected":    why_rejected,
        "why_no_execution":        why_no_exec,
        "what_condition_missing":  what_missing,
        "what_triggers_execution": what_triggers,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def process(data: dict) -> dict:
    """
    Main Truth Engine entry point.

    Runs all truth checks, resolves contradictions, returns augmented data dict
    with '_truth' key. Original dict is not mutated.

    Pipeline: collect_data → truth_engine.process() → corrected_data → generate_report
    """
    contradictions   = detect_contradictions(data)
    signal_flow      = validate_signal_flow(data)
    split            = split_metrics(data)
    capital_check    = analyze_capital_efficiency(data)
    root_cause       = resolve_root_cause(data, contradictions)
    alerts           = generate_alerts(data, contradictions)
    decision_enhance = enhance_decision_reasoning(data, root_cause)

    result = dict(data)
    result["_truth"] = {
        "contradictions":      contradictions,
        "signal_flow":         signal_flow,
        "split_metrics":       split,
        "capital_check":       capital_check,
        "root_cause":          root_cause,
        "alerts":              alerts,
        "decision_enhance":    decision_enhance,
        "has_contradictions":  len(contradictions) > 0,
        "contradiction_count": len(contradictions),
    }
    return result

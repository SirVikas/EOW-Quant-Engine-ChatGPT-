"""
EOW Quant Engine — FTD-025B-URX-V2 + FTD-025C-TRUTH-LAYER-V1 + FTD-025CD-INTEL-V1
Unified Report Engine v2 with integrated Truth Engine and Intelligence Layer.

Produces a cause-effect narrative report:
  SYSTEM → THINKING → DECISION → RESULT → ROOT CAUSE → ACTION

Every section answers WHY. No contradictions. No empty root cause.
Pipeline: collect_data → truth_engine.process() → intelligence_layer.enrich() → generate_report
"""
from __future__ import annotations

import time
from typing import Any

from core.reporting.truth_engine import process as _truth_process
from core.reporting.intelligence_layer import enrich as _intel_enrich


# ── Helpers ───────────────────────────────────────────────────────────────────

def _g(d: dict, *keys, default: Any = None) -> Any:
    """Safe nested get."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d if d is not None else default


def _pct(v: float, decimals: int = 1) -> str:
    return f"{v:.{decimals}f}%"


def _money(v: float, signed: bool = False) -> str:
    prefix = "+" if (signed and v > 0) else ""
    return f"{prefix}${v:.2f}"


def _row(label: str, value: str) -> str:
    return f"| {label} | {value} |"


def _table(rows: list[tuple[str, str]]) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    lines += [_row(k, str(v)) for k, v in rows]
    return "\n".join(lines)


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body}"


def _bullet(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items)


# ── Section builders ──────────────────────────────────────────────────────────

def _s1_executive_snapshot(d: dict) -> str:
    ss      = d.get("session_stats", {})
    tf      = d.get("trade_flow", {})
    gate    = d.get("gate", {})
    mins    = d.get("mins_idle", 0.0)
    thresh  = d.get("thresholds", {})
    pf      = _g(ss, "profit_factor", default=0.0)
    pnl     = _g(ss, "total_net_pnl", default=0.0)
    n_tr    = _g(ss, "n_trades", default=0)
    can_trade = _g(gate, "can_trade", default=True)
    halted  = _g(d, "risk", "halted", default=False)

    # System state
    if halted:
        sys_state = "HALTED"
    elif not can_trade:
        sys_state = "BLOCKED"
    else:
        sys_state = "ACTIVE"

    # Trading activity — use truth engine to detect gating blocks
    truth       = d.get("_truth", {})
    cap_check   = truth.get("capital_check", {})
    sig_flow    = truth.get("signal_flow", {})
    dominant    = sig_flow.get("dominant_block")

    if cap_check.get("missed_opportunity") and mins < 5:
        trade_activity = f"BLOCKED ({dominant} — signals present, no execution)"
    elif mins < 5:
        trade_activity = "ACTIVE"
    elif mins < 30:
        trade_activity = f"RECENT ({mins:.0f} min ago)"
    else:
        trade_activity = f"IDLE ({mins:.0f} min — activator tier={thresh.get('tier','?')})"

    # Profitability
    if pf >= 1.5:
        profit_state = f"PROFITABLE (PF={pf:.2f})"
    elif pf >= 1.0:
        profit_state = f"MARGINAL (PF={pf:.2f})"
    else:
        profit_state = f"LOSS (PF={pf:.2f}, net={_money(pnl)})"

    # Key problem — truth engine supersedes generic fallback
    avg_win  = _g(ss, "avg_win_usdt",  default=0.0)
    avg_loss = _g(ss, "avg_loss_usdt", default=0.0)
    fees     = _g(ss, "total_fees_paid", default=0.0)
    ratio    = abs(avg_loss / avg_win) if avg_win else 0.0

    contradictions = truth.get("contradictions", [])
    has_gating_block = any(c["id"] == "GATING_BLOCK_INVISIBLE" for c in contradictions)

    if has_gating_block:
        key_problem = f"All signals blocked by {dominant} — no execution despite active signal flow"
        action = f"Investigate {dominant} condition; check threshold and tier configuration"
    elif pf < 1.0 and n_tr >= 10:
        key_problem = (
            f"Avg loss ({_money(avg_loss)}) is {ratio:.1f}× avg win ({_money(avg_win)}); "
            f"fees {_money(fees)} consume {_pct(fees / max(abs(pnl) + fees, 1e-9) * 100)} of gross"
        )
        action = "Increase RR target to ≥2.0; reduce fee drag by raising min notional"
    elif mins > 60:
        key_problem = f"System idle {mins:.0f} min — no signal passing quality threshold"
        action = f"Check Alpha Engine output; tier={thresh.get('tier','?')} score_min={thresh.get('score_min','?')}"
    else:
        key_problem = "System operating normally"
        action = "Monitor — no immediate action required"

    body = _table([
        ("System State",    sys_state),
        ("Trading Activity", trade_activity),
        ("Profitability",   profit_state),
        ("Key Problem",     key_problem),
        ("Immediate Action", action),
    ])
    return _section("1. Executive Snapshot", body)


def _s2_signal_flow(d: dict) -> str:
    tf      = d.get("trade_flow", {})
    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)
    skips   = tf.get("total_skips",   0)
    passed  = trades  # signals that became trades
    rejected = skips
    rej_rate = tf.get("rejection_rate_pct", 0.0)
    reasons  = tf.get("top_rejection_reasons", {})

    truth    = d.get("_truth", {})
    sf       = truth.get("signal_flow", {})
    exec_gap = sf.get("execution_gap", 0)
    dom_blk  = sf.get("dominant_block")
    dom_cnt  = sf.get("dominant_count", 0)

    intel    = d.get("_intel", {})
    exec_i   = intel.get("execution", {})
    pass_r   = exec_i.get("pass_rate",   sf.get("pct_signals_passed",   0.0))
    reject_r = exec_i.get("reject_rate", sf.get("pct_signals_rejected", 0.0))

    flow_rows = [
        ("Signals Generated (window)",  signals),
        ("Signals Passed → Traded",     trades),
        ("Signals Rejected",            skips),
        ("Pass Rate",                   _pct(pass_r)),
        ("Reject Rate",                 _pct(reject_r)),
        ("Rejection Rate (window %)",   _pct(rej_rate)),
        ("Mins Since Last Trade",       f"{tf.get('minutes_since_last_trade', 0):.1f}"),
        ("Signals / hour",              f"{tf.get('signals_per_hour', 0):.1f}"),
        ("Trades / hour",               f"{tf.get('trades_per_hour', 0):.2f}"),
    ]
    if exec_gap > 0:
        flow_rows.append(("Execution Gap", f"{exec_gap} signal(s) → 0 trades"))
    if dom_blk:
        flow_rows.append(("Dominant Block", f"{dom_blk} ({dom_cnt} rejection(s))"))

    flow_table = _table(flow_rows)

    if reasons:
        total_reasons = sum(reasons.values()) or 1
        reason_lines = [
            f"- {k}: {v} ({v/total_reasons*100:.0f}%)"
            for k, v in sorted(reasons.items(), key=lambda x: -x[1])
        ]
        reason_block = "**Top Rejection Reasons:**\n" + "\n".join(reason_lines)
    else:
        reason_block = "_No rejection reasons recorded in current window._"

    return _section("2. Signal → Trade Flow", f"{flow_table}\n\n{reason_block}")


def _s3_decision_intelligence(d: dict) -> str:
    ai    = d.get("ai_brain", {})
    thresh = d.get("thresholds", {})
    ss    = d.get("session_stats", {})
    mins  = d.get("mins_idle", 0.0)

    decision = _g(ai, "decision", default="MONITOR")
    mode     = _g(ai, "mode",     default="NORMAL")
    pf       = _g(ss, "profit_factor", default=0.0)
    wr       = _g(ss, "win_rate",      default=0.0)
    tier     = thresh.get("tier",     "NORMAL")
    score_mn = thresh.get("score_min", 0.58)
    af_state = thresh.get("af_state", "NORMAL")

    # WHY reasoning — truth engine enhanced
    truth = d.get("_truth", {})
    de    = truth.get("decision_enhance", {})

    why_lines = []
    if de.get("why_signals_rejected"):
        why_lines.append(de["why_signals_rejected"])
    if de.get("why_no_execution"):
        why_lines.append(de["why_no_execution"])
    if de.get("what_condition_missing"):
        why_lines.append(f"Missing condition: {de['what_condition_missing']}")

    if pf < 1.0:
        why_lines.append(f"Profit factor {pf:.2f} < 1.0 — system in drawdown recovery posture")
    if wr < 45:
        why_lines.append(f"Win rate {wr:.1f}% below 45% — signal quality degraded")
    if tier != "NORMAL":
        why_lines.append(f"Trade Activator {tier} — filters relaxed (score_min={score_mn:.3f})")
    if af_state == "TIGHTEN":
        why_lines.append("Adaptive Filter TIGHTEN — consecutive losses triggered quality increase")
    elif af_state == "RELAX":
        why_lines.append("Adaptive Filter RELAX — dry-spell triggered quality relaxation")
    if mins > 30:
        why_lines.append(f"Idle {mins:.0f} min — no qualifying setup across all pairs")
    if not why_lines:
        why_lines.append("All systems nominal — monitoring for next qualifying setup")

    # Alternative action — include trigger condition from truth engine
    what_triggers = de.get("what_triggers_execution")
    if pf < 1.0 and _g(ss, "n_trades", default=0) > 20:
        alt_action = "Pause new entries; review strategy DNA and RR structure before resuming"
    elif mins > 60:
        alt_action = "Consider forcing Alpha Engine scan cycle or manual signal injection"
    elif what_triggers:
        alt_action = f"Execution will resume when: {what_triggers}"
    else:
        alt_action = "Continue monitoring — system will execute on next qualifying setup"

    # WHAT NEEDED — from intelligence layer
    intel       = d.get("_intel", {})
    dec_intel   = intel.get("decision", {})
    missing_cond = dec_intel.get("missing_condition") or de.get("what_condition_missing") or "None"
    next_trigger = dec_intel.get("next_trigger") or what_triggers or alt_action

    body = (
        _table([
            ("AI Decision", decision),
            ("Mode",        mode),
            ("Tier",        tier),
            ("Score Min",   f"{score_mn:.3f}"),
            ("AF State",    af_state),
        ])
        + "\n\n**WHY:**\n" + _bullet(why_lines)
        + "\n\n**WHAT NEEDED:**\n" + _bullet([
            f"Missing condition: {missing_cond}",
            f"Next trigger: {next_trigger}",
        ])
        + "\n\n**Alternative Action:**\n" + alt_action
    )
    return _section("3. Decision Intelligence", body)


def _s4_risk_behavior(d: dict) -> str:
    risk = d.get("risk", {})
    dd   = d.get("drawdown", {})
    gate = d.get("gate", {})

    halted    = _g(risk, "halted",    default=False)
    halt_rsn  = _g(risk, "halt_reason", default="—")
    graceful  = _g(risk, "graceful_stop", default=False)
    can_trade = _g(gate, "can_trade", default=True)
    gate_rsn  = _g(gate, "reason",   default="ALL_CLEAR")
    dd_state  = _g(dd,   "state",    default="NORMAL")
    dd_pct    = _g(dd,   "current_drawdown_pct", default=0.0)
    dd_max    = _g(dd,   "max_drawdown_pct",     default=0.0)
    dd_mult   = _g(dd,   "size_multiplier",      default=1.0)

    if halted:
        risk_state = f"HALTED — {halt_rsn}"
    elif graceful:
        risk_state = "GRACEFUL STOP"
    elif not can_trade:
        risk_state = f"BLOCKED — {gate_rsn}"
    else:
        risk_state = "ACTIVE"

    body = _table([
        ("Risk State",       risk_state),
        ("Size Reduced?",    "Yes" if dd_mult < 1.0 else "No"),
        ("Trade Blocked?",   "Yes" if not can_trade else "No"),
        ("Kill Switch?",     "Yes" if halted else "No"),
        ("Halt Reason",      halt_rsn if halted else "—"),
        ("DD State",         dd_state),
        ("Current DD",       _pct(dd_pct)),
        ("Max DD (session)", _pct(dd_max)),
        ("Size Multiplier",  f"{dd_mult:.2f}×"),
        ("Gate Reason",      gate_rsn),
    ])
    return _section("4. Risk Engine Behavior", body)


def _s5_capital_efficiency(d: dict) -> str:
    cap   = d.get("capital", {})
    ss    = d.get("session_stats", {})
    tf    = d.get("trade_flow", {})
    mins  = d.get("mins_idle", 0.0)
    thr   = d.get("thresholds", {})

    initial     = _g(ss, "initial_capital", default=1000.0)
    equity      = _g(ss, "final_equity",    default=initial)
    pnl         = _g(ss, "total_net_pnl",   default=0.0)
    fees        = _g(ss, "total_fees_paid", default=0.0)
    daily_used  = cap.get("daily_risk_used",      0.0)
    daily_rem   = cap.get("daily_risk_remaining",  cap.get("daily_risk_cap", 0.03))
    daily_cap_pct = cap.get("daily_risk_cap", 0.03)

    capital_deployed_pct = abs(pnl + fees) / max(initial, 1) * 100
    capital_idle_pct     = 100.0 - min(capital_deployed_pct, 100.0)

    # Missed opportunity — truth engine has definitive answer
    truth     = d.get("_truth", {})
    cap_check = truth.get("capital_check", {})

    if cap_check.get("missed_opportunity"):
        missed = cap_check["missed_reason"]
    elif mins > 60:
        missed = (
            f"{mins:.0f} min idle at {thr.get('tier','?')} "
            f"(score_min={thr.get('score_min','?')}, vol_mult={thr.get('volume_multiplier','?')}×) — "
            "no signal cleared all quality gates"
        )
    else:
        missed = "None — system actively trading or recently traded"

    body = _table([
        ("Current Equity",        _money(equity)),
        ("Net PnL",               _money(pnl, signed=True)),
        ("Fees Paid",             _money(fees)),
        ("Capital Deployed",      _pct(capital_deployed_pct)),
        ("Capital Idle",          _pct(capital_idle_pct)),
        ("Daily Risk Used",       f"${daily_used:.2f}"),
        ("Daily Risk Remaining",  f"${daily_rem * (equity if daily_rem < 1 else 1):.2f}" if daily_rem < 1 else f"{_pct(daily_rem * 100)} of equity"),
        ("Daily Cap",             _pct(daily_cap_pct * 100)),
        ("Missed Opportunity",    missed),
    ])
    return _section("5. Capital Efficiency", body)


def _s6_performance_reality(d: dict) -> str:
    ss   = d.get("session_stats", {})
    edge = d.get("edge_engine",   {})

    wr       = _g(ss, "win_rate",       default=0.0) / 100.0
    avg_win  = _g(ss, "avg_win_usdt",   default=0.0)
    avg_loss = _g(ss, "avg_loss_usdt",  default=0.0)
    fees     = _g(ss, "total_fees_paid",default=0.0)
    pnl      = _g(ss, "total_net_pnl",  default=0.0)
    n_trades = _g(ss, "n_trades",       default=0)
    gross    = abs(pnl) + fees

    expectancy   = (wr * avg_win) + ((1.0 - wr) * avg_loss) if n_trades else 0.0
    fee_impact   = fees / max(gross, 1e-9) * 100
    fee_per_trade = fees / max(n_trades, 1)

    strategies = _g(edge, "strategies", default={})
    edge_lines = []
    for strat, info in strategies.items():
        e = info.get("edge", 0)
        wr_s = info.get("win_rate", 0)
        n = info.get("n_trades", 0)
        disabled = info.get("disabled", False)
        state = "DISABLED" if disabled else ("POSITIVE" if e > 0 else "NEGATIVE")
        edge_lines.append(f"- {strat}: edge={e:+.3f} wr={wr_s:.0%} n={n} [{state}]")

    truth    = d.get("_truth", {})
    split    = truth.get("split_metrics", {})
    is_mixed = split.get("is_mixed", False)
    hist_note = (
        "\n\n> **Note (FTD-025C):** Session trades = 0. "
        "Stats below are **HISTORICAL (lifetime)**, not current session."
        if is_mixed else ""
    )

    body = (
        hist_note
        + "\n\n" + _table([
            ("Expectancy / Trade",   _money(expectancy, signed=True)),
            ("Fee Impact",           _pct(fee_impact)),
            ("Fee per Trade (avg)",  _money(fee_per_trade)),
            ("Win Rate",             _pct(wr * 100)),
            ("Avg Win",              _money(avg_win, signed=True)),
            ("Avg Loss",             _money(avg_loss, signed=True)),
            ("Total Trades",         n_trades),
            ("Total Net PnL",        _money(pnl, signed=True)),
        ])
        + "\n\n**Edge Consistency (strategy × regime):**\n"
        + (_bullet(edge_lines) if edge_lines else "_Not enough trades to measure edge (need ≥20 per strategy-regime)._")
    )
    return _section("6. Performance Reality", body.lstrip("\n"))


def _s7_learning_memory(d: dict) -> str:
    mem = d.get("learning_memory", {})

    status   = mem.get("status",   "UNKNOWN")
    records  = mem.get("memory_records", 0)
    patterns = mem.get("total_patterns",  0)
    formed   = mem.get("formed_patterns", 0)
    neg_perm = mem.get("negative_memory_permanent", 0)
    neg_temp = mem.get("negative_memory_temporary", 0)

    body = _table([
        ("Status",               status),
        ("Memory Records",       records),
        ("Total Patterns",       patterns),
        ("Formed Patterns",      formed),
        ("Negative (Permanent)", neg_perm),
        ("Negative (Temporary)", neg_temp),
    ])

    if formed == 0:
        insight = (
            "\n\n_No patterns formed yet — learning engine requires more trades. "
            "Pattern formation begins once per-strategy samples accumulate. "
            "No strategies are banned; all remain eligible._"
        )
    else:
        insight = f"\n\n_{formed} pattern(s) formed — learning engine actively adjusting weights._"

    if neg_perm > 0:
        insight += f"\n\n**Warning:** {neg_perm} strategy/regime combination(s) permanently banned due to repeated losses."

    return _section("7. Learning Memory", body + insight)


def _s8_alert_intelligence(d: dict) -> str:
    # Prefer intel layer alerts (guaranteed NO_EXECUTION / SIGNAL_BLOCK / CONTRADICTION)
    intel = d.get("_intel", {})
    te_alerts = intel.get("alerts") or d.get("_truth", {}).get("alerts")

    if te_alerts is not None:
        if not te_alerts:
            formatted = ["No critical alerts — system operating within normal parameters."]
        else:
            formatted = [
                f"**{a['title']}**\n"
                f"  Cause: {a['cause']}\n"
                f"  Impact: {a['impact']}\n"
                f"  Fix: {a['fix']}"
                for a in te_alerts
            ]
        return _section("8. Alert Intelligence", "\n\n".join(formatted))

    # Fallback: original logic when truth engine is unavailable
    ss    = d.get("session_stats", {})
    tf    = d.get("trade_flow",    {})
    risk  = d.get("risk",          {})
    errors = d.get("errors",       [])
    mins  = d.get("mins_idle",     0.0)

    pf       = _g(ss, "profit_factor",   default=0.0)
    avg_win  = _g(ss, "avg_win_usdt",    default=0.0)
    avg_loss = _g(ss, "avg_loss_usdt",   default=0.0)
    fees     = _g(ss, "total_fees_paid", default=0.0)
    pnl      = _g(ss, "total_net_pnl",   default=0.0)
    n_trades = _g(ss, "n_trades",        default=0)
    halted   = _g(risk, "halted",        default=False)
    gross    = abs(pnl) + fees

    alerts = []

    if halted:
        alerts.append(
            "**HALT ACTIVE**\n"
            "  Cause: Risk kill-switch triggered\n"
            "  Impact: Zero new trades until manually cleared\n"
            "  Fix: Resolve halt condition; call /api/risk/resume"
        )

    if pf < 1.0 and n_trades >= 10:
        ratio = abs(avg_loss / avg_win) if avg_win else 0
        alerts.append(
            f"**LOW PROFIT FACTOR ({pf:.2f})**\n"
            f"  Cause: Avg loss ({_money(avg_loss)}) is {ratio:.1f}× avg win ({_money(avg_win)})\n"
            f"  Impact: Expected loss of {_money((1 - pf) * abs(avg_loss))} per {1/max(pf, 0.01):.0f} trades\n"
            f"  Fix: Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0"
        )

    if fees > 0 and gross > 0:
        fee_pct = fees / gross * 100
        if fee_pct > 20:
            alerts.append(
                f"**HIGH FEE DRAG ({fee_pct:.0f}% of gross)**\n"
                f"  Cause: Small-notional trades × maker/taker fee 0.1%\n"
                f"  Impact: Fees consuming {_money(fees)} of gross turnover\n"
                f"  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency"
            )

    if mins > 60:
        alerts.append(
            f"**TRADE DRY-SPELL ({mins:.0f} min)**\n"
            f"  Cause: No signal clearing all quality gates\n"
            f"  Impact: Capital idle; Trade Activator relaxing filters\n"
            f"  Fix: Check Alpha Engine signal quality; inspect top rejection reasons"
        )

    err_counts: dict[str, int] = {}
    for e in errors:
        code = e.get("code", "UNKNOWN")
        err_counts[code] = err_counts.get(code, 0) + 1
    for code, count in sorted(err_counts.items(), key=lambda x: -x[1]):
        if count >= 3:
            alerts.append(
                f"**RECURRING ERROR: {code} ({count} times)**\n"
                f"  Cause: Repeated indicator quality failure\n"
                f"  Impact: Affected symbols blocked from evaluation\n"
                f"  Fix: Check ATR/ADX thresholds for affected symbol"
            )
            break

    if not alerts:
        alerts.append("No critical alerts — system operating within normal parameters.")

    return _section("8. Alert Intelligence", "\n\n".join(alerts))


def _s9_root_cause(d: dict) -> str:
    truth  = d.get("_truth", {})
    rc     = truth.get("root_cause", {})

    if rc:
        primary  = rc["primary"]
        sec_list = rc.get("secondary", [])

        # Augment secondary with error patterns (these are not in truth engine)
        errors = d.get("errors", [])
        atr_errors = sum(1 for e in errors if "ATR_TOO_LOW" in e.get("extra", ""))
        if atr_errors > 5:
            sec_list = list(sec_list) + [
                f"ATR_TOO_LOW filter blocking major pairs ({atr_errors} hits) — "
                "large-cap pairs excluded during low-volatility windows"
            ]
        adx_errors = sum(1 for e in errors if "ADX_UNSTABLE" in e.get("extra", ""))
        if adx_errors > 3:
            sec_list = list(sec_list) + [f"ADX_UNSTABLE on range-bound pairs ({adx_errors} hits)"]

        secondary = _bullet(sec_list) if sec_list else "_No significant secondary causes identified._"

        body = f"**PRIMARY CAUSE:**\n{primary}\n\n**SECONDARY CAUSES:**\n{secondary}"
        return _section("9. Root Cause Analysis", body)

    # Fallback: original logic when truth engine unavailable
    ss     = d.get("session_stats", {})
    tf     = d.get("trade_flow",    {})
    errors = d.get("errors",        [])
    mins   = d.get("mins_idle",     0.0)
    thresh = d.get("thresholds",    {})

    pf       = _g(ss, "profit_factor",  default=0.0)
    avg_win  = _g(ss, "avg_win_usdt",   default=0.0)
    avg_loss = _g(ss, "avg_loss_usdt",  default=0.0)
    n_trades = _g(ss, "n_trades",       default=0)
    reasons  = tf.get("top_rejection_reasons", {})

    if pf < 1.0 and n_trades >= 10:
        ratio = abs(avg_loss / avg_win) if avg_win else 0
        primary = (
            f"**Negative expectancy (PF={pf:.2f})** — avg loss {ratio:.1f}× avg win. "
            f"Signal pipeline is functioning; the structural problem is that entries have "
            f"insufficient reward-to-risk. Every trade destroys expectancy on average."
        )
    elif mins > 60:
        primary = (
            f"**Signal scarcity ({mins:.0f} min idle)** — Trade Activator is in "
            f"{thresh.get('tier','?')} with score_min={thresh.get('score_min','?'):.3f}, "
            f"but no signal is clearing the full quality chain. "
            f"Market conditions do not match any strategy's entry criteria."
        )
    else:
        primary = "**No critical root cause identified** — system operating normally."

    secondary_parts = []
    if reasons:
        top_reason, top_count = max(reasons.items(), key=lambda x: x[1])
        secondary_parts.append(f"Top skip reason `{top_reason}` ({top_count} times) blocking signal flow")

    atr_errors = sum(1 for e in errors if "ATR_TOO_LOW" in e.get("extra", ""))
    if atr_errors > 5:
        secondary_parts.append(
            f"ATR_TOO_LOW filter blocking major pairs ({atr_errors} hits) — "
            "large-cap pairs excluded during low-volatility windows"
        )

    adx_errors = sum(1 for e in errors if "ADX_UNSTABLE" in e.get("extra", ""))
    if adx_errors > 3:
        secondary_parts.append(f"ADX_UNSTABLE on range-bound pairs ({adx_errors} hits)")

    secondary = _bullet(secondary_parts) if secondary_parts else "_No significant secondary causes identified._"

    body = (
        f"**PRIMARY CAUSE:**\n{primary}\n\n"
        f"**SECONDARY CAUSES:**\n{secondary}"
    )
    return _section("9. Root Cause Analysis", body)


def _s10_action_plan(d: dict) -> str:
    ss    = d.get("session_stats", {})
    errors = d.get("errors",       [])
    mins  = d.get("mins_idle",     0.0)

    pf       = _g(ss, "profit_factor", default=0.0)
    n_trades = _g(ss, "n_trades",      default=0)
    fees     = _g(ss, "total_fees_paid", default=0.0)

    immediate, short_term, long_term = [], [], []

    # Immediate actions
    atr_errors = sum(1 for e in errors if "ATR_TOO_LOW" in e.get("extra", ""))
    if atr_errors > 5:
        immediate.append("ATR floor already reduced (qFTD-032-R4) — BTCUSDT/BNBUSDT now scannable")

    if pf < 1.0 and n_trades >= 10:
        immediate.append("Increase rr_min 1.5 → 2.0 in config.py (reject RR < 2.0 entries)")
        immediate.append("Reduce ACTIVATOR_T1_SCORE to 0.42 (allow borderline setups at TIER_1)")

    if mins > 90:
        immediate.append(f"Investigate top skip reasons — idle {mins:.0f} min suggests systematic quality miss")

    if not immediate:
        immediate.append("No immediate action required — maintain current configuration")

    # Short-term
    short_term.append("Review Alpha Engine TrendBreakout RR — single trade data suggests poor setup quality")
    short_term.append("Add session PF circuit breaker: if session_pf < 0.5 after ≥20 trades → pause 30 min")
    if fees > 30:
        short_term.append("Raise MIN_NOTIONAL_USDT to reduce fee drag per trade")

    # Long-term
    long_term.append("Strategy DNA overhaul via genome evolution (Volatility Expansion showing 0 usage)")
    long_term.append("Implement regime stability filter: require regime stable ≥ 3 consecutive candles before entry")
    long_term.append("Build per-symbol expectancy tracking — remove symbols with PF < 0.8 after 20+ trades")

    body = (
        "**IMMEDIATE (restart not required):**\n" + _bullet(immediate)
        + "\n\n**SHORT TERM (next session):**\n" + _bullet(short_term)
        + "\n\n**LONG TERM (strategy evolution):**\n" + _bullet(long_term)
    )
    return _section("10. Action Plan", body)


def _s11_developer_export(d: dict) -> str:
    ss    = d.get("session_stats", {})
    tf    = d.get("trade_flow",    {})
    thresh = d.get("thresholds",   {})
    gate  = d.get("gate",          {})
    errors = d.get("errors",       [])
    mins  = d.get("mins_idle",     0.0)
    ts    = d.get("generated_at",  "—")

    pf       = _g(ss, "profit_factor", default=0.0)
    n_trades = _g(ss, "n_trades",      default=0)
    can_trade = _g(gate, "can_trade",  default=True)
    gate_rsn  = _g(gate, "reason",     default="ALL_CLEAR")

    err_summary: dict[str, int] = {}
    for e in errors:
        key = f"{e.get('code','?')}:{e.get('extra','')[:30]}"
        err_summary[key] = err_summary.get(key, 0) + 1
    top_errors = sorted(err_summary.items(), key=lambda x: -x[1])[:5]

    # Developer Summary from intel layer
    intel    = d.get("_intel", {})
    exec_i   = intel.get("execution", {})
    dec_i    = intel.get("decision",  {})
    cap_i    = intel.get("capital",   {})

    issue_str   = d.get("primary_issue", "None")
    cause_str   = exec_i.get("dominant_block", "N/A") if exec_i.get("has_gap") else "N/A"
    fix_str     = dec_i.get("next_trigger", "Continue monitoring")

    dev_summary = (
        f"**Developer Summary**\n\n"
        f"- Issue:  {issue_str}\n"
        f"- Cause:  {cause_str} dominant block"
        + (f" ({exec_i.get('execution_gap', '')})" if exec_i.get("has_gap") else "")
        + f"\n- Capital Idle:  {cap_i.get('capital_idle_pct_str', 'N/A')}"
        + (" (missed opportunity)" if cap_i.get("missed_opportunity") else "")
        + f"\n- Fix:    {fix_str}\n"
    )

    body = (
        dev_summary
        + f"\n```\n"
        f"Generated:       {ts}\n"
        f"Trades (total):  {n_trades}  |  PF: {pf:.3f}  |  WR: {_g(ss, 'win_rate', default=0):.1f}%\n"
        f"Gate:            can_trade={can_trade}  reason={gate_rsn}\n"
        f"Tier:            {thresh.get('tier','?')}  "
        f"score_min={thresh.get('score_min','?')}  "
        f"vol_mult={thresh.get('volume_multiplier','?')}×\n"
        f"Idle:            {mins:.1f} min\n"
        f"Signals/hr:      {tf.get('signals_per_hour', 0):.1f}  "
        f"Skips(window):   {tf.get('total_skips', 0)}\n"
        + (
            "Top Errors:\n" + "\n".join(f"  {k}: {v}×" for k, v in top_errors)
            if top_errors else "Top Errors:      none\n"
        )
        + f"\n```"
    )
    return _section("11. Developer Export", body)


# ── FTD-033 Section builders ──────────────────────────────────────────────────

def _s12_execution_analysis(d: dict) -> str:
    """FTD-033 Part 3+4 — Execution gap and gate trace summary."""
    et  = d.get("execution_trace", {})
    gt  = d.get("gate_trace", {})

    total    = et.get("total_signals", 0)
    executed = et.get("executed", 0)
    rejected = et.get("rejected", 0)
    exec_rate = et.get("execution_rate_pct", 0.0)
    dominant = et.get("dominant_block", gt.get("dominant_block", "N/A"))
    top_rej  = et.get("top_rejection", "N/A")

    reasons  = et.get("rejection_reasons", {})
    gate_bd  = et.get("gate_breakdown", {})

    rej_lines = "\n".join(
        f"- {r}: {pct}%" for r, pct in list(reasons.items())[:5]
    ) if reasons else "- None recorded"

    gate_stats = gt.get("gate_stats", {})
    gate_lines = "\n".join(
        f"- {name}: PASS={s.get('pass', 0)} FAIL={s.get('fail', 0)} ({s.get('pass_pct', 0.0):.1f}% pass)"
        for name, s in gate_stats.items()
    ) if gate_stats else "- No gate data"

    body = (
        _table([
            ("Signals Evaluated",  str(total)),
            ("Executed",           str(executed)),
            ("Rejected",           str(rejected)),
            ("Execution Rate",     f"{exec_rate:.1f}%"),
            ("Dominant Block",     dominant),
            ("Top Rejection Reason", top_rej),
        ])
        + f"\n\n**Rejection Breakdown:**\n{rej_lines}"
        + f"\n\n**Gate Status:**\n{gate_lines}"
    )
    return _section("12. Execution Analysis (FTD-033)", body)


def _s13_cost_analysis(d: dict) -> str:
    """FTD-033 Part 1+2 — Cost breakdown and net edge summary."""
    ca  = d.get("cost_analysis", {})
    ss  = d.get("session_stats", {})

    n_trades       = _g(ss, "n_trades", default=0)
    fees_paid      = _g(ss, "fees_paid", default=0.0)
    gross_pnl      = _g(ss, "gross_pnl", default=None)
    avg_cost       = ca.get("avg_cost_pct", 0.0)
    high_cost_syms = ca.get("high_cost_symbols", [])

    cost_impact = "N/A"
    if gross_pnl and abs(gross_pnl) > 0:
        cost_impact = f"{fees_paid / abs(gross_pnl) * 100:.1f}% of gross profit"

    syms_str = ", ".join(high_cost_syms) if high_cost_syms else "None"

    body = _table([
        ("Avg Cost per Trade",   f"{avg_cost:.4f}%"),
        ("Total Fees Paid",      f"{fees_paid:.4f} USDT"),
        ("Cost Impact",          cost_impact),
        ("High-Cost Symbols",    syms_str),
        ("Trades Evaluated",     str(n_trades)),
    ])
    return _section("13. Cost Analysis (FTD-033)", body)


def _s14_net_edge_summary(d: dict) -> str:
    """FTD-033 Part 2+5 — Net edge distribution across evaluated signals."""
    ne  = d.get("net_edge_summary", {})
    cl  = d.get("cost_learning", {})

    total_eval     = ne.get("total_evaluated", 0)
    pos_edge_pct   = ne.get("positive_net_edge_pct", 0.0)
    rej_cost_pct   = ne.get("rejected_due_to_cost_pct", 0.0)
    avg_alpha      = ne.get("avg_alpha_score", 0.0)

    strategy_rows  = ne.get("strategy_summary", {})
    strat_lines = "\n".join(
        f"- {k}: count={v.get('count', 0)} avg_alpha={v.get('avg_alpha', 0):.4f} approval={v.get('approval_rate_pct', 0):.1f}%"
        for k, v in strategy_rows.items()
    ) if strategy_rows else "- No data"

    blacklisted    = cl.get("blacklisted_keys", [])
    bl_str         = ", ".join(blacklisted) if blacklisted else "None"

    body = (
        _table([
            ("Signals Evaluated",        str(total_eval)),
            ("With Positive Net Edge",   f"{pos_edge_pct:.1f}%"),
            ("Rejected Due to Cost",     f"{rej_cost_pct:.1f}%"),
            ("Avg Alpha Score",          f"{avg_alpha:.4f}"),
            ("Blacklisted Patterns",     bl_str),
        ])
        + f"\n\n**Strategy Net Edge:**\n{strat_lines}"
    )
    return _section("14. Net Edge Summary (FTD-033)", body)


def _s15_developer_summary_ftd033(d: dict) -> str:
    """FTD-033 Part 8 — Upgraded developer summary with execution root cause."""
    et    = d.get("execution_trace",   {})
    gt    = d.get("gate_trace",        {})
    ca    = d.get("cost_analysis",     {})
    ne    = d.get("net_edge_summary",  {})
    ss    = d.get("session_stats",     {})
    intel = d.get("_intel",            {})
    cap_i = intel.get("capital",       {})

    dominant_block   = et.get("dominant_block", gt.get("dominant_block", "N/A"))
    dominant_reason  = gt.get("dominant_reason", "")
    pos_edge_pct     = ne.get("positive_net_edge_pct", 0.0)
    exec_rate        = et.get("execution_rate_pct", 0.0)
    pf               = _g(ss, "profit_factor", default=0.0)
    capital_idle_str = cap_i.get("capital_idle_pct_str", "N/A")

    block_str = dominant_block
    if dominant_reason:
        block_str += f" ({dominant_reason})"

    fix_lines = []
    if exec_rate < 10 and dominant_block != "N/A":
        fix_lines.append(f"Reduce score threshold OR improve signal quality (block: {block_str})")
    if pos_edge_pct < 30:
        fix_lines.append("Improve RR — fewer signals have positive net edge after costs")
    if pf < 1.0:
        fix_lines.append("Widen TP targets to ≥1.5R to recover profit factor above 1.0")
    if not fix_lines:
        fix_lines.append("Continue monitoring — no critical execution block detected")

    body = (
        f"**FTD-033 Developer Summary**\n\n"
        f"- Issue: No execution / low execution rate\n"
        f"- Cause: {block_str} dominates rejections\n"
        f"- Capital Idle: {capital_idle_str}\n"
        f"- Net Edge Coverage: {pos_edge_pct:.1f}% of signals have positive edge after costs\n"
        f"- Execution Rate: {exec_rate:.1f}%\n"
        f"- Fix:\n"
        + "\n".join(f"  - {f}" for f in fix_lines)
    )
    return _section("15. Developer Summary (FTD-033)", body)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_full_report_v2(data: dict) -> str:
    """
    Generate the FTD-025B-URX-V2 + FTD-025C Unified Report.

    Pipeline (FTD-025C): data → truth_engine.process() → corrected_data → sections

    Args:
        data: dict assembled by the caller (main.py endpoint).
              Keys: trade_flow, mins_idle, thresholds, session_stats,
                    capital, risk, gate, errors, learning_memory,
                    ct_scan, ai_brain, drawdown, activator, thoughts,
                    edge_engine, generated_at.

    Returns:
        Formatted Markdown string with 11 sections.
    """
    # FTD-025C: truth engine — contradiction detection + root cause resolution
    data = _truth_process(data)
    # FTD-025CD: intelligence layer — execution / decision / capital / learning depth
    data = _intel_enrich(data)

    ts = data.get("generated_at", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()))

    header = (
        f"# EOW Quant Engine — Unified System Report v2\n\n"
        f"_Generated: {ts}_  \n"
        f"_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_\n\n"
        f"---\n\n"
        f"> **Design principle:** Truth → Insight → Decision → Action  \n"
        f"> Every section answers WHY, not just WHAT."
    )

    sections = [
        _s1_executive_snapshot(data),
        _s2_signal_flow(data),
        _s3_decision_intelligence(data),
        _s4_risk_behavior(data),
        _s5_capital_efficiency(data),
        _s6_performance_reality(data),
        _s7_learning_memory(data),
        _s8_alert_intelligence(data),
        _s9_root_cause(data),
        _s10_action_plan(data),
        _s11_developer_export(data),
        # FTD-033 sections
        _s12_execution_analysis(data),
        _s13_cost_analysis(data),
        _s14_net_edge_summary(data),
        _s15_developer_summary_ftd033(data),
    ]

    return header + "\n\n" + "\n\n".join(sections)

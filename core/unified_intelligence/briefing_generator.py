"""
core/unified_intelligence/briefing_generator.py

Generates 00_BRIEFING.md — the synthesized "read-first" intelligence document
in the One-Click Unified Intelligence Package.

The briefing answers the most important diagnostic questions immediately,
without requiring navigation through individual data files.  It is derived
entirely from the `data` dict assembled by the unified_intelligence_export()
endpoint, with every field access defensive so a missing subsystem never
crashes the entire export.
"""

from __future__ import annotations
import time
from typing import Any


# ── Formatting helpers ────────────────────────────────────────────────────────

def _g(obj: Any, *keys, default: Any = "N/A") -> Any:
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return default
        val = cur.get(k)
        if val is None:
            return default
        cur = val
    return cur


def _fmt_usd(v: Any, default: str = "N/A") -> str:
    if not isinstance(v, (int, float)):
        return default
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f} USDT"


def _fmt_pct(v: Any, default: str = "N/A") -> str:
    if not isinstance(v, (int, float)):
        return default
    return f"{v:.1f}%"


def _fmt_dur(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    h = int(seconds / 3600)
    m = int((seconds % 3600) / 60)
    return f"{h}h {m}m"


def _fmt_mins(minutes: float) -> str:
    if minutes <= 0:
        return "< 1m"
    if minutes < 60:
        return f"{int(minutes)}m"
    h = int(minutes / 60)
    m = int(minutes % 60)
    return f"{h}h {m}m"


def _pf_str(pf: Any) -> str:
    if not isinstance(pf, (int, float)):
        return "N/A"
    if pf == float("inf"):
        return "∞ (no losses)"
    return f"{pf:.3f}"


# ── Section builders ─────────────────────────────────────────────────────────

def _build_alerts(data: dict, mins_idle: float, n_trades: int,
                  pf: float, obs_status: str) -> str:
    alerts = []

    if mins_idle > 120:
        alerts.append(
            f"**TRADE DROUGHT [{_fmt_mins(mins_idle)}]**: Signal pipeline has been silent — "
            f"investigate gates (check 02_signal_intelligence/)")
    elif mins_idle > 30:
        alerts.append(
            f"**IDLE WARNING [{_fmt_mins(mins_idle)}]**: Extended period without a completed trade")

    halt = data.get("halt_audit") or {}
    if halt.get("halted"):
        alerts.append("**ENGINE HALTED**: Risk controller triggered halt — no new positions being opened")
    if halt.get("graceful_stop"):
        alerts.append("**GRACEFUL STOP**: Engine winding down — no new entries allowed")

    obs_e = data.get("obs_escalations") or {}
    for esc in (obs_e.get("active") or [])[:3]:
        sev     = _g(esc, "severity", default="?")
        trigger = str(_g(esc, "trigger", default="unknown"))[:70]
        cats    = ", ".join(_g(esc, "anomaly_categories", default=[]) or [])
        alerts.append(
            f"**ESCALATION [{sev}]**: {trigger}" + (f" ({cats})" if cats else ""))

    if obs_status in ("STALE", "DEGRADED", "COLD"):
        alerts.append(
            f"**OBSERVABILITY {obs_status}**: Monitoring pipeline is not operating normally")

    if n_trades == 0:
        alerts.append(
            "**ZERO TRADES**: No completed trades this session — RL bandit cannot accumulate learning")
    elif n_trades >= 10 and isinstance(pf, float) and 0 < pf < 1.0:
        alerts.append(
            f"**NEGATIVE EDGE**: Profit Factor = {_pf_str(pf)} — system is consuming capital")

    rl_sum = data.get("rl_summary") or {}
    if rl_sum.get("total_pulls", 0) == 0 and n_trades > 0:
        alerts.append(
            "**RL COLD**: 0 total RL pulls despite trades — learning pipeline may be disconnected")

    return ("".join(f"> {a}\n" for a in alerts)
            if alerts
            else "> None — Engine operating within normal parameters\n")


def _build_escalation_table(obs_e: dict) -> str:
    active = obs_e.get("active") or []
    if not active:
        return "_No active escalations._\n"
    rows = "| Severity | Trigger | Age | Status |\n|---------|---------|-----|--------|\n"
    for esc in active[:8]:
        sev     = _g(esc, "severity", default="?")
        trigger = str(_g(esc, "trigger", default="?"))[:55]
        status  = _g(esc, "status", default="?")
        ts_ms   = _g(esc, "ts", default=0)
        age_str = _fmt_dur((time.time() * 1000 - ts_ms) / 1000) if ts_ms else "?"
        rows += f"| {sev} | {trigger} | {age_str} | {status} |\n"
    return rows


def _build_anomaly_counts(obs_a: dict) -> str:
    summary = obs_a.get("active_summary") or {}
    lines = [
        f"- **{sev}**: {summary[sev]}"
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        if summary.get(sev, 0)
    ]
    return "\n".join(lines) if lines else "_No active anomalies._"


def _build_rejection_table(top_reasons: dict) -> str:
    if not top_reasons:
        return "  (no rejection data in current window)"
    lines = []
    for reason, count in sorted(top_reasons.items(), key=lambda x: -x[1])[:5]:
        lines.append(f"  {reason}: {count}")
    return "\n".join(lines)


def _build_rl_contexts(label: str, contexts: list) -> str:
    if not contexts:
        return f"**{label}:** No data\n\n"
    header = (f"**{label}:**\n"
              "| Context | Q-Value | Visits | Win Rate |\n"
              "|---------|---------|--------|----------|\n")
    rows = ""
    for ctx in contexts[:5]:
        if not isinstance(ctx, dict):
            continue
        key    = str(_g(ctx, "context", default="?"))[:52]
        q      = _g(ctx, "q_value", default=0.0)
        visits = _g(ctx, "n_visits", default=0)
        wr     = _g(ctx, "win_rate", default=0.0)
        wr_str = _fmt_pct(wr * 100 if isinstance(wr, float) and wr <= 1.0 else wr)
        q_str  = f"{q:+.3f}" if isinstance(q, float) else str(q)
        rows  += f"| {key} | {q_str} | {visits} | {wr_str} |\n"
    return header + rows + "\n"


def _build_genome_table(active_dna: dict) -> str:
    if not active_dna:
        return "_No genome data available_\n"
    header = ("| Strategy | Gen | Train PF | OOS PF | OOS WR | Promoted |\n"
              "|----------|-----|---------|--------|--------|----------|\n")
    rows = ""
    for strat, dna in active_dna.items():
        if not isinstance(dna, dict):
            continue
        gen   = _g(dna, "generation", default="?")
        tpf   = _g(dna, "train_pf", default=None)
        opf   = _g(dna, "oos_pf",   default=None)
        owr   = _g(dna, "oos_wr",   default=None)
        promo = "YES" if _g(dna, "promoted", default=False) else "NO"
        tpf_s = f"{tpf:.2f}" if isinstance(tpf, float) else "N/A"
        opf_s = f"{opf:.2f}" if isinstance(opf, float) else "N/A"
        owr_s = _fmt_pct(owr * 100 if isinstance(owr, float) and owr <= 1 else owr)
        rows += f"| {strat} | G{gen} | {tpf_s} | {opf_s} | {owr_s} | {promo} |\n"
    return header + (rows if rows else "_No entries_\n")


def _build_alpha_engine_table(alpha_conf: dict) -> str:
    sub    = alpha_conf.get("sub_engine_states") or {}
    scores = alpha_conf.get("sub_engine_scores")  or {}
    if not sub:
        return "_No sub-engine data_\n"
    label_map = {
        "i1_statistical":  ("I.1 Statistical",  "statistical_score"),
        "i2_oos":          ("I.2 OOS",           "oos_score"),
        "i3_fee_survival": ("I.3 Fee Survival",  "fee_score"),
        "i4_regime":       ("I.4 Regime",        "regime_score"),
        "i5_drawdown":     ("I.5 Drawdown",      "drawdown_score"),
    }
    header = "| Engine | State | Score |\n|--------|-------|-------|\n"
    rows = ""
    for key, (label, score_key) in label_map.items():
        state = _g(sub, key, default="?")
        score = scores.get(score_key, "?")
        rows += f"| {label} | {state} | {score} |\n"
    return header + rows


def _build_top_findings(data: dict, mins_idle: float, n_trades: int,
                         pf: float, net_pnl: float, total_fees: float) -> str:
    findings = []

    if mins_idle > 60:
        findings.append(
            f"Trade drought: {_fmt_mins(mins_idle)} without a trade — investigate signal pipeline and gates")

    rl_sum = data.get("rl_summary") or {}
    if rl_sum.get("total_pulls", 0) == 0:
        findings.append(
            "RL bandit: 0 total pulls — RL has never been asked to gate a trade this session")

    if n_trades >= 10 and isinstance(pf, float) and 0 < pf < 1.0:
        findings.append(f"Negative profit factor ({pf:.3f}) — more capital consumed than earned")

    if total_fees > 0 and (abs(net_pnl) + total_fees) > 0:
        fee_drag_pct = total_fees / (abs(net_pnl) + total_fees) * 100
        if fee_drag_pct > 30:
            findings.append(f"High fee drag: {fee_drag_pct:.0f}% of gross PnL consumed by fees")

    toxic_count = rl_sum.get("toxic_contexts", 0)
    if isinstance(toxic_count, int) and toxic_count > 0:
        findings.append(
            f"RL: {toxic_count} toxic context(s) blocking entries in those regime/session/strategy combinations")

    alpha_conf = data.get("alpha_confirmation") or {}
    ac_tier   = alpha_conf.get("alpha_tier", "UNKNOWN")
    ac_trades = alpha_conf.get("trade_count", n_trades) or n_trades
    if ac_tier in ("UNPROVEN", "DEVELOPING"):
        need = max(0, 300 - ac_trades)
        findings.append(
            f"Alpha gate {ac_tier} (score={alpha_conf.get('alpha_score', 0)}/100): "
            f"need {need} more trades for Phase-I certification")

    genome_s = data.get("genome_state") or {}
    for strat, dna in (genome_s.get("active_dna") or {}).items():
        if isinstance(dna, dict):
            opf = dna.get("oos_pf")
            if isinstance(opf, float) and opf < 0.3:
                findings.append(
                    f"Genome {strat}: OOS PF={opf:.2f} — severely overfitted, signals may be noise")

    tf = data.get("trade_flow") or {}
    rej_rate = tf.get("rejection_rate_pct", 0.0)
    if isinstance(rej_rate, float) and rej_rate > 90:
        findings.append(f"Signal rejection rate {rej_rate:.0f}% — nearly all signals are being filtered out")

    obs_h      = data.get("obs_health") or {}
    obs_status = obs_h.get("status", "UNKNOWN")
    if obs_status in ("STALE", "DEGRADED"):
        findings.append(f"Observability pipeline {obs_status} — monitoring data may be stale")

    if not findings:
        findings.append("No critical issues detected — system operating within normal parameters")

    return "".join(f"{i}. {f}\n" for i, f in enumerate(findings[:10], 1))


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_briefing(data: dict) -> str:
    """Return the full 00_BRIEFING.md content as a string."""

    captured_at = data.get("captured_at", "Unknown")
    version     = data.get("version", "?")
    boot_ts     = data.get("boot_ts") or 0.0
    bypass_mode = data.get("bypass_mode", True)

    # Session stats
    ss          = data.get("session_stats") or {}
    n_trades    = ss.get("total_trades", 0) or 0
    net_pnl     = ss.get("total_net_pnl", 0.0) or 0.0
    win_rate    = ss.get("win_rate", 0.0) or 0.0
    pf          = ss.get("profit_factor", 0.0) or 0.0
    sharpe      = ss.get("sharpe_ratio", 0.0) or 0.0
    max_dd      = ss.get("max_drawdown_pct", 0.0) or 0.0
    total_fees  = ss.get("total_fees_paid", 0.0) or 0.0
    capital     = ss.get("capital", 0.0) or 0.0

    # Trade flow
    tf        = data.get("trade_flow") or {}
    mins_idle = tf.get("minutes_since_last_trade") or 0.0
    sigs_ph   = tf.get("signals_per_hour", "N/A")
    trades_ph = tf.get("trades_per_hour", "N/A")
    rej_rate  = tf.get("rejection_rate_pct", 0.0)

    # Observability
    obs_h      = data.get("obs_health")      or {}
    obs_a      = data.get("obs_anomalies")   or {}
    obs_e      = data.get("obs_escalations") or {}
    obs_status = obs_h.get("status", "UNKNOWN")

    # Halt state
    halt          = data.get("halt_audit") or {}
    halted        = halt.get("halted", False)
    graceful_stop = halt.get("graceful_stop", False)

    # RL
    rl_sum      = data.get("rl_summary") or {}
    rl_pulls    = rl_sum.get("total_pulls", 0)
    rl_allowed  = rl_sum.get("total_allowed", 0)
    rl_allow_r  = rl_sum.get("allow_rate", 0.0)
    rl_contexts = rl_sum.get("total_contexts", 0)
    rl_toxic    = rl_sum.get("toxic_contexts", 0)
    rl_top      = rl_sum.get("top_contexts")    or []
    rl_bottom   = rl_sum.get("bottom_contexts") or []

    # Alpha confirmation
    alpha_conf = data.get("alpha_confirmation") or {}
    ac_tier    = alpha_conf.get("alpha_tier", "UNKNOWN")
    ac_score   = alpha_conf.get("alpha_score", 0)
    ac_gate    = alpha_conf.get("gate_status", "UNKNOWN")
    ac_trades  = alpha_conf.get("trade_count", n_trades) or n_trades

    # Economic truth
    econ       = data.get("economic_truth") or {}
    et_verdict = _g(econ, "survivability_verdict",   default="UNKNOWN")
    et_net_exp = _g(econ, "overall_net_expectancy",  default=None)
    et_regime  = _g(econ, "overall_regime_health",   default="UNKNOWN")

    # Survivability / equilibrium
    surv      = data.get("survivability") or {}
    equil     = data.get("equilibrium")   or {}
    sv_verdict = _g(surv,  "verdict", default="UNKNOWN")
    eq_verdict = _g(equil, "verdict", default="UNKNOWN")

    # Genome
    genome_s   = data.get("genome_state") or {}
    active_dna = genome_s.get("active_dna") or {}

    # System status
    sys_s      = data.get("system_status") or {}
    n_positions = len(data.get("positions") or [])
    n_symbols   = sys_s.get("symbols_watched", "?")

    # Deployability
    deploy        = data.get("deployability") or {}
    deploy_score  = deploy.get("score", 0)   if isinstance(deploy, dict) else 0
    deploy_status = deploy.get("status", "UNKNOWN") if isinstance(deploy, dict) else "UNKNOWN"

    # Uptime
    uptime_str = _fmt_dur(time.time() - boot_ts) if boot_ts > 0 else "Unknown"

    # Last skip
    last_skip_d   = data.get("last_skip") or {}
    skip_total    = last_skip_d.get("skip_total", 0)
    recent_skips  = last_skip_d.get("recent_msgs") or []
    last_skip_text = (recent_skips[-1] if recent_skips else "None")[:120]

    # Thought log counts
    thought_log = data.get("thought_log") or []
    tl_signal   = sum(1 for t in thought_log if _g(t, "level") == "SIGNAL")
    tl_filter   = sum(1 for t in thought_log if _g(t, "level") == "FILTER")
    tl_trade    = sum(1 for t in thought_log if _g(t, "level") == "TRADE")

    # Regime map summary
    regime_map    = data.get("regime_map") or {}
    regime_counts: dict = {}
    for sym, rs in regime_map.items():
        r = (_g(rs, "regime") if isinstance(rs, dict) else "UNKNOWN") or "UNKNOWN"
        regime_counts[r] = regime_counts.get(r, 0) + 1
    regime_summary = (", ".join(f"{r}={c}" for r, c in sorted(regime_counts.items()))
                      if regime_counts else "No data")

    allow_r_str = (_fmt_pct(rl_allow_r * 100
                            if isinstance(rl_allow_r, float) and rl_allow_r <= 1.0
                            else rl_allow_r))

    mode_str    = "PAPER (BYPASS_ALL_GATES=True)" if bypass_mode else "LIVE"
    exp_str     = (_fmt_usd(et_net_exp)
                   if isinstance(et_net_exp, (int, float)) else "N/A")

    return f"""# PHOENIX Intelligence Briefing
**Snapshot:** {captured_at} | **Engine:** v{version} | **Mode:** {mode_str}

---

## CRITICAL ALERTS

{_build_alerts(data, mins_idle, n_trades, pf, obs_status)}
---

## 1. OPERATIONAL STATUS

| Field | Value |
|-------|-------|
| Engine Halted | {halted} |
| Graceful Stop | {graceful_stop} |
| Uptime | {uptime_str} |
| Observability Pipeline | {obs_status} |
| Capital (Equity) | {_fmt_usd(capital)} |
| Max Drawdown | {_fmt_pct(max_dd)} |
| Deployability | {deploy_score}/100 ({deploy_status}) |
| Open Positions | {n_positions} |
| Symbols Watched | {n_symbols} |

---

## 2. TRADING ACTIVITY

| Metric | Value |
|--------|-------|
| Total Trades | {n_trades} |
| Net PnL | {_fmt_usd(net_pnl)} |
| Win Rate | {_fmt_pct(win_rate)} |
| Profit Factor | {_pf_str(pf)} |
| Sharpe Ratio | {f"{sharpe:.2f}" if isinstance(sharpe, float) else "N/A"} |
| Max Drawdown | {_fmt_pct(max_dd)} |
| Total Fees Paid | {_fmt_usd(total_fees)} |
| Avg Win | {_fmt_usd(ss.get("avg_win_usdt"))} |
| Avg Loss | {_fmt_usd(ss.get("avg_loss_usdt"))} |
| Minutes Since Last Trade | {_fmt_mins(mins_idle)} |

---

## 3. SIGNAL PIPELINE

| Metric | Value |
|--------|-------|
| Signals / Hour | {sigs_ph} |
| Trades / Hour | {trades_ph} |
| Rejection Rate | {_fmt_pct(rej_rate)} |
| Skips This Session | {skip_total} |
| CT-Scan SIGNAL entries (last 100) | {tl_signal} |
| CT-Scan FILTER entries (last 100) | {tl_filter} |
| CT-Scan TRADE entries (last 100) | {tl_trade} |
| Last Skip Reason | `{last_skip_text}` |

**Top Rejection Reasons:**
```
{_build_rejection_table(tf.get("top_rejection_reasons", {}))}
```

**Market Regime Distribution:** {regime_summary}

---

## 4. ANOMALIES & ESCALATIONS

{_build_escalation_table(obs_e)}
**Active Anomaly Counts:**
{_build_anomaly_counts(obs_a)}

---

## 5. ECONOMIC TRUTH VERDICT

| Dimension | Verdict |
|-----------|---------|
| Survivability (Phase-D) | {et_verdict} |
| Net Expectancy / Trade | {exp_str} |
| Regime Health | {et_regime} |
| Survivability (Phase-E) | {sv_verdict} |
| Equilibrium (Phase-F) | {eq_verdict} |

---

## 6. ALPHA CONFIRMATION (Phase-I)

| Field | Value |
|-------|-------|
| Alpha Tier | {ac_tier} |
| Alpha Score | {ac_score} / 100 |
| Gate Status | {ac_gate} |
| Trades in Window | {ac_trades} |
| Live Deployment Authorized | False (constitutional invariant) |

{_build_alpha_engine_table(alpha_conf)}

---

## 7. RL LEARNING STATE

| Metric | Value |
|--------|-------|
| Total Contexts | {rl_contexts} |
| Total Pulls | {rl_pulls} |
| Total Allowed | {rl_allowed} |
| Allow Rate | {allow_r_str} |
| Toxic Contexts | {rl_toxic} |

{_build_rl_contexts("Top Performing Contexts", rl_top)}{_build_rl_contexts("Worst Performing Contexts", rl_bottom)}

---

## 8. GENOME & STRATEGY STATE

{_build_genome_table(active_dna)}

---

## 9. TOP DIAGNOSTIC FINDINGS

{_build_top_findings(data, mins_idle, n_trades, pf, net_pnl, total_fees)}
---

## ARCHITECTURE REFERENCE

| Diagnostic Question | File |
|--------------------|------|
| Why no trades? | `02_signal_intelligence/trade_flow.json` + `02_signal_intelligence/thought_log.json` |
| Which signals are blocked? | `02_signal_intelligence/last_skip.json` |
| RL Q-table (all contexts) | `03_live_process_snapshot/rl_qtable.json` |
| Economic truth (all 6 engines) | `04_economic_truth/orchestration.json` |
| Full learning intelligence (29 sections) | `05_alpha_and_learning/lio_full_snapshot.json` |
| Alpha certification status | `06_risk_and_governance/alpha_confirmation.json` |
| Execution governance | `06_risk_and_governance/execution_governance.json` |
| Capital & AEE state | `07_capital_and_performance/aee_state.json` + `07_capital_and_performance/capital_flow.json` |
| Genome DNA & evolution | `09_genome/genome_state.json` |
| Active anomalies | `01_operational_health/anomalies.json` |
| Active escalations | `01_operational_health/escalations.json` |
| Halt & skip history | `01_operational_health/halt_audit.json` |
"""

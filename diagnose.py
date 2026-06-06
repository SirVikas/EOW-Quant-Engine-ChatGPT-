"""
EOW Quant Engine — Advanced Forensic Diagnostic Report v2.0
Run: python diagnose.py
Paste the output to Claude for analysis.

Sections:
  1.  Engine Status
  2.  PnL Summary
  3.  Exit Type Breakdown + Session Analysis
  4.  CT-Scan Internal Health
  5.  Profit Guard
  6.  Risk State
  7.  Last Skip / Gate Rejection
  8.  Error Registry
  9.  Live Deployment Scorecard
  10. Strategy Usage
  11. WebSocket Health
  12. Last 10 Trades Detail
  13. SIGNAL FLOW FORENSICS  ← new
  14. RSI GOVERNOR STATE      ← new
  15. CONTEXT MEMORY (TOXIC) ← new
  16. REGIME SNAPSHOT         ← new
  17. TRUTH ENGINE (ETE/AAP) ← new
  18. PIPELINE BREAK FORENSICS← new
  19. ECONOMIC TRUTH          ← new
  20. SIGNAL FILTER STATE     ← new
"""
import json, urllib.request, urllib.error, datetime, sys
from collections import Counter

BASE = "http://localhost:8000"

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=6) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}

def hr(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def kv(label, value, warn=None):
    flag = ""
    if warn and value is not None:
        try:
            flag = " ⚠" if warn(value) else " ✓"
        except: pass
    print(f"  {label:<35} {value}{flag}")

def safe_float(v, default=0.0):
    try: return float(v)
    except: return default

print(f"\n{'#'*60}")
print(f"  EOW QUANT ENGINE — FORENSIC DIAGNOSTIC REPORT v2.0")
print(f"  Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
print(f"{'#'*60}")

# ── 1. ENGINE STATUS ────────────────────────────────────────
hr("1. ENGINE STATUS")
s = get("/api/status")
if "_error" in s:
    print(f"  ❌ Engine not reachable: {s['_error']}")
    print("  → Make sure engine is running: python run.py")
    sys.exit(1)

kv("Mode",           s.get("mode"))
kv("WS Status",      s.get("ws_status"), warn=lambda v: "CONNECTED" not in str(v))
kv("Capital",        f"${s.get('capital', 0):.2f}")
kv("Open Positions", s.get("open_positions"))
kv("Total Trades",   s.get("total_trades"), warn=lambda v: v == 0)
kv("Symbols Watched",s.get("symbols_watched"), warn=lambda v: v < 10)
kv("Halted",         s.get("halted"), warn=lambda v: v is True)
kv("Drawdown %",     f"{s.get('drawdown_pct', 0):.2f}%", warn=lambda v: float(v.strip('%')) > 10)
kv("Loss Streak",    s.get("streak"))

ver = get("/api/version")
kv("Engine Version", ver.get("version") or ver.get("app_version") or str(ver))

# ── 2. PnL SUMMARY ──────────────────────────────────────────
hr("2. PnL SUMMARY")
p = get("/api/pnl")
kv("Net PnL",        f"${p.get('total_net_pnl', 0):.4f}", warn=lambda v: float(v.strip('$')) < 0)
_wr_raw = p.get('win_rate', 0) or 0
_wr_pct = _wr_raw if _wr_raw > 1 else _wr_raw * 100
kv("Win Rate",       f"{_wr_pct:.1f}%", warn=lambda v: float(v.strip('%')) < 45)
kv("Profit Factor",  f"{p.get('profit_factor', 0):.2f}", warn=lambda v: float(v) < 1.0)
kv("Avg Win",        f"${p.get('avg_win_usdt', 0):.4f}")
kv("Avg Loss",       f"${p.get('avg_loss_usdt', 0):.4f}")
kv("Max Drawdown",   f"{p.get('max_drawdown_pct', 0):.2f}%", warn=lambda v: float(v.strip('%')) > 15)
kv("Sharpe Ratio",   f"{p.get('sharpe_ratio', 0):.2f}", warn=lambda v: float(v) < 0.5)
kv("Total Fees Paid",f"${p.get('total_fees_paid', 0):.4f}")
kv("Total Trades",   p.get("n_trades"))

# ── 3. EXIT TYPE BREAKDOWN ──────────────────────────────────
hr("3. EXIT TYPE BREAKDOWN")
trades = get("/api/trades")
if isinstance(trades, list) and trades:
    exits = Counter(t.get("exit_reason") or t.get("exit_method") or "UNKNOWN" for t in trades)
    total = len(trades)
    for k, v in exits.most_common(15):
        pct = v / total * 100
        print(f"  {k:<40} {v:>5} trades  ({pct:.1f}%)")

    print()
    sessions = {}
    for t in trades:
        sess = t.get("origin_session") or t.get("session") or "UNKNOWN"
        if sess not in sessions:
            sessions[sess] = {"pnl": 0, "fee": 0, "count": 0, "wins": 0}
        _net = t.get("net_pnl") or t.get("pnl") or 0
        _fee = (t.get("fee_entry") or 0) + (t.get("fee_exit") or 0)
        if _fee == 0: _fee = t.get("fee") or 0
        sessions[sess]["count"] += 1
        sessions[sess]["pnl"]   += _net
        sessions[sess]["fee"]   += _fee
        if _net > 0:
            sessions[sess]["wins"] += 1

    print(f"  {'SESSION':<12} {'TRADES':>7} {'WIN%':>7} {'PnL':>10} {'FEE':>10} {'FDR':>8}")
    print(f"  {'-'*58}")
    for sess, d in sorted(sessions.items()):
        fdr  = d["fee"] / abs(d["pnl"]) if d["pnl"] else 999
        wr   = d["wins"] / d["count"] * 100 if d["count"] else 0
        flag = " ⚠" if fdr > 5 else ""
        print(f"  {sess:<12} {d['count']:>7} {wr:>6.1f}% {d['pnl']:>10.4f} {d['fee']:>10.4f} {fdr:>7.1f}x{flag}")

    avg_win  = p.get("avg_win_usdt", 0) or 0
    avg_loss = p.get("avg_loss_usdt", 0) or 0
    n_trades = p.get("n_trades") or p.get("total_trades") or len(trades)
    total_fee= p.get("total_fees_paid", 0) or 0
    fee_per_trade = total_fee / n_trades if n_trades else 0
    print()
    print(f"  FEE DRAG ANALYSIS:")
    print(f"  {'Avg Win':<30} ${avg_win:.4f}")
    print(f"  {'Avg Loss':<30} ${avg_loss:.4f}")
    print(f"  {'Fee per trade':<30} ${fee_per_trade:.4f}" + (" ⚠ fee >= avg win!" if fee_per_trade >= abs(avg_win) and avg_win > 0 else ""))
    rr = abs(avg_win / avg_loss) if avg_loss else 0
    print(f"  {'Practical R:R':<30} {rr:.2f}" + (" ⚠ need > 0.5" if rr < 0.5 else ""))
    durations = [(t.get("duration_sec") or t.get("hold_seconds") or 0) for t in trades if t.get("duration_sec") or t.get("hold_seconds")]
    if durations:
        avg_dur = sum(durations)/len(durations)
        print(f"  {'Avg trade duration':<30} {avg_dur:.0f}s ({avg_dur/60:.1f}min)" + (" ⚠ too short" if avg_dur < 180 else ""))
else:
    print("  No trades yet — waiting for first trade")

# ── 4. CT-SCAN ───────────────────────────────────────────────
hr("4. CT-SCAN — INTERNAL HEALTH")
ct = get("/api/ct-scan")
kv("Health",  ct.get("system_health"), warn=lambda v: v != "HEALTHY")
kv("Score",   ct.get("score"), warn=lambda v: v < 80)
for i in ct.get("issues", []):
    print(f"  ⚠ {i}")
if not ct.get("issues"):
    print("  No issues detected ✓")

# ── 5. PROFIT GUARD ─────────────────────────────────────────
hr("5. PROFIT GUARD")
pg = get("/api/profit-guard")
kv("PF Guard Active",       pg.get("pf_guard_active"), warn=lambda v: v is True)
kv("Profit Factor",         f"{pg.get('profit_factor', 0):.2f}")
kv("Max Consecutive Losses",pg.get("max_consecutive_losses"))
kv("Frequency Multiplier",  pg.get("frequency_multiplier"))

# ── 6. RISK STATE ───────────────────────────────────────────
hr("6. RISK STATE")
rs = get("/api/risk-state")
if "_error" not in rs:
    kv("Daily Risk Used",  f"{rs.get('daily_risk_used_pct', 0):.2f}%")
    kv("Daily Risk Cap",   f"{rs.get('daily_risk_cap_pct', 0):.2f}%")
    kv("Safe Mode",        rs.get("safe_mode"), warn=lambda v: v is True)

# ── 7. LAST SKIP / GATE REJECTION ───────────────────────────
hr("7. LAST SKIP / GATE REJECTION")
sk = get("/api/last-skip")
skip = sk.get("last_skip", {})
if skip:
    for k, v in skip.items():
        print(f"  {k}: {v}")
    print(f"  Total skips: {sk.get('skip_total', 0)}")
else:
    print("  No skips recorded yet")

# No-Trade Reason Breakdown (session totals)
sr = get("/api/skip-reasons")
if "_error" not in sr:
    reasons = sr.get("top_rejection_reasons") or {}
    total_s = sr.get("total_skips", 0)
    mins_idle = sr.get("minutes_since_last_trade", 0)
    rej_rate  = sr.get("rejection_rate_pct", 0)
    if reasons:
        reason_total = sum(reasons.values())
        print(f"\n  NO-TRADE REASON BREAKDOWN (session — top gates):")
        print(f"  {'Gate / Reason':<40} {'Count':>6}  {'Share':>6}")
        print(f"  {'-'*56}")
        for gate, cnt in sorted(reasons.items(), key=lambda x: -x[1]):
            share = (cnt / reason_total * 100) if reason_total else 0
            warn  = " ⚠" if cnt == max(reasons.values()) else ""
            print(f"  {gate:<40} {cnt:>6}  {share:>5.1f}%{warn}")
        print(f"  Session skip total: {reason_total}  |  Rejection rate: {rej_rate:.1f}%  |  Mins since trade: {mins_idle:.0f}")
    else:
        print(f"  No-Trade log: no skips recorded yet this session")

# ── 8. ERROR REGISTRY ───────────────────────────────────────
hr("8. ERROR REGISTRY")
err = get("/api/errors")
kv("Total Errors",  err.get("total_errors"), warn=lambda v: v > 0)
kv("Health Penalty",err.get("health_penalty"))
for e in err.get("recent_5", []):
    print(f"    → {e}")

# ── 9. LIVE DEPLOYMENT SCORECARD ────────────────────────────
hr("9. LIVE DEPLOYMENT SCORECARD")
sc = get("/api/scorecard")
kv("Overall Pass",  sc.get("overall_pass"), warn=lambda v: v is False)
if sc.get("summary"):
    print(f"  Summary: {sc['summary']}")
failed = [i for i in sc.get("items", []) if not i.get("passed")]
if failed:
    print("  Failed checks:")
    for i in failed:
        print(f"    ✗ {i['name']}: {i.get('note','')}")

# ── 10. STRATEGY USAGE ──────────────────────────────────────
hr("10. STRATEGY USAGE")
su = get("/api/strategy-usage")
if isinstance(su, dict):
    print(f"  total_trades (current session): {su.get('total_trades', 0)}")
    fractions = su.get("usage_fractions") or {}
    if isinstance(fractions, dict) and any(v > 0 for v in fractions.values()):
        for strat, frac in fractions.items():
            print(f"  {strat:<30} {frac*100:.1f}%")
    else:
        for strat, pct in (su.get("strategy_usage") or {}).items():
            print(f"  {strat:<30} {pct}")
    print(f"  active_strategies: {su.get('active_strategies', [])}")
    if su.get("warning"):
        print(f"  ⚠ {su['warning']}")

# ── 11. WEBSOCKET HEALTH ────────────────────────────────────
hr("11. WEBSOCKET HEALTH")
ws = get("/api/ws-truth")
kv("State",              ws.get("state"), warn=lambda v: "CONNECTED" not in str(v))
kv("Gap Seconds",        ws.get("gap_seconds"), warn=lambda v: v and float(v) > 30)
kv("Reconnect Attempts", ws.get("reconnect_attempts"), warn=lambda v: v and int(v) > 3)

# ── 12. LAST 10 TRADES DETAIL ───────────────────────────────
hr("12. LAST 10 TRADES — DETAIL")
if isinstance(trades, list) and trades:
    last10 = trades[:10]
    hdr = f"  {'#':<3} {'SYM':<10} {'SIDE':<5} {'QTY':>8} {'ENTRY':>10} {'EXIT':>10} {'SL':>10} {'TP':>10} {'NET_PNL':>9} {'FEE':>7} {'R':>6} {'PEAK_R':>7} {'EXIT_REASON':<35} {'SESSION'}"
    print(hdr)
    print(f"  {'-'*len(hdr)}")
    for i, t in enumerate(last10, 1):
        sym    = t.get("symbol", "?")[:9]
        side   = t.get("side", "?")[:4]
        net_pnl= t.get("net_pnl") or t.get("pnl") or 0
        fee    = (t.get("fee_entry") or 0) + (t.get("fee_exit") or 0)
        if fee == 0: fee = t.get("fee") or 0
        reason = (t.get("exit_reason") or t.get("exit_method") or "?")[:34]
        sess   = t.get("origin_session") or t.get("session") or "?"
        flag   = " ✓" if net_pnl > 0 else " ✗"
        print(f"  {i:<3} {sym:<10} {side:<5} {t.get('qty',0):>8.4f} {t.get('entry_price',0):>10.4f} {t.get('exit_price',0):>10.4f} {t.get('stop_loss',0):>10.4f} {t.get('take_profit',0):>10.4f} {net_pnl:>9.4f} {fee:>7.4f} {t.get('r_multiple',0) or 0:>6.3f} {t.get('peak_r',0) or 0:>7.3f} {reason:<35} {sess}{flag}")
else:
    print("  No trades yet")

# ═══════════════════════════════════════════════════════════
# FORENSIC LAYER — new sections below
# ═══════════════════════════════════════════════════════════

# ── 13. SIGNAL FLOW FORENSICS ───────────────────────────────
hr("13. SIGNAL FLOW FORENSICS (PRP-002 Ecology)")
ec = get("/api/prp/002/ecology")
if "_error" not in ec:
    kv("Total Evaluated",     ec.get("total_evaluated"))
    kv("Total Approved",      ec.get("total_approved"), warn=lambda v: v == 0)
    kv("RSI Blocked",         ec.get("rsi_blocked") or ec.get("total_rsi_blocked"), warn=lambda v: v and v > 0)
    kv("Context Blocked",     ec.get("context_blocked") or ec.get("total_ctx_blocked"), warn=lambda v: v and v > 0)
    kv("Recovery Trades",     ec.get("recovery_trades") or ec.get("total_recovery_trades"))
    sr = ec.get("survival_rate") or ec.get("overall_survival_rate")
    if sr is not None:
        kv("Survival Rate",   f"{safe_float(sr)*100:.1f}%", warn=lambda v: float(v.strip('%')) < 5)
    den = get("/api/prp/002/density")
    if "_error" not in den:
        kv("Signals/hr",      den.get("signals_per_hr"))
        kv("Is Starvation",   den.get("is_starvation"), warn=lambda v: v is True)
        kv("Drought Seconds", den.get("drought_seconds"), warn=lambda v: v and float(v) > 300)
else:
    print(f"  {ec.get('_error', 'unavailable')}")

# ── 14. RSI GOVERNOR STATE ──────────────────────────────────
hr("14. RSI GOVERNOR STATE (AdaptiveRSIGovernor)")
rg = get("/api/prp/002/rsi-governor")
if "_error" not in rg:
    bands = rg.get("bands") or rg.get("current_bands") or {}
    if isinstance(bands, dict):
        for regime_name, band_vals in bands.items():
            if isinstance(band_vals, dict):
                lo  = band_vals.get("long_rsi",  band_vals.get("lo", "?"))
                hi  = band_vals.get("short_rsi", band_vals.get("hi", "?"))
                sr_ = band_vals.get("survival_rate", "?")
                print(f"  {regime_name:<20} LONG≤{lo}  SHORT≥{hi}  survival={sr_}")
            else:
                print(f"  {regime_name}: {band_vals}")
    kv("Total Evaluated", rg.get("total_evaluated"))
    kv("Total Passed",    rg.get("total_passed"),
       warn=lambda v: v == 0)
    adapt_log = rg.get("adapt_log") or rg.get("recent_adaptations") or []
    if adapt_log:
        print("  Recent band adaptations:")
        for a in adapt_log[-3:]:
            print(f"    → {a}")
    # Recent RSI decisions
    dec = get("/api/prp/002/rsi-decisions")
    if "_error" not in dec:
        decisions = dec if isinstance(dec, list) else dec.get("decisions", dec.get("recent", []))
        if isinstance(decisions, list) and decisions:
            print(f"  Last 5 RSI decisions:")
            for d in decisions[-5:]:
                sym_    = d.get("symbol", "?")
                regime_ = d.get("regime", "?")
                rsi_    = d.get("rsi", "?")
                side_   = d.get("side") or "NONE"
                blocked_= "BLOCKED" if d.get("blocked") else "PASS"
                reason_ = (d.get("reason", "") or "")[:50]
                print(f"    {sym_:<10} {regime_:<15} rsi={rsi_:<6} → {side_:<5} {blocked_:<8} {reason_}")
else:
    print(f"  {rg.get('_error', 'unavailable')}")

# ── 15. CONTEXT MEMORY (TOXIC CONTEXTS) ─────────────────────
hr("15. CONTEXT MEMORY — TOXIC / PROFITABLE")
cm = get("/api/prp/002/context-memory")
if "_error" not in cm:
    contexts = cm if isinstance(cm, list) else cm.get("contexts", cm.get("records", []))
    if isinstance(contexts, list):
        toxic   = [c for c in contexts if str(c.get("context_type","")).upper() == "TOXIC"]
        profit  = [c for c in contexts if str(c.get("context_type","")).upper() == "PROFITABLE"]
        print(f"  Total contexts tracked: {len(contexts)}")
        print(f"  TOXIC:      {len(toxic)}")
        print(f"  PROFITABLE: {len(profit)}")
        if toxic:
            print("  Toxic contexts (blocking trades):")
            for c in toxic[:10]:
                key = c.get("context_key") or f"{c.get('regime','?')}|{c.get('strategy','?')}"
                wr_ = c.get("win_rate") or c.get("wr", "?")
                n_  = c.get("n") or c.get("count", "?")
                print(f"    ⚠ {key}  WR={wr_}  n={n_}")
        if profit:
            print("  Profitable contexts (signal amplifiers):")
            for c in profit[:5]:
                key = c.get("context_key") or f"{c.get('regime','?')}|{c.get('strategy','?')}"
                wr_ = c.get("win_rate") or c.get("wr", "?")
                n_  = c.get("n") or c.get("count", "?")
                print(f"    ✓ {key}  WR={wr_}  n={n_}")
    else:
        print(f"  {cm}")
else:
    print(f"  {cm.get('_error', 'unavailable')}")

# ── 16. REGIME SNAPSHOT ─────────────────────────────────────
hr("16. REGIME SNAPSHOT (current per-symbol)")
reg = get("/api/regime")
if "_error" not in reg:
    regimes_data = reg if isinstance(reg, dict) else {}
    symbols_reg  = regimes_data.get("symbols") or regimes_data.get("regimes") or regimes_data
    if isinstance(symbols_reg, dict):
        trending = [k for k,v in symbols_reg.items() if "TREND" in str(v).upper()]
        mr       = [k for k,v in symbols_reg.items() if "MEAN" in str(v).upper() or "REVERT" in str(v).upper()]
        comp     = [k for k,v in symbols_reg.items() if "COMPRESS" in str(v).upper()]
        other    = [k for k,v in symbols_reg.items() if k not in trending+mr+comp]
        print(f"  TRENDING ({len(trending)}):        {', '.join(trending[:8])}")
        print(f"  MEAN_REVERTING ({len(mr)}):  {', '.join(mr[:8])}")
        print(f"  COMPRESSION ({len(comp)}):    {', '.join(comp[:8])}")
        if other:
            print(f"  OTHER ({len(other)}):           {', '.join(other[:8])}")
    elif isinstance(symbols_reg, list):
        for r in symbols_reg[:20]:
            print(f"  {r}")
    else:
        summary_ = reg.get("summary") or reg.get("regime_summary") or ""
        if summary_:
            print(f"  {summary_}")
        else:
            print(f"  (regime data format: {list(reg.keys())[:5]})")
else:
    print(f"  {reg.get('_error', 'unavailable')}")

# ── 17. TRUTH ENGINE (ETE/AAP) ──────────────────────────────
hr("17. TRUTH ENGINE — ETE / AAP")
ete = get("/api/truth/ete-status")
if "_error" not in ete:
    kv("ETE Gate Enabled",   ete.get("gate_enabled"), warn=lambda v: v is True)
    kv("Observation Mode",   ete.get("observation_mode"))
    kv("Min Score (future)", ete.get("min_score"))
    kv("Scores Evaluated",   ete.get("total_evaluated") or ete.get("evaluations"))
else:
    print(f"  ETE: {ete.get('_error', 'unavailable')}")

am = get("/api/truth/alpha-matrix")
if "_error" not in am and am:
    sources   = am.get("top_alpha_sources", [])
    destroyers= am.get("top_destroyers", [])
    buckets   = am.get("score_vs_expectancy", [])
    if sources:
        print("  Top Alpha Sources (components scoring ≥70 in winning trades):")
        for s_ in sources[:5]:
            print(f"    ✓ {s_.get('component','?'):<15} wins={s_.get('win_count',0)}  avg_score={s_.get('avg_score',0):.1f}")
    if destroyers:
        print("  Top Alpha Destroyers (components scoring <40 in losing trades):")
        for d_ in destroyers[:5]:
            print(f"    ⚠ {d_.get('component','?'):<15} losses={d_.get('loss_count',0)}  avg_score={d_.get('avg_score',0):.1f}")
    if buckets:
        print("  Score vs Expectancy:")
        print(f"  {'Score Bucket':<15} {'Trades':>7} {'Avg PnL':>10} {'Win%':>7}")
        for b in buckets:
            print(f"  {str(b.get('score_bucket','?')):<15} {b.get('trade_count',0):>7} {b.get('avg_pnl',0):>10.4f} {b.get('win_rate',0)*100:>6.1f}%")
else:
    print("  Alpha matrix: no data yet (accumulates after first trades)")

# ── 18. PIPELINE BREAK FORENSICS ────────────────────────────
hr("18. PIPELINE BREAK FORENSICS")
pb = get("/api/diagnostics/pipeline-break-forensics")
if "_error" not in pb:
    breaks = pb.get("breaks") or pb.get("pipeline_breaks") or []
    if isinstance(breaks, list) and breaks:
        print(f"  Total breaks detected: {len(breaks)}")
        for b in breaks[:5]:
            print(f"    → {b}")
    else:
        summary_ = pb.get("summary") or pb.get("status") or ""
        if summary_:
            print(f"  {summary_}")
        else:
            print("  No pipeline breaks detected ✓")
    # Also check signal filter
    sf = get("/api/signal-filter")
    if "_error" not in sf:
        kv("Signal Filter State", sf.get("state") or sf.get("status"))
        for k_, v_ in sf.items():
            if k_ not in ("state","status","_error") and v_:
                print(f"  {k_}: {v_}")
else:
    print(f"  {pb.get('_error', 'unavailable')}")

# ── 19. ECONOMIC TRUTH ──────────────────────────────────────
hr("19. ECONOMIC TRUTH — EXPECTANCY")
et = get("/api/economic-truth/expectancy")
if "_error" not in et:
    kv("Expectancy ($/trade)", f"${et.get('expectancy_per_trade', et.get('expectancy', 0)):.4f}",
       warn=lambda v: float(v.strip('$')) < 0)
    kv("Edge Score",           et.get("edge_score") or et.get("alpha_score"))
    kv("Fee Drag %",           et.get("fee_drag_pct") or et.get("fee_burden_pct"),
       warn=lambda v: v and float(str(v).strip('%')) > 25)
    kv("Breakeven WR",         et.get("breakeven_win_rate") or et.get("breakeven_wr"))
    regime_exp = et.get("regime_expectancy") or et.get("by_regime") or {}
    if isinstance(regime_exp, dict) and regime_exp:
        print("  Expectancy by regime:")
        for reg_name, exp_val in regime_exp.items():
            flag_ = " ⚠" if safe_float(exp_val) < 0 else " ✓"
            print(f"    {reg_name:<20} ${safe_float(exp_val):.4f}{flag_}")
else:
    et2 = get("/api/economic-truth/alpha")
    if "_error" not in et2:
        for k_, v_ in et2.items():
            if k_ != "_error":
                print(f"  {k_}: {v_}")
    else:
        print(f"  {et.get('_error', 'unavailable')}")

# ── 20. SIGNAL FILTER STATE ─────────────────────────────────
hr("20. AUTONOMOUS INTELLIGENCE / SELF-CORRECTION")
ai = get("/api/auto-intelligence/state")
if "_error" not in ai:
    kv("AI State",   ai.get("state") or ai.get("status"))
    kv("Enabled",    ai.get("enabled"))
    kv("Last Run",   ai.get("last_run") or ai.get("last_run_ts"))
else:
    sc2 = get("/api/self-correction/state")
    if "_error" not in sc2:
        kv("Self-Correction",  sc2.get("state") or sc2.get("status"))
        kv("Enabled",          sc2.get("enabled"))
        last_ = sc2.get("last_change") or {}
        if last_:
            print(f"  Last change: {last_}")
    else:
        print("  (unavailable)")

# ── DONE ────────────────────────────────────────────────────
print(f"\n{'#'*60}")
print(f"  END OF FORENSIC REPORT — Paste this to Claude")
print(f"{'#'*60}\n")

"""
EOW Quant Engine — Advanced Forensic Diagnostic Report v3.0
Run: python diagnose.py
Paste the output to Claude for analysis.

Sections:
  1.  Engine Status
  2.  PnL Summary
  3.  Exit Type Breakdown + Session Analysis
  4.  CT-Scan Internal Health
  5.  Profit Guard
  6.  Risk State
  7.  No-Trade Reason Breakdown (all gates, grouped by family)
  8.  Error Registry
  9.  Live Deployment Scorecard
  10. Strategy Usage
  11. WebSocket Health
  12. Last 10 Trades Detail
  13. Signal Flow Forensics
  14. RSI Governor State
  15. Context Memory (Toxic)
  16. Regime Snapshot
  17. Truth Engine (ETE/AAP)
  18. Pipeline Break Forensics
  19. Economic Truth
  20. Autonomous Intelligence
  21. RL Engine State
  22. Session Health Summary
"""
import json, urllib.request, urllib.error, datetime, sys, socket
from collections import Counter

# Windows: when stdout is redirected to a file (python diagnose.py > report.txt)
# Python falls back to the ANSI codepage (cp1252), which cannot encode the
# emoji used in the report (🟢/✓/⚠) and crashes with UnicodeEncodeError.
# Force UTF-8 with replacement so the report always completes.
for _stream in (sys.stdout, sys.stderr):
    try:
        if (_stream.encoding or "").lower() not in ("utf-8", "utf8", "cp65001"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = "http://localhost:8000"

# ── HTTP helpers ─────────────────────────────────────────────────────────────

def get(path, timeout=6):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}

def get_fast(path):
    """10-second timeout for reporting endpoints (heavy computation, not latency-sensitive)."""
    return get(path, timeout=10)

def hr(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def kv(label, value, warn=None):
    flag = ""
    if warn and value is not None:
        try:
            flag = " ⚠" if warn(value) else " ✓"
        except Exception:
            pass
    print(f"  {label:<35} {value}{flag}")

def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

# ── Gate family classifier ────────────────────────────────────────────────────

_GATE_FAMILIES = {
    "RSI": ["RSI_BLOCKED", "RSI_FAIL", "RSI_FILTER", "RSI_GOVERNOR", "RSI"],
    "RL":  ["RL_TOXIC", "ECO_TOXIC", "RL_BLOCK", "CONTEXT_TOXIC", "RL_EXPLORE",
            "EXPLORATION", "BANDIT"],
    "QUALITY": ["WEAK_EDGE", "ADAPTIVE_LOW_SCORE", "CONFIDENCE_DECAY",
                "SIGNAL_FILTER", "LOW_CONF", "QUALITY"],
    "FEE":  ["FEE_BLOCKED", "FEE_REJECT", "SMART_FEE", "FEE"],
    "RISK": ["ZERO_QTY", "HALT", "MDD", "DAILY_RISK", "RISK", "DRAWDOWN"],
    "RL_ENGINE": ["RL_ENGINE", "RL_QUALITY"],
    "SIZING": ["SIZING", "NOTIONAL_CAP"],
    "ECO":  ["ECO_BLOCKED", "ECOLOGY", "DENSITY", "STARVATION"],
    "AIE":  ["AIE_CALIBRATE", "AIE_BLOCK", "AIE"],
    "LEAN": ["LEAN_GATE", "LEAN"],
    "PROFIT_GUARD": ["PROFIT_GUARD", "PF_GUARD", "PF_BLOCK"],
}

def classify_gate(gate_key: str) -> str:
    g = gate_key.upper()
    for family, keywords in _GATE_FAMILIES.items():
        if any(g.startswith(kw) or kw in g for kw in keywords):
            return family
    return "OTHER"

# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'#'*60}")
print(f"  EOW QUANT ENGINE — FORENSIC DIAGNOSTIC REPORT v3.0")
print(f"  Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
print(f"{'#'*60}")

# ── 1. ENGINE STATUS ─────────────────────────────────────────────────────────
hr("1. ENGINE STATUS")
s = get("/api/status")
if "_error" in s:
    print(f"  ❌ Engine not reachable: {s['_error']}")
    print("  → Make sure engine is running: python run.py")
    sys.exit(1)

kv("Mode",           s.get("mode"))
# ⚠ on BYPASS is intentional: calibration mode must not become permanent
# (PHX-CALIBRATION-PHASE-001 Phase-3 requires returning to GATED)
kv("Gate Mode",      s.get("gate_mode"), warn=lambda v: v == "BYPASS")
kv("WS Status",      s.get("ws_status"),
   warn=lambda v: "CONNECTED" not in str(v) and "LIVE" not in str(v))
kv("Capital",        f"${s.get('capital', 0):.2f}")
kv("Open Positions", s.get("open_positions"))
kv("Total Trades",   s.get("total_trades"), warn=lambda v: v == 0)
kv("Symbols Watched",s.get("symbols_watched"), warn=lambda v: v < 10)
kv("Halted",         s.get("halted"), warn=lambda v: v is True)
kv("Drawdown %",     f"{s.get('drawdown_pct', 0):.2f}%",
   warn=lambda v: safe_float(v.strip('%')) > 10)
kv("Loss Streak",    s.get("streak"))

ver = get("/api/version")
kv("Engine Version", ver.get("version") or ver.get("app_version") or str(ver))

# ── 2. PnL SUMMARY ───────────────────────────────────────────────────────────
hr("2. PnL SUMMARY")
p  = get("/api/pnl")
su = get("/api/strategy-usage")   # has session_stats via total_trades current session

# All-time stats (includes BYPASS era — reference only)
print("  [ALL-TIME — includes pre-BYPASS era trades]")
kv("Net PnL",        f"${p.get('total_net_pnl', 0):.4f}",
   warn=lambda v: safe_float(v.strip('$')) < 0)
_wr_raw = p.get('win_rate', 0) or 0
_wr_pct = _wr_raw if _wr_raw > 1 else _wr_raw * 100
kv("Win Rate",       f"{_wr_pct:.1f}%",
   warn=lambda v: safe_float(v.strip('%')) < 45)
kv("Profit Factor",  f"{p.get('profit_factor', 0):.2f}",
   warn=lambda v: safe_float(v) < 1.0)
kv("Avg Win",        f"${p.get('avg_win_usdt', 0):.4f}")
kv("Avg Loss",       f"${p.get('avg_loss_usdt', 0):.4f}")
kv("Max Drawdown",   f"{p.get('max_drawdown_pct', 0):.2f}%",
   warn=lambda v: safe_float(v.strip('%')) > 15)
kv("Sharpe Ratio",   f"{p.get('sharpe_ratio', 0):.2f}",
   warn=lambda v: safe_float(v) < 0.5)
kv("Total Fees Paid",f"${p.get('total_fees_paid', 0):.4f}")
kv("Total Trades",   p.get("n_trades"))

# Current session stats (since last restart — meaningful signal of current behavior)
_sess_trades = su.get("total_trades", 0) if isinstance(su, dict) else 0
print(f"\n  [CURRENT SESSION — since last restart]")
kv("Session Trades", _sess_trades, warn=lambda v: v == 0)

# ── 3. EXIT TYPE BREAKDOWN ───────────────────────────────────────────────────
hr("3. EXIT TYPE BREAKDOWN")
trades = get("/api/trades")
if isinstance(trades, list) and trades:
    exits = Counter(t.get("exit_reason") or t.get("exit_method") or "UNKNOWN"
                    for t in trades)
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
        if _fee == 0:
            _fee = t.get("fee") or 0
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
        print(f"  {sess:<12} {d['count']:>7} {wr:>6.1f}% {d['pnl']:>10.4f} "
              f"{d['fee']:>10.4f} {fdr:>7.1f}x{flag}")

    avg_win   = p.get("avg_win_usdt", 0) or 0
    avg_loss  = p.get("avg_loss_usdt", 0) or 0
    n_trades  = p.get("n_trades") or p.get("total_trades") or len(trades)
    total_fee = p.get("total_fees_paid", 0) or 0
    fee_per_trade = total_fee / n_trades if n_trades else 0
    print()
    print(f"  FEE DRAG ANALYSIS:")
    print(f"  {'Avg Win':<30} ${avg_win:.4f}")
    print(f"  {'Avg Loss':<30} ${avg_loss:.4f}")
    fee_warn = " ⚠ fee >= avg win!" if fee_per_trade >= abs(avg_win) and avg_win > 0 else ""
    print(f"  {'Fee per trade':<30} ${fee_per_trade:.4f}{fee_warn}")
    rr = abs(avg_win / avg_loss) if avg_loss else 0
    rr_warn = " ⚠ need > 0.5" if rr < 0.5 else ""
    print(f"  {'Practical R:R':<30} {rr:.2f}{rr_warn}")
    durations = [(t.get("duration_sec") or t.get("hold_seconds") or 0)
                 for t in trades
                 if t.get("duration_sec") or t.get("hold_seconds")]
    if durations:
        avg_dur = sum(durations) / len(durations)
        dur_warn = " ⚠ too short" if avg_dur < 180 else ""
        print(f"  {'Avg trade duration':<30} {avg_dur:.0f}s ({avg_dur/60:.1f}min){dur_warn}")
else:
    print("  No trades yet — waiting for first trade")

# ── 4. CT-SCAN ────────────────────────────────────────────────────────────────
hr("4. CT-SCAN — INTERNAL HEALTH")
ct = get("/api/ct-scan")
kv("Health",  ct.get("system_health"), warn=lambda v: v != "HEALTHY")
kv("Score",   ct.get("score"), warn=lambda v: v < 80)
for i in ct.get("issues", []):
    print(f"  ⚠ {i}")
if not ct.get("issues"):
    print("  No issues detected ✓")

# ── 5. PROFIT GUARD ──────────────────────────────────────────────────────────
hr("5. PROFIT GUARD")
pg = get("/api/profit-guard")
kv("PF Guard Active",       pg.get("pf_guard_active"), warn=lambda v: v is True)
kv("Profit Factor",         f"{pg.get('profit_factor', 0):.2f}")
kv("Max Consecutive Losses",pg.get("max_consecutive_losses"))
kv("Frequency Multiplier",  pg.get("frequency_multiplier"))

# ── 6. RISK STATE ─────────────────────────────────────────────────────────────
hr("6. RISK STATE")
rs = get("/api/risk-state")
if "_error" not in rs:
    kv("Daily Risk Used",  f"{rs.get('daily_risk_used_pct', 0):.2f}%")
    kv("Daily Risk Cap",   f"{rs.get('daily_risk_cap_pct', 0):.2f}%")
    kv("Safe Mode",        rs.get("safe_mode"), warn=lambda v: v is True)
else:
    print(f"  {rs.get('_error', 'unavailable')}")

# ── 7. NO-TRADE REASON BREAKDOWN ─────────────────────────────────────────────
hr("7. NO-TRADE REASON BREAKDOWN (all gates, by family)")
sk = get("/api/last-skip")
skip = sk.get("last_skip", {})
if skip:
    print("  Last skip:")
    for k, v in skip.items():
        print(f"    {k}: {v}")
    print(f"  (session skip total: {sk.get('skip_total', 0)})")
else:
    print("  No skips recorded yet")

sr = get("/api/skip-reasons")
if "_error" not in sr:
    reasons = sr.get("all_rejection_reasons") or sr.get("top_rejection_reasons") or {}
    total_s   = sr.get("total_skips", 0)
    mins_idle = sr.get("minutes_since_last_trade", 0)
    rej_rate  = sr.get("rejection_rate_pct", 0)

    if reasons:
        reason_total = sum(reasons.values())

        # Group by family
        families: dict[str, list[tuple[str, int]]] = {}
        for gate, cnt in sorted(reasons.items(), key=lambda x: -x[1]):
            fam = classify_gate(gate)
            families.setdefault(fam, []).append((gate, cnt))

        print(f"\n  ALL SKIP REASONS — grouped by gate family (session total: {reason_total})")
        print(f"  Rejection rate: {rej_rate:.1f}%  |  Mins since last trade: {mins_idle:.0f}")
        print()

        for fam in sorted(families.keys()):
            fam_total = sum(c for _, c in families[fam])
            fam_share = fam_total / reason_total * 100 if reason_total else 0
            is_top    = fam_total == max(sum(c for _, c in v) for v in families.values())
            fam_warn  = " ⚠ DOMINANT" if is_top else ""
            print(f"  [{fam}] — {fam_total} skips ({fam_share:.1f}%){fam_warn}")
            for gate, cnt in families[fam]:
                share = cnt / reason_total * 100 if reason_total else 0
                print(f"    {gate:<42} {cnt:>5}  {share:>5.1f}%")
    else:
        print(f"\n  No-Trade log: no skips recorded yet this session")
else:
    print(f"  {sr.get('_error', 'unavailable')}")

# ── 8. ERROR REGISTRY ────────────────────────────────────────────────────────
hr("8. ERROR REGISTRY")
err = get("/api/errors")
kv("Total Errors",  err.get("total_errors"), warn=lambda v: v > 0)
kv("Health Penalty",err.get("health_penalty"))
for e in err.get("recent_5", []):
    print(f"    → {e}")

# ── 9. LIVE DEPLOYMENT SCORECARD ─────────────────────────────────────────────
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

# ── 10. STRATEGY USAGE ───────────────────────────────────────────────────────
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

# ── 11. WEBSOCKET HEALTH ──────────────────────────────────────────────────────
hr("11. WEBSOCKET HEALTH")
ws = get("/api/ws-truth")
kv("State",              ws.get("state"), warn=lambda v: "CONNECTED" not in str(v))
kv("Gap Seconds",        ws.get("gap_seconds"), warn=lambda v: v and safe_float(v) > 30)
kv("Reconnect Attempts", ws.get("reconnect_attempts"),
   warn=lambda v: v and int(v) > 3)

# ── 12. LAST 10 TRADES DETAIL ────────────────────────────────────────────────
hr("12. LAST 10 TRADES — DETAIL")
if isinstance(trades, list) and trades:
    last10 = trades[:10]
    hdr = (f"  {'#':<3} {'SYM':<10} {'SIDE':<5} {'QTY':>8} {'ENTRY':>10} "
           f"{'EXIT':>10} {'SL':>10} {'TP':>10} {'NET_PNL':>9} {'FEE':>7} "
           f"{'R':>6} {'PEAK_R':>7} {'EXIT_REASON':<35} SESSION")
    print(hdr)
    print(f"  {'-'*len(hdr)}")
    for i, t in enumerate(last10, 1):
        sym    = t.get("symbol", "?")[:9]
        side   = t.get("side", "?")[:4]
        net_pnl= t.get("net_pnl") or t.get("pnl") or 0
        fee    = (t.get("fee_entry") or 0) + (t.get("fee_exit") or 0)
        if fee == 0:
            fee = t.get("fee") or 0
        reason = (t.get("exit_reason") or t.get("exit_method") or "?")[:34]
        sess   = t.get("origin_session") or t.get("session") or "?"
        flag   = " ✓" if net_pnl > 0 else " ✗"
        print(f"  {i:<3} {sym:<10} {side:<5} {t.get('qty',0):>8.4f} "
              f"{t.get('entry_price',0):>10.4f} {t.get('exit_price',0):>10.4f} "
              f"{t.get('stop_loss',0):>10.4f} {t.get('take_profit',0):>10.4f} "
              f"{net_pnl:>9.4f} {fee:>7.4f} "
              f"{t.get('r_multiple',0) or 0:>6.3f} {t.get('peak_r',0) or 0:>7.3f} "
              f"{reason:<35} {sess}{flag}")
else:
    print("  No trades yet")

# ═══════════════════════════════════════════════════════════════════════════════
# FORENSIC LAYER
# ═══════════════════════════════════════════════════════════════════════════════

# ── 13. SIGNAL FLOW FORENSICS ────────────────────────────────────────────────
hr("13. SIGNAL FLOW FORENSICS (PRP-002 Ecology)")
ec = get("/api/prp/002/ecology")
if "_error" not in ec:
    total_eval = ec.get("total_evaluated") or 0
    total_appr = ec.get("total_approved") or 0
    appr_pct   = (total_appr / total_eval * 100) if total_eval else 0
    kv("Total Evaluated",  total_eval)
    kv("Total Approved",   f"{total_appr}  ({appr_pct:.1f}%)",
       warn=lambda v: int(v.split()[0]) == 0)
    kv("RSI Blocked",      ec.get("rsi_blocked"), warn=lambda v: v and v > 0)
    kv("Context Blocked",  ec.get("context_blocked"), warn=lambda v: v and v > 0)
    kv("Recovery Trades",  ec.get("recovery_trades"))
    # Survival rate — ecology telemetry has no top-level survival_rate; skip if missing
    sr_val = ec.get("survival_rate") or ec.get("overall_survival_rate")
    if sr_val is not None:
        kv("Survival Rate",  f"{safe_float(sr_val)*100:.1f}%",
           warn=lambda v: safe_float(v.strip('%')) < 5)
    den = get("/api/prp/002/density")
    if "_error" not in den:
        kv("Signals/hr",     den.get("signals_per_hr"))
        kv("Is Starvation",  den.get("is_starvation"), warn=lambda v: v is True)
        kv("Drought Seconds",den.get("drought_seconds"),
           warn=lambda v: v and safe_float(v) > 300)
else:
    print(f"  {ec.get('_error', 'unavailable')}")

# ── 14. RSI GOVERNOR STATE ───────────────────────────────────────────────────
hr("14. RSI GOVERNOR STATE (AdaptiveRSIGovernor)")
rg = get("/api/prp/002/rsi-governor")
if "_error" not in rg:
    bands = rg.get("bands") or rg.get("current_bands") or {}
    surv_by_regime = rg.get("survival_by_regime") or {}
    if isinstance(bands, dict):
        for regime_name, band_vals in bands.items():
            if isinstance(band_vals, dict):
                lo   = band_vals.get("long_rsi",  band_vals.get("lo", "?"))
                hi   = band_vals.get("short_rsi", band_vals.get("hi", "?"))
                surv = surv_by_regime.get(regime_name, band_vals.get("survival_rate", "?"))
                # window n distinguishes "all blocked" (n>0, surv=0) from
                # "regime never evaluated" (n=0, surv=0)
                n_ev = (rg.get("window_evals") or {}).get(regime_name)
                surv_txt = f"{surv}" if n_ev is None else f"{surv} (window n={n_ev})"
                if regime_name in ("TRENDING", "UNKNOWN"):
                    # Unified band: both LONG and SHORT use long_rsi threshold
                    print(f"  {regime_name:<20} BOTH≤{lo:<6}  (unified band)  survival={surv_txt}")
                else:
                    print(f"  {regime_name:<20} LONG≤{lo:<6}  SHORT≥{hi:<6}  survival={surv_txt}")
            else:
                print(f"  {regime_name}: {band_vals}")
    kv("Total Evaluated", rg.get("total_evaluated"))
    kv("Total Passed",    rg.get("total_passed"), warn=lambda v: v == 0)
    adapt_log = rg.get("adapt_log") or rg.get("recent_adaptations") or []
    if adapt_log:
        print("  Recent band adaptations:")
        for a in adapt_log[-3:]:
            print(f"    → {a}")
    # Recent RSI decisions — show full reason text, no truncation
    dec = get("/api/prp/002/rsi-decisions")
    if "_error" not in dec:
        decisions = (dec if isinstance(dec, list)
                     else dec.get("decisions", dec.get("recent", [])))
        if isinstance(decisions, list) and decisions:
            print(f"  Last 5 RSI decisions:")
            for d in decisions[-5:]:
                sym_     = d.get("symbol", "?")
                regime_  = d.get("regime", "?")
                rsi_     = d.get("rsi", "?")
                side_    = d.get("side") or "NONE"
                blocked_ = "BLOCKED" if d.get("blocked") else "PASS"
                reason_  = d.get("reason") or ""    # full reason, no truncation
                print(f"    {sym_:<10} {regime_:<15} rsi={rsi_:<6} → "
                      f"{side_:<5} {blocked_:<8} {reason_}")
else:
    print(f"  {rg.get('_error', 'unavailable')}")

# ── 15. CONTEXT MEMORY (TOXIC CONTEXTS) ──────────────────────────────────────
hr("15. CONTEXT MEMORY — TOXIC / PROFITABLE")
cm = get("/api/prp/002/context-memory")
if "_error" not in cm:
    # API returns a flat telemetry dict — keys are total_contexts, profitable_count,
    # toxic_count, top_profitable.  Previous code looked for "contexts"/"records" keys
    # that don't exist, so it always printed 0.
    total_ctx  = cm.get("total_contexts", 0)
    n_profit   = cm.get("profitable_count", 0)
    n_toxic    = cm.get("toxic_count", 0)
    top_profit = cm.get("top_profitable", [])
    lookup_ct  = cm.get("lookup_count", 0)
    boost_ct   = cm.get("boost_count", 0)
    block_ct   = cm.get("block_count", 0)
    print(f"  Total contexts tracked: {total_ctx}")
    print(f"  TOXIC:      {n_toxic}")
    print(f"  PROFITABLE: {n_profit}  (need ≥5 trades + avg_pnl > 0)")
    print(f"  Lookups: {lookup_ct}  Boosts applied: {boost_ct}  Blocks applied: {block_ct}")
    if n_toxic == 0 and n_profit == 0 and total_ctx == 0:
        print("  ⚠ No context history — verify startup backfill ran and SAVE_INTERVAL is short enough")
    if top_profit:
        print("  Top profitable contexts (signal amplifiers):")
        for c in top_profit[:5]:
            key    = c.get("context_key", "?")
            wr_    = c.get("win_rate", "?")
            n_     = c.get("n_trades", "?")
            avg_p  = c.get("avg_pnl", "?")
            print(f"    ✓ {key}  WR={wr_}  n={n_}  avg_pnl={avg_p}")
else:
    print(f"  {cm.get('_error', 'unavailable')}")

# ── 16. REGIME SNAPSHOT ──────────────────────────────────────────────────────
hr("16. REGIME SNAPSHOT (current per-symbol)")
reg = get("/api/regime")
if "_error" not in reg:
    regimes_data = reg if isinstance(reg, dict) else {}
    symbols_reg  = (regimes_data.get("symbols")
                    or regimes_data.get("regimes")
                    or regimes_data)
    if isinstance(symbols_reg, dict):
        trending = [k for k, v in symbols_reg.items() if "TREND"    in str(v).upper()]
        mr       = [k for k, v in symbols_reg.items() if "MEAN"     in str(v).upper()
                                                      or "REVERT"   in str(v).upper()]
        comp     = [k for k, v in symbols_reg.items() if "COMPRESS" in str(v).upper()]
        other    = [k for k, v in symbols_reg.items() if k not in trending + mr + comp]
        # Show ALL symbols per regime — no cap
        print(f"  TRENDING ({len(trending)}):")
        for chunk in [trending[i:i+10] for i in range(0, len(trending), 10)]:
            print(f"    {', '.join(chunk)}")
        print(f"  MEAN_REVERTING ({len(mr)}):")
        for chunk in [mr[i:i+10] for i in range(0, len(mr), 10)]:
            print(f"    {', '.join(chunk)}")
        print(f"  COMPRESSION ({len(comp)}):")
        for chunk in [comp[i:i+10] for i in range(0, len(comp), 10)]:
            print(f"    {', '.join(chunk)}")
        if other:
            print(f"  OTHER ({len(other)}):")
            for chunk in [other[i:i+10] for i in range(0, len(other), 10)]:
                print(f"    {', '.join(chunk)}")
    elif isinstance(symbols_reg, list):
        for r in symbols_reg[:30]:
            print(f"  {r}")
    else:
        summary_ = reg.get("summary") or reg.get("regime_summary") or ""
        if summary_:
            print(f"  {summary_}")
        else:
            print(f"  (regime data format: {list(reg.keys())[:5]})")
else:
    print(f"  {reg.get('_error', 'unavailable')}")

# ── 17. TRUTH ENGINE (ETE/AAP) ───────────────────────────────────────────────
hr("17. TRUTH ENGINE — ETE / AAP")
ete = get("/api/truth/ete-status")
if "_error" not in ete:
    kv("ETE Gate Enabled",   ete.get("gate_enabled"), warn=lambda v: v is True)
    kv("Observation Mode",   ete.get("observation_mode"))
    kv("Min Score (future)", ete.get("min_score"))
    # explicit None-check: "0 or fallback" turned a legitimate 0 into None
    _sess_eval = ete.get("total_evaluated")
    if _sess_eval is None:
        _sess_eval = ete.get("evaluations")
    kv("Scores Evaluated (session)", _sess_eval)
    # Phase-2 calibration progress — cumulative archive count, survives restarts
    n_arch = ete.get("archive_samples")
    if n_arch is not None:
        tgt = ete.get("calibration_target", 500)
        kv("ETE Samples (cumulative)",
           f"{n_arch} / {tgt}  ({min(100.0, n_arch / tgt * 100):.1f}%)",
           warn=lambda v: n_arch < tgt)
else:
    print(f"  ETE: {ete.get('_error', 'unavailable')}")

am = get("/api/truth/alpha-matrix")
if "_error" not in am and am:
    sources    = am.get("top_alpha_sources", [])
    destroyers = am.get("top_destroyers", [])
    buckets    = am.get("score_vs_expectancy", [])
    if sources:
        print("  Top Alpha Sources (components scoring ≥70 in winning trades):")
        for s_ in sources[:5]:
            print(f"    ✓ {s_.get('component','?'):<15} "
                  f"wins={s_.get('win_count',0)}  avg_score={s_.get('avg_score',0):.1f}")
    if destroyers:
        print("  Top Alpha Destroyers (components scoring <40 in losing trades):")
        for d_ in destroyers[:5]:
            print(f"    ⚠ {d_.get('component','?'):<15} "
                  f"losses={d_.get('loss_count',0)}  avg_score={d_.get('avg_score',0):.1f}")
    if buckets:
        print("  Score vs Expectancy:")
        print(f"  {'Score Bucket':<15} {'Trades':>7} {'Avg PnL':>10} {'Win%':>7}")
        for b in buckets:
            print(f"  {str(b.get('score_bucket','?')):<15} {b.get('trade_count',0):>7} "
                  f"{b.get('avg_pnl',0):>10.4f} {b.get('win_rate',0)*100:>6.1f}%")
else:
    print("  Alpha matrix: no data yet (accumulates after first trades)")

# Phase-2 Truth Calibration — decile breakdown + ETE_MIN_SCORE threshold sweep.
# The sweep answers the Phase-2 question directly: "what would expectancy be
# if only trades scoring ≥ T had been taken?" (cumulative from above).
cal = get("/api/truth/calibration")
if "_error" not in cal and cal.get("total_trades", 0) > 0:
    deciles = cal.get("calibration", [])
    print(f"\n  PHASE-2 CALIBRATION — decile detail ({cal['total_trades']} archived trades):")
    print(f"  {'Decile':<10} {'Trades':>7} {'Avg PnL':>10} {'Win%':>7}")
    for d_ in deciles:
        if d_.get("trade_count", 0) > 0:
            print(f"  {d_.get('decile','?'):<10} {d_.get('trade_count',0):>7} "
                  f"{d_.get('avg_pnl',0):>10.4f} {d_.get('win_rate',0)*100:>6.1f}%")
    print(f"\n  ETE_MIN_SCORE THRESHOLD SWEEP (expectancy if only score ≥ T taken):")
    print(f"  {'T':>4} {'Kept':>6} {'Kept%':>7} {'Exp $/trade':>12} {'Win%':>7}")
    total_n = sum(d_.get("trade_count", 0) for d_ in deciles)
    for t_ in range(0, 100, 10):
        kept = [d_ for d_ in deciles
                if int(d_["decile"].split("-")[0]) >= t_ and d_.get("trade_count", 0) > 0]
        n_ = sum(d_["trade_count"] for d_ in kept)
        if n_ == 0:
            continue
        exp_ = sum(d_["avg_pnl"] * d_["trade_count"] for d_ in kept) / n_
        wr_  = sum(d_["win_rate"] * d_["trade_count"] for d_ in kept) / n_
        flag = " ✓" if exp_ > 0 else ""
        print(f"  {t_:>4} {n_:>6} {n_/total_n*100:>6.1f}% {exp_:>12.4f} {wr_*100:>6.1f}%{flag}")

# ── 18. PIPELINE BREAK FORENSICS ─────────────────────────────────────────────
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
    sf = get("/api/signal-filter")
    if "_error" not in sf:
        kv("Signal Filter State", sf.get("state") or sf.get("status"))
        for k_, v_ in sf.items():
            if k_ not in ("state", "status", "_error") and v_:
                print(f"  {k_}: {v_}")
else:
    print(f"  {pb.get('_error', 'unavailable')}")

# ── 19. ECONOMIC TRUTH ───────────────────────────────────────────────────────
hr("19. ECONOMIC TRUTH — EXPECTANCY")
et = get_fast("/api/economic-truth/expectancy")
if "_error" not in et:
    # Keys must match compute_expectancy_reconstruction() output — the previous
    # names (expectancy_per_trade, edge_score, ...) never existed in the API
    # response, so this section printed $0.0000/None regardless of real data.
    _net_exp   = et.get("overall_net_expectancy")
    _gross_exp = et.get("overall_gross_expectancy")
    kv("Expectancy ($/trade)",
       f"${_net_exp:.4f}" if _net_exp is not None else "n/a (no trades)",
       warn=lambda v: safe_float(str(v).strip('$')) < 0)
    kv("Gross Expectancy",
       f"${_gross_exp:.4f}" if _gross_exp is not None else "n/a")
    kv("Survivability", et.get("survivability_verdict"),
       warn=lambda v: str(v) in ("NOT_VIABLE", "FEE_COLLAPSED", "ERROR"))
    _fee_adj = (((et.get("decomposition") or {}).get("fee_adjusted") or {})
                .get("OVERALL") or {})
    _fdr = _fee_adj.get("fee_destruction_ratio")
    if isinstance(_fdr, (int, float)):
        kv("Fee Destruction Ratio", f"{_fdr:.1%}",
           warn=lambda v: safe_float(str(v).strip('%')) > 25)
    kv("Survivable Regions", et.get("survivable_region_count"))
    _trend = (et.get("expectancy_decay") or {}).get("trend")
    if _trend:
        kv("Expectancy Trend", _trend, warn=lambda v: v == "DEGRADING")
    _regime_decomp = (et.get("decomposition") or {}).get("regime") or {}
    if isinstance(_regime_decomp, dict) and _regime_decomp:
        print("  Expectancy by regime:")
        for reg_name, reg_stats in _regime_decomp.items():
            _re = (reg_stats or {}).get("net_expectancy")
            if _re is None:
                continue
            flag_ = " ⚠" if _re < 0 else " ✓"
            print(f"    {reg_name:<20} ${_re:.4f}{flag_}")
else:
    et2 = get_fast("/api/economic-truth/alpha")
    if "_error" not in et2:
        for k_, v_ in et2.items():
            if k_ != "_error":
                print(f"  {k_}: {v_}")
    else:
        print(f"  {et.get('_error', 'unavailable')} (3s timeout)")

# ── 20. AUTONOMOUS INTELLIGENCE ──────────────────────────────────────────────
hr("20. AUTONOMOUS INTELLIGENCE / SELF-CORRECTION")
ai = get_fast("/api/auto-intelligence/state")
if "_error" not in ai:
    kv("AI State",  ai.get("state") or ai.get("status"))
    kv("Enabled",   ai.get("enabled"))
    kv("Last Run",  ai.get("last_run") or ai.get("last_run_ts"))
else:
    sc2 = get_fast("/api/self-correction/state")
    if "_error" not in sc2:
        kv("Self-Correction",  sc2.get("state") or sc2.get("status"))
        kv("Enabled",          sc2.get("enabled"))
        last_ = sc2.get("last_change") or {}
        if last_:
            print(f"  Last change: {last_}")
    else:
        print("  (unavailable — 3s timeout)")

# ── 21. RL ENGINE STATE ───────────────────────────────────────────────────────
hr("21. RL ENGINE STATE (Contextual Bandit)")
rl = get_fast("/api/learning-intelligence/rl")
if "_error" not in rl:
    kv("Brain Status",       rl.get("brain_status"),
       warn=lambda v: v in ("COLLAPSED", "NEGATIVE_CONVERGENCE", "IDLE"))
    kv("Convergence State",  rl.get("convergence_state"),
       warn=lambda v: v == "DIVERGING")
    kv("Intelligence Score", f"{safe_float(rl.get('intelligence_score', 0)):.3f}",
       warn=lambda v: safe_float(v) < 0.3)
    kv("Avg Q-Value",        f"{safe_float(rl.get('avg_q', 0)):.4f}",
       warn=lambda v: safe_float(v) < -0.2)
    kv("Explore Ratio",      f"{safe_float(rl.get('explore_ratio', 1)):.2f}",
       warn=lambda v: safe_float(v) > 0.7)
    kv("Exploit Ratio",      f"{safe_float(rl.get('exploit_ratio', 0)):.2f}")
    kv("Toxic Contexts",     rl.get("toxic_count"),
       warn=lambda v: v and v > 5)
    kv("Total Contexts",     rl.get("total_contexts"))

    counters = rl.get("counters") or {}
    kv("Total Pulls (trades)", counters.get("total_pulls") or rl.get("session_trades"))

    qd = rl.get("quality_distribution") or {}
    if qd:
        print("  Q-value distribution:")
        for bucket, cnt in qd.items():
            if isinstance(cnt, (int, float)) and cnt > 0:
                print(f"    {bucket:<20} {cnt}")

    # Spot-check toxic context keys (first 5)
    ctx_map = rl.get("live_context_map") or {}
    toxic_ctxs = [(k, v) for k, v in ctx_map.items() if safe_float(v.get("q", 0)) < -0.1]
    if toxic_ctxs:
        print(f"  Toxic context keys ({len(toxic_ctxs)} total, showing first 5):")
        for k, v in sorted(toxic_ctxs, key=lambda x: x[1].get("q", 0))[:5]:
            print(f"    ⚠ {k:<40} q={v.get('q'):.4f}  n={v.get('visits')}  "
                  f"wr={v.get('wr')}%  pnl={v.get('pnl'):.4f}")
    elif ctx_map:
        print(f"  All {len(ctx_map)} tracked contexts have q≥-0.1 ✓")
else:
    print(f"  {rl.get('_error', 'unavailable')} (3s timeout)")

# ── 22. SESSION HEALTH SUMMARY ───────────────────────────────────────────────
hr("22. SESSION HEALTH SUMMARY")

_health: list[tuple[str, str, str]] = []  # (subsystem, verdict, detail)

# Engine
_mode = s.get("mode", "?")
_dd   = safe_float(s.get("drawdown_pct", 0))
_health.append(("Engine",   "OK" if not s.get("halted") else "HALTED",
                 f"mode={_mode} dd={_dd:.1f}%"))

# WS
_ws_state = s.get("ws_status", "?")
_ws_ok    = "CONNECTED" in str(_ws_state) or "LIVE" in str(_ws_state)
_health.append(("WebSocket", "OK" if _ws_ok else "WARN", str(_ws_state)[:40]))

# Scaler / Capital
_cap = safe_float(s.get("capital", 0))
_health.append(("Capital", "OK" if _cap > 0 else "WARN", f"${_cap:.2f}"))

# Trades flowing
_n_trades = safe_float(s.get("total_trades", 0))
_health.append(("Trades", "NONE" if _n_trades == 0 else "OK",
                 f"{int(_n_trades)} total"))

# Win rate
_pf = safe_float(p.get("profit_factor", 0))
_wr_disp = f"{_wr_pct:.1f}%"
_health.append(("Edge (PF/WR)",
                 "WARN" if _pf < 1.0 and _n_trades > 10 else "OK",
                 f"PF={_pf:.2f}  WR={_wr_disp}"))

# RL brain
if "_error" not in rl:
    _bs = rl.get("brain_status", "UNKNOWN")
    _tox = rl.get("toxic_count", 0) or 0
    _health.append(("RL Brain",
                     "WARN" if _bs in ("COLLAPSED", "NEGATIVE_CONVERGENCE", "IDLE")
                     else "OK",
                     f"status={_bs}  toxic_ctxs={_tox}"))
else:
    _health.append(("RL Brain", "TIMEOUT", "3s timeout — endpoint slow"))

# RSI Governor
if "_error" not in rg:
    _tot_pass = rg.get("total_passed") or 0
    _health.append(("RSI Governor",
                     "WARN" if _tot_pass == 0 else "OK",
                     f"passed={_tot_pass} / evaluated={rg.get('total_evaluated',0)}"))
else:
    _health.append(("RSI Governor", "UNAVAIL", str(rg.get("_error", "?"))))

# Signal ecology
if "_error" not in ec:
    _eco_appr = ec.get("total_approved") or 0
    _health.append(("Ecology",
                     "WARN" if _eco_appr == 0 else "OK",
                     f"approved={_eco_appr} / evaluated={ec.get('total_evaluated',0)}"))
else:
    _health.append(("Ecology", "UNAVAIL", str(ec.get("_error", "?"))))

# Skip reasons — dominant blocker
if "_error" not in sr and reasons:
    _dom_gate, _dom_cnt = max(reasons.items(), key=lambda x: x[1])
    _dom_pct = _dom_cnt / sum(reasons.values()) * 100 if reasons else 0
    _health.append(("Top Blocker",
                     "WARN" if _dom_pct > 50 else "OK",
                     f"{_dom_gate}  {_dom_cnt} ({_dom_pct:.0f}% of skips)"))

# Print summary table
print(f"  {'SUBSYSTEM':<20} {'VERDICT':<10} DETAIL")
print(f"  {'-'*60}")
icons = {"OK": "✓", "WARN": "⚠", "HALTED": "⛔", "NONE": "○",
         "TIMEOUT": "⏱", "UNAVAIL": "?"}
for subsys, verdict, detail in _health:
    icon = icons.get(verdict, "?")
    print(f"  {subsys:<20} {icon} {verdict:<8} {detail}")

# Overall verdict
warn_count = sum(1 for _, v, _ in _health if v in ("WARN", "HALTED"))
none_count = sum(1 for _, v, _ in _health if v == "NONE")
print()
if warn_count == 0 and none_count == 0:
    print("  ✓ ALL SYSTEMS NOMINAL — engine ready to trade")
elif none_count > 0 and warn_count == 0:
    print("  ○ WAITING FOR FIRST TRADE — all systems nominal, no trades yet")
else:
    print(f"  ⚠ {warn_count} SUBSYSTEM(S) NEED ATTENTION — see warnings above")

# ── DONE ─────────────────────────────────────────────────────────────────────
print(f"\n{'#'*60}")
print(f"  END OF FORENSIC REPORT v3.0 — Paste this to Claude")
print(f"{'#'*60}\n")

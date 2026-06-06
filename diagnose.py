"""
EOW Quant Engine — One-Click Diagnostic Report
Run: python diagnose.py
Paste the output to Claude for analysis.
"""
import json, urllib.request, urllib.error, datetime, sys
from collections import Counter

BASE = "http://localhost:8000"

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=5) as r:
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

print(f"\n{'#'*60}")
print(f"  EOW QUANT ENGINE — DIAGNOSTIC REPORT")
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
_wr_pct = _wr_raw if _wr_raw > 1 else _wr_raw * 100   # API may return 33.3 or 0.333
kv("Win Rate",       f"{_wr_pct:.1f}%", warn=lambda v: float(v.strip('%')) < 45)
kv("Profit Factor",  f"{p.get('profit_factor', 0):.2f}", warn=lambda v: float(v) < 1.0)
kv("Avg Win",        f"${p.get('avg_win_usdt', 0):.4f}")
kv("Avg Loss",       f"${p.get('avg_loss_usdt', 0):.4f}")
kv("Max Drawdown",   f"{p.get('max_drawdown_pct', 0):.2f}%", warn=lambda v: float(v.strip('%')) > 15)
kv("Sharpe Ratio",   f"{p.get('sharpe_ratio', 0):.2f}", warn=lambda v: float(v) < 0.5)
kv("Total Fees Paid",f"${p.get('total_fees_paid', 0):.4f}")
kv("Total Trades",   p.get("n_trades"))

# ── 3. EXIT TYPE BREAKDOWN ──────────────────────────────────
hr("3. EXIT TYPE BREAKDOWN  (v1.50.2 key fix area)")
trades = get("/api/trades")
if isinstance(trades, list) and trades:
    exits = Counter(t.get("exit_reason") or t.get("exit_method") or "UNKNOWN" for t in trades)
    total = len(trades)
    for k, v in exits.most_common():
        pct = v / total * 100
        flag = " ⚠" if k == "FAST_FAIL" and pct > 10 else ""
        flag = " ⚠" if k == "TIME_EXIT" and pct > 30 else flag
        print(f"  {k:<30} {v:>5} trades  ({pct:.1f}%){flag}")

    # Session breakdown
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

    # Fee vs Win analysis
    avg_win  = p.get("avg_win_usdt", 0) or 0
    avg_loss = p.get("avg_loss_usdt", 0) or 0
    # Use authoritative total-trade count from PnL stats; len(trades) is capped
    # at the /api/trades limit (200) and would inflate fee-per-trade by ~24×.
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
    # Duration stats
    durations = [(t.get("duration_sec") or t.get("hold_seconds") or 0) for t in trades if t.get("duration_sec") or t.get("hold_seconds")]
    if durations:
        avg_dur = sum(durations)/len(durations)
        print(f"  {'Avg trade duration':<30} {avg_dur:.0f}s ({avg_dur/60:.1f}min)" + (" ⚠ too short" if avg_dur < 180 else ""))
else:
    print("  No trades yet — waiting for first trade")

# ── 4. CT-SCAN (internal health) ────────────────────────────
hr("4. CT-SCAN — INTERNAL HEALTH")
ct = get("/api/ct-scan")
kv("Health",  ct.get("system_health"), warn=lambda v: v != "HEALTHY")
kv("Score",   ct.get("score"), warn=lambda v: v < 80)
issues = ct.get("issues", [])
if issues:
    for i in issues:
        print(f"  ⚠ {i}")
else:
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

# ── 7. LAST SKIP REASON ─────────────────────────────────────
hr("7. LAST SKIP / GATE REJECTION")
sk = get("/api/last-skip")
skip = sk.get("last_skip", {})
if skip:
    for k, v in skip.items():
        print(f"  {k}: {v}")
    print(f"  Total skips: {sk.get('skip_total', 0)}")
else:
    print("  No skips recorded yet")

# ── 8. ERRORS ───────────────────────────────────────────────
hr("8. ERROR REGISTRY")
err = get("/api/errors")
kv("Total Errors",  err.get("total_errors"), warn=lambda v: v > 0)
kv("Health Penalty",err.get("health_penalty"))
recent = err.get("recent_5", [])
if recent:
    print("  Recent errors:")
    for e in recent:
        print(f"    → {e}")

# ── 9. SCORECARD ────────────────────────────────────────────
hr("9. LIVE DEPLOYMENT SCORECARD")
sc = get("/api/scorecard")
kv("Overall Pass",  sc.get("overall_pass"), warn=lambda v: v is False)
summary = sc.get("summary", "")
if summary:
    print(f"  Summary: {summary}")
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
        usage_strs = su.get("strategy_usage") or {}
        if isinstance(usage_strs, dict):
            for strat, pct in usage_strs.items():
                print(f"  {strat:<30} {pct}")
        else:
            print(f"  (no usage data)")
    active = su.get("active_strategies", [])
    print(f"  active_strategies: {active}")
    warn = su.get("warning", "")
    if warn:
        print(f"  ⚠ {warn}")
elif isinstance(su, list):
    for item in su:
        print(f"  {item}")
else:
    print(f"  {su}")

# ── 11. WS TRUTH ────────────────────────────────────────────
hr("11. WEBSOCKET HEALTH")
ws = get("/api/ws-truth")
kv("State",              ws.get("state"), warn=lambda v: "CONNECTED" not in str(v))
kv("Gap Seconds",        ws.get("gap_seconds"), warn=lambda v: v and float(v) > 30)
kv("Reconnect Attempts", ws.get("reconnect_attempts"), warn=lambda v: v and int(v) > 3)

# ── 12. LAST 10 TRADES DETAIL ───────────────────────────────
hr("12. LAST 10 TRADES — DETAIL")
if isinstance(trades, list) and trades:
    # API returns newest-first; take first 10 = most recent trades
    last10 = trades[:10]
    hdr = f"  {'#':<3} {'SYM':<10} {'SIDE':<5} {'QTY':>8} {'ENTRY':>10} {'EXIT':>10} {'SL':>10} {'TP':>10} {'NET_PNL':>9} {'FEE':>7} {'R':>6} {'PEAK_R':>7} {'EXIT_REASON':<35} {'SESSION'}"
    print(hdr)
    print(f"  {'-'*len(hdr)}")
    for i, t in enumerate(last10, 1):
        sym      = t.get("symbol", "?")[:9]
        side     = t.get("side", "?")[:4]
        qty      = t.get("qty", 0)
        entry    = t.get("entry_price", 0)
        exit_p   = t.get("exit_price", 0)
        sl       = t.get("stop_loss", 0)
        tp       = t.get("take_profit", 0)
        net_pnl  = t.get("net_pnl") or t.get("pnl") or 0
        fee      = (t.get("fee_entry") or 0) + (t.get("fee_exit") or 0)
        if fee == 0: fee = t.get("fee") or 0
        r        = t.get("r_multiple", 0) or 0
        peak_r   = t.get("peak_r", 0) or 0
        reason   = (t.get("exit_reason") or t.get("exit_method") or "?")[:34]
        sess     = t.get("origin_session") or t.get("session") or "?"
        flag     = " ✓" if net_pnl > 0 else " ✗"
        print(f"  {i:<3} {sym:<10} {side:<5} {qty:>8.4f} {entry:>10.4f} {exit_p:>10.4f} {sl:>10.4f} {tp:>10.4f} {net_pnl:>9.4f} {fee:>7.4f} {r:>6.3f} {peak_r:>7.3f} {reason:<35} {sess}{flag}")
else:
    print("  No trades yet")

# ── DONE ────────────────────────────────────────────────────
print(f"\n{'#'*60}")
print(f"  END OF REPORT — Paste this to Claude for analysis")
print(f"{'#'*60}\n")

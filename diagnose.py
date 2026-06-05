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
print(f"  Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
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
kv("Win Rate",       f"{p.get('win_rate', 0)*100:.1f}%", warn=lambda v: float(v.strip('%')) < 45)
kv("Profit Factor",  f"{p.get('profit_factor', 0):.2f}", warn=lambda v: float(v) < 1.0)
kv("Avg Win",        f"${p.get('avg_win_usdt', 0):.4f}")
kv("Avg Loss",       f"${p.get('avg_loss_usdt', 0):.4f}")
kv("Max Drawdown",   f"{p.get('max_drawdown_pct', 0):.2f}%", warn=lambda v: float(v.strip('%')) > 15)
kv("Sharpe Ratio",   f"{p.get('sharpe_ratio', 0):.2f}", warn=lambda v: float(v) < 0.5)
kv("Total Fees Paid",f"${p.get('total_fees_paid', 0):.4f}")
kv("Total Trades",   p.get("n_trades"))

# ── 3. EXIT TYPE BREAKDOWN ──────────────────────────────────
hr("3. EXIT TYPE BREAKDOWN  (v1.50.1 key fix area)")
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
        sess = t.get("session", "UNKNOWN")
        if sess not in sessions:
            sessions[sess] = {"pnl": 0, "fee": 0, "count": 0, "wins": 0}
        sessions[sess]["count"] += 1
        sessions[sess]["pnl"]   += t.get("pnl", 0) or 0
        sessions[sess]["fee"]   += t.get("fee", 0) or 0
        if (t.get("pnl") or 0) > 0:
            sessions[sess]["wins"] += 1

    print(f"  {'SESSION':<12} {'TRADES':>7} {'WIN%':>7} {'PnL':>10} {'FEE':>10} {'FDR':>8}")
    print(f"  {'-'*58}")
    for sess, d in sorted(sessions.items()):
        fdr  = d["fee"] / abs(d["pnl"]) if d["pnl"] else 999
        wr   = d["wins"] / d["count"] * 100 if d["count"] else 0
        flag = " ⚠" if fdr > 5 else ""
        print(f"  {sess:<12} {d['count']:>7} {wr:>6.1f}% {d['pnl']:>10.4f} {d['fee']:>10.4f} {fdr:>7.1f}x{flag}")
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
    for strat, data in su.items():
        if isinstance(data, dict):
            count = data.get("count", data.get("trades", 0))
            wr    = data.get("win_rate", 0)
            pnl   = data.get("pnl", data.get("net_pnl", 0))
            print(f"  {strat:<30} trades={count}  WR={wr*100:.1f}%  PnL={pnl:.4f}")
        else:
            print(f"  {strat}: {data}")
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

# ── DONE ────────────────────────────────────────────────────
print(f"\n{'#'*60}")
print(f"  END OF REPORT — Paste this to Claude for analysis")
print(f"{'#'*60}\n")

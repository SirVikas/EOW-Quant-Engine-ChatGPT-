"""
Standalone Recovery Cycle Audit
Run from the project root: python run_cycle_audit.py
Works WITHOUT restarting the engine — reads from the same pnl_calc instance
via the live API if engine is running, OR from the data_lake if not.
"""
import json, sys, urllib.request, urllib.error

PORT = 8000

def via_api():
    url = f"http://127.0.0.1:{PORT}/api/forensics/recovery-cycle-audit"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None   # endpoint not on this branch yet
        raise
    except Exception:
        return None

def via_trades_api():
    """Fall back to existing /api/trades endpoint."""
    url = f"http://127.0.0.1:{PORT}/api/trades?limit=2000"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as exc:
        print(f"Cannot reach engine at port {PORT}: {exc}")
        return None

def analyse_trades(trades):
    import collections
    if not trades:
        print("No trades found.")
        return

    trades_s = sorted(trades, key=lambda t: t.get("exit_ts", 0))

    # 1. Consecutive runs
    runs = []
    run_type = run_len = None
    for t in trades_s:
        cur = "WIN" if t.get("net_pnl", 0) > 0 else "LOSS"
        if cur == run_type:
            run_len += 1
        else:
            if run_type: runs.append({"type": run_type, "len": run_len})
            run_type, run_len = cur, 1
    if run_type: runs.append({"type": run_type, "len": run_len})

    win_runs  = [r["len"] for r in runs if r["type"] == "WIN"]
    loss_runs = [r["len"] for r in runs if r["type"] == "LOSS"]
    avg_win   = round(sum(win_runs)  / max(len(win_runs),  1), 1)
    avg_loss  = round(sum(loss_runs) / max(len(loss_runs), 1), 1)
    loss_dist = collections.Counter(loss_runs)

    # 2. R-multiple distribution
    r_buckets = collections.defaultdict(list)
    for t in trades_s:
        r = t.get("r_multiple", 0.0) or 0.0
        ep = t.get("entry_price", 0); sl = t.get("stop_loss", 0); ex = t.get("exit_price", 0)
        if r == 0 and ep and sl and ex:   # recompute if missing
            risk = abs(ep - sl)
            r = (ex - ep) / risk if ep > sl else (ep - ex) / risk if ep < sl else 0
        if   r > 1.5:  r_buckets["win_1.5+"].append(r)
        elif r > 1.0:  r_buckets["win_1.0-1.5"].append(r)
        elif r > 0.5:  r_buckets["win_0.5-1.0"].append(r)
        elif r > 0:    r_buckets["win_0.0-0.5"].append(r)
        else:          r_buckets["loss"].append(r)

    unprotected = sum(len(r_buckets[k]) for k in ["win_0.0-0.5","win_0.5-1.0","win_1.0-1.5"])
    total_wins  = unprotected + len(r_buckets["win_1.5+"])
    pct_unprot  = round(unprotected / max(total_wins, 1) * 100, 1)

    # 3. Recovery vs Normal
    def _is_rec(t):
        eo = t.get("exploration_origin") or {}
        if eo.get("was_exploration_trade"): return True
        ds = t.get("decision_snapshot") or {}
        em = (ds.get("ecology") or {}).get("size_multiplier")
        return em is not None and em < 1.0

    rec   = [t for t in trades_s if _is_rec(t)]
    norm  = [t for t in trades_s if not _is_rec(t)]
    def _m(lst):
        n = len(lst); pnls = [t.get("net_pnl",0) for t in lst]
        w = sum(1 for p in pnls if p > 0)
        return {"n": n, "wr": round(w/max(n,1)*100,1), "avg_pnl": round(sum(pnls)/max(n,1),4)}

    # 4. Context boost
    def _bm(t):
        ds = t.get("decision_snapshot") or {}
        v = (ds.get("ctx_amp") or {}).get("boost_mult") or (ds.get("ecology") or {}).get("boost_mult")
        return float(v) if v else 1.0
    boosted  = [t for t in trades_s if _bm(t) > 1.0]
    nboosted = [t for t in trades_s if _bm(t) <= 1.0]

    # ── PRINT ────────────────────────────────────────────────────────────────
    sep = "─" * 60
    print(f"\n{'═'*60}")
    print(f"  RECOVERY CYCLE AUDIT  (trades analysed: {len(trades_s)})")
    print(f"{'═'*60}\n")

    print(f"SECTION 1 — CONSECUTIVE WIN/LOSS RUNS")
    print(sep)
    print(f"  Avg win  run length : {avg_win}")
    print(f"  Avg loss run length : {avg_loss}")
    print(f"  Max win  run        : {max(win_runs,  default=0)}")
    print(f"  Max loss run        : {max(loss_runs, default=0)}")
    print(f"  Loss run distribution: {dict(sorted(loss_dist.items()))}")
    verdict1 = "CYCLE DETECTED ✓" if avg_loss >= avg_win else "No systematic cycle"
    print(f"  Verdict : {verdict1}\n")

    print(f"SECTION 2 — R-MULTIPLE DISTRIBUTION  (Fix A validation)")
    print(sep)
    for k in ["win_0.0-0.5","win_0.5-1.0","win_1.0-1.5","win_1.5+","loss"]:
        vals = r_buckets[k]
        avg  = round(sum(vals)/max(len(vals),1), 2)
        print(f"  {k:14s}: {len(vals):4d} trades  avg_r={avg:+.2f}")
    print(f"  Unprotected wins (r<1.5) : {unprotected}/{total_wins}  ({pct_unprot}%)")
    verdict2 = "Fix A JUSTIFIED ✓" if pct_unprot > 50 else "Fix A — weak evidence"
    print(f"  Verdict : {verdict2}\n")

    print(f"SECTION 3 — RECOVERY vs NORMAL TRADES  (Fix B/C validation)")
    print(sep)
    rm = _m(rec);  nm = _m(norm)
    print(f"  Recovery trades : n={rm['n']:4d}  WR={rm['wr']:5.1f}%  avg_pnl={rm['avg_pnl']:+.4f}")
    print(f"  Normal   trades : n={nm['n']:4d}  WR={nm['wr']:5.1f}%  avg_pnl={nm['avg_pnl']:+.4f}")
    if rm["n"] > 5:
        verdict3 = "Recovery HURTS ✓ — Fix B evidence" if rm["avg_pnl"] < nm["avg_pnl"]*0.5 else "Recovery similar to normal"
    else:
        verdict3 = "Insufficient recovery trades to judge"
    print(f"  Verdict : {verdict3}\n")

    print(f"SECTION 4 — CONTEXT BOOST TRADES  (Fix B validation)")
    print(sep)
    bm = _m(boosted); nm2 = _m(nboosted)
    print(f"  Boosted     trades : n={bm['n']:4d}  WR={bm['wr']:5.1f}%  avg_pnl={bm['avg_pnl']:+.4f}")
    print(f"  Non-boosted trades : n={nm2['n']:4d}  WR={nm2['wr']:5.1f}%  avg_pnl={nm2['avg_pnl']:+.4f}")
    if bm["n"] > 5:
        verdict4 = "Boost HARMFUL ✓ — suppress recovery-mode boosts" if bm["avg_pnl"] < nm2["avg_pnl"]-0.05 else "Boost neutral/positive"
    else:
        verdict4 = "Insufficient boosted trades to judge"
    print(f"  Verdict : {verdict4}\n")

    print(f"{'═'*60}")
    ov = "STRONG" if (pct_unprot > 50 and avg_loss >= avg_win) else \
         "MODERATE" if (pct_unprot > 30 or avg_loss > avg_win) else "WEAK"
    print(f"  OVERALL HYPOTHESIS : {ov}")
    if ov in ("STRONG","MODERATE"):
        print(f"  NEXT ACTION        : Fix A (BREAKEVEN_TRIGGER_R 1.5→1.0) is justified.")
        print(f"  Fix B / Fix C      : Need above data before touching learning arch.")
    else:
        print(f"  NEXT ACTION        : Collect more trades. Hypothesis not yet proven.")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    print("Trying live endpoint first...")
    data = via_api()
    if data:
        print(json.dumps(data, indent=2))
        sys.exit(0)

    print("Endpoint not found (old branch?) — falling back to /api/trades...")
    raw = via_trades_api()
    if raw is None:
        sys.exit(1)

    trades = raw if isinstance(raw, list) else raw.get("trades", [])
    analyse_trades(trades)

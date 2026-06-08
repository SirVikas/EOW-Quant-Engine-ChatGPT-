"""
FTD-LONDON-001 Phase-B: London Entry Timing & Structural Forensics
Board Directive: Establish WHY London loses across all volatility regimes.

Run while engine is live:
    python analyse_london_phase_b.py

Output: entry timing, strategy mix, regime mix, exit-type distribution,
        context distribution — paste to Claude/Board for root cause ranking.
"""
import json, urllib.request, math
from collections import defaultdict

BASE = "http://localhost:8000"


def get(path, timeout=15):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}


def pct(n, total):
    return f"{n/total*100:.1f}%" if total else "N/A"


def section(title):
    print()
    print(f"  ── {title} {'─' * max(0, 60 - len(title))}")


def main():
    print("=" * 68)
    print("  FTD-LONDON-001 PHASE-B: LONDON STRUCTURAL FORENSICS")
    print("  Objective: Establish WHY London loses — not how to fix it yet.")
    print("=" * 68)

    trades_data = get("/api/trades")
    if "_error" in trades_data:
        print(f"  ERROR fetching trades: {trades_data['_error']}")
        print("  Is the engine running? (python main.py)")
        return

    trades = trades_data if isinstance(trades_data, list) else trades_data.get("trades", [])
    if not trades:
        print("  No trades available.")
        return

    print(f"  Total trades: {len(trades)}")

    london = [
        t for t in trades
        if (t.get("origin_session") or t.get("session") or "").upper() == "LONDON"
    ]
    non_london = [t for t in trades if t not in london]
    print(f"  LONDON trades: {len(london)}")
    print(f"  Non-LONDON trades: {len(non_london)}")

    if len(london) < 5:
        print("  Insufficient LONDON trades for Phase-B analysis (need ≥5).")
        return

    def stats(group):
        if not group:
            return {"count": 0, "wins": 0, "net_pnl": 0.0, "wr": 0.0, "pnl_per": 0.0}
        wins = sum(1 for t in group if float(t.get("net_pnl") or 0) > 0)
        pnl  = sum(float(t.get("net_pnl") or 0) for t in group)
        return {
            "count": len(group),
            "wins": wins,
            "net_pnl": pnl,
            "wr": wins / len(group),
            "pnl_per": pnl / len(group),
        }

    # ── 1. Entry Hour Distribution ────────────────────────────────────────────
    section("1. ENTRY HOUR DISTRIBUTION (UTC)")
    hour_buckets = defaultdict(list)
    missing_hour = 0
    for t in london:
        h = t.get("origin_utc_hour")
        if h is None or h == -1:
            # fallback: parse from entry_ts
            ts = t.get("entry_ts")
            if ts:
                h = (int(ts) // 3_600_000) % 24
        if h is not None and h != -1:
            hour_buckets[int(h)].append(t)
        else:
            missing_hour += 1
            hour_buckets["?"].append(t)

    print(f"  {'HOUR (UTC)':<14}  {'COUNT':>5}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TRADE':>10}  NOTE")
    print("  " + "-" * 66)
    london_hours = sorted([h for h in hour_buckets if h != "?"])
    # London session is roughly 07:00–16:00 UTC
    for h in london_hours + (["?"] if "?" in hour_buckets else []):
        s = stats(hour_buckets[h])
        note = ""
        if isinstance(h, int):
            if h < 7:  note = "pre-London"
            elif h < 10: note = "London open"
            elif h < 13: note = "London mid"
            elif h < 16: note = "London/NY overlap"
            else:        note = "post-London"
        print(f"  {str(h)+':00 UTC':<14}  {s['count']:>5}  {s['wr']:>6.1%}  "
              f"{s['net_pnl']:>10.4f}  {s['pnl_per']:>10.4f}  {note}")
    if missing_hour:
        print(f"  (origin_utc_hour missing/unknown: {missing_hour}/{len(london)})")

    # ── 2. Strategy Distribution ──────────────────────────────────────────────
    section("2. STRATEGY DISTRIBUTION")
    strat_buckets = defaultdict(list)
    for t in london:
        s = (t.get("strategy_id") or "UNKNOWN").split("_")[0]
        # normalize: strip symbol suffix
        strat_buckets[s].append(t)

    print(f"  {'STRATEGY':<22}  {'COUNT':>5}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TRADE':>10}")
    print("  " + "-" * 60)
    for strat in sorted(strat_buckets, key=lambda k: -len(strat_buckets[k])):
        s = stats(strat_buckets[strat])
        print(f"  {strat:<22}  {s['count']:>5}  {s['wr']:>6.1%}  "
              f"{s['net_pnl']:>10.4f}  {s['pnl_per']:>10.4f}")

    # ── 3. Regime Distribution ────────────────────────────────────────────────
    section("3. REGIME AT ENTRY")
    regime_buckets = defaultdict(list)
    for t in london:
        regime_buckets[t.get("regime") or "UNKNOWN"].append(t)

    print(f"  {'REGIME':<22}  {'COUNT':>5}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TRADE':>10}")
    print("  " + "-" * 60)
    for reg in sorted(regime_buckets, key=lambda k: -len(regime_buckets[k])):
        s = stats(regime_buckets[reg])
        print(f"  {reg:<22}  {s['count']:>5}  {s['wr']:>6.1%}  "
              f"{s['net_pnl']:>10.4f}  {s['pnl_per']:>10.4f}")

    # ── 4. Exit Method Distribution ───────────────────────────────────────────
    section("4. EXIT METHOD DISTRIBUTION")
    exit_buckets = defaultdict(list)
    for t in london:
        exit_buckets[t.get("exit_method") or t.get("close_tag") or "UNKNOWN"].append(t)

    print(f"  {'EXIT METHOD':<22}  {'COUNT':>5}  {'%':>5}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TRADE':>10}")
    print("  " + "-" * 70)
    total_l = len(london)
    for ex in sorted(exit_buckets, key=lambda k: -len(exit_buckets[k])):
        s = stats(exit_buckets[ex])
        print(f"  {ex:<22}  {s['count']:>5}  {pct(s['count'],total_l):>5}  "
              f"{s['wr']:>6.1%}  {s['net_pnl']:>10.4f}  {s['pnl_per']:>10.4f}")

    # ── 5. Session Boundary Crossings ─────────────────────────────────────────
    section("5. SESSION BOUNDARY CROSSINGS")
    crossed  = [t for t in london if t.get("crossed_session_boundary")]
    same_ses = [t for t in london if not t.get("crossed_session_boundary")]
    sc = stats(crossed);  ss = stats(same_ses)
    print(f"  {'TYPE':<28}  {'COUNT':>5}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TRADE':>10}")
    print("  " + "-" * 66)
    print(f"  {'Stayed in LONDON':<28}  {ss['count']:>5}  {ss['wr']:>6.1%}  "
          f"{ss['net_pnl']:>10.4f}  {ss['pnl_per']:>10.4f}")
    print(f"  {'Crossed session boundary':<28}  {sc['count']:>5}  {sc['wr']:>6.1%}  "
          f"{sc['net_pnl']:>10.4f}  {sc['pnl_per']:>10.4f}")
    transitions = defaultdict(list)
    for t in crossed:
        key = t.get("boundary_transition") or f"{t.get('origin_session','?')}→{t.get('close_session','?')}"
        transitions[key].append(t)
    for tr_key, tr_trades in sorted(transitions.items()):
        s = stats(tr_trades)
        print(f"    {tr_key:<26}  {s['count']:>5}  {s['wr']:>6.1%}  "
              f"{s['net_pnl']:>10.4f}  {s['pnl_per']:>10.4f}")

    # ── 6. London vs ASIA comparison ──────────────────────────────────────────
    section("6. LONDON vs ASIA COMPARISON (same metrics)")
    asia = [t for t in trades if (t.get("origin_session") or t.get("session") or "").upper() == "ASIA"]
    sl  = stats(london);  sa = stats(asia)
    print(f"  {'SESSION':<12}  {'COUNT':>5}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TRADE':>10}")
    print("  " + "-" * 54)
    print(f"  {'LONDON':<12}  {sl['count']:>5}  {sl['wr']:>6.1%}  "
          f"{sl['net_pnl']:>10.4f}  {sl['pnl_per']:>10.4f}")
    print(f"  {'ASIA':<12}  {sa['count']:>5}  {sa['wr']:>6.1%}  "
          f"{sa['net_pnl']:>10.4f}  {sa['pnl_per']:>10.4f}")

    # ── 7. ATR lineage check (v1.60.5+) ──────────────────────────────────────
    section("7. ATR LINEAGE STATUS (v1.60.5 fix verification)")
    with_atr    = sum(1 for t in london if float(t.get("atr_pct") or 0) > 0)
    without_atr = len(london) - with_atr
    print(f"  Trades with direct atr_pct:     {with_atr}/{len(london)}")
    print(f"  Trades still using SL proxy:    {without_atr}/{len(london)}")
    if with_atr > 0:
        print(f"  ATR lineage fix: ACTIVE ✅")
    else:
        print(f"  ATR lineage fix: not yet in trade history (pre-v1.60.5 trades)")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("  ┌─ PHASE-B INVESTIGATION QUESTIONS ─────────────────────────────┐")
    print("  │ 1. Which UTC hours have worst WR? (timing hypothesis)          │")
    print("  │ 2. Which strategy type dominates London losses?                │")
    print("  │ 3. Is any regime consistently losing? (regime mismatch?)       │")
    print("  │ 4. What % of exits are BE exits? (53% BE hypothesis)           │")
    print("  │ 5. Do boundary-crossing trades lose more?                      │")
    print("  └────────────────────────────────────────────────────────────────┘")
    print()
    print("  Paste this output to Claude/Board for Phase-B root cause ranking.")
    print("=" * 68)


if __name__ == "__main__":
    main()

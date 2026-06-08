"""
FTD-LONDON-001 Phase-C.1: Pre-London (06:00 UTC) Structural Forensics
Board Directive: Deep-dive on 06 UTC trades vs 07-12 UTC London trades.
Objective: Establish WHETHER 06 UTC trades are structurally different — not fix yet.

Run while engine is live:
    python analyse_london_phase_c1.py

Questions to answer:
  1. Are 06 UTC trades different symbols?
  2. Are they different strategies/contexts?
  3. Are their exit types different?
  4. Is the regime different?
  5. Is this a London session boundary classification issue?
"""
import json, urllib.request
from collections import defaultdict

BASE = "http://localhost:8000"


def get(path, timeout=15):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}


def stats(group):
    if not group:
        return {"count": 0, "wins": 0, "wr": 0.0, "net_pnl": 0.0, "pnl_per": 0.0}
    wins = sum(1 for t in group if float(t.get("net_pnl") or 0) > 0)
    pnl  = sum(float(t.get("net_pnl") or 0) for t in group)
    return {"count": len(group), "wins": wins, "wr": wins / len(group),
            "net_pnl": pnl, "pnl_per": pnl / len(group)}


def breakdown(group, field, label, top_n=10):
    buckets = defaultdict(list)
    for t in group:
        key = str(t.get(field) or "UNKNOWN")
        # Normalize strategy_id — strip symbol suffix
        if field == "strategy_id":
            key = key.split("_")[0]
        buckets[key].append(t)
    print(f"  {'':4}{label:<22}  {'N':>4}  {'WR':>7}  {'PNL/TR':>9}")
    print(f"  {'':4}{'-'*50}")
    for k in sorted(buckets, key=lambda x: -len(buckets[x]))[:top_n]:
        s = stats(buckets[k])
        print(f"  {'':4}{k:<22}  {s['count']:>4}  {s['wr']:>6.1%}  {s['pnl_per']:>9.4f}")


def main():
    print("=" * 70)
    print("  FTD-LONDON-001 PHASE-C.1: PRE-LONDON (06 UTC) STRUCTURAL FORENSICS")
    print("  Board Question: Are 06 UTC trades structurally different?")
    print("=" * 70)

    trades_data = get("/api/trades")
    if "_error" in trades_data:
        print(f"  ERROR: {trades_data['_error']}  — is engine running?")
        return

    trades = trades_data if isinstance(trades_data, list) else trades_data.get("trades", [])
    london = [
        t for t in trades
        if (t.get("origin_session") or t.get("session") or "").upper() == "LONDON"
    ]
    print(f"  Total trades: {len(trades)} | LONDON: {len(london)}")

    # Assign UTC hour
    def utc_hour(t):
        h = t.get("origin_utc_hour")
        if h is None or h == -1:
            ts = t.get("entry_ts")
            if ts:
                return (int(ts) // 3_600_000) % 24
            return -1
        return int(h)

    pre   = [t for t in london if utc_hour(t) == 6]
    core  = [t for t in london if 7 <= utc_hour(t) <= 12]
    other = [t for t in london if utc_hour(t) not in (6, *range(7, 13))]

    sp = stats(pre);  sc = stats(core);  so = stats(other)
    sl = stats(london)

    print()
    print(f"  {'GROUP':<28}  {'N':>4}  {'WR':>7}  {'NET PNL':>10}  {'PNL/TR':>9}")
    print(f"  {'-'*60}")
    print(f"  {'06 UTC (pre-London)':<28}  {sp['count']:>4}  {sp['wr']:>6.1%}  {sp['net_pnl']:>10.4f}  {sp['pnl_per']:>9.4f}")
    print(f"  {'07-12 UTC (core London)':<28}  {sc['count']:>4}  {sc['wr']:>6.1%}  {sc['net_pnl']:>10.4f}  {sc['pnl_per']:>9.4f}")
    print(f"  {'Other hours':<28}  {so['count']:>4}  {so['wr']:>6.1%}  {so['net_pnl']:>10.4f}  {so['pnl_per']:>9.4f}")
    print(f"  {'LONDON TOTAL':<28}  {sl['count']:>4}  {sl['wr']:>6.1%}  {sl['net_pnl']:>10.4f}  {sl['pnl_per']:>9.4f}")

    for label, group in [("06 UTC (pre-London)", pre), ("07-12 UTC (core London)", core)]:
        if not group:
            continue
        print()
        print(f"  ═══ {label} (n={len(group)}) ═══")

        print(f"\n  Symbol distribution:")
        breakdown(group, "symbol", "SYMBOL")

        print(f"\n  Strategy distribution:")
        breakdown(group, "strategy_id", "STRATEGY")

        print(f"\n  Regime at entry:")
        breakdown(group, "regime", "REGIME")

        print(f"\n  Exit method:")
        breakdown(group, "exit_method", "EXIT_METHOD")

        print(f"\n  Context type (from decision_snapshot):")
        ctx_buckets = defaultdict(list)
        for t in group:
            snap = t.get("decision_snapshot") or {}
            if isinstance(snap, str):
                import json as _j
                try: snap = _j.loads(snap)
                except: snap = {}
            ctx = snap.get("context_type") or snap.get("ctx_type") or "UNKNOWN"
            ctx_buckets[ctx].append(t)
        print(f"  {'':4}{'CONTEXT':<22}  {'N':>4}  {'WR':>7}  {'PNL/TR':>9}")
        print(f"  {'':4}{'-'*40}")
        for k in sorted(ctx_buckets, key=lambda x: -len(ctx_buckets[x])):
            s = stats(ctx_buckets[k])
            print(f"  {'':4}{k:<22}  {s['count']:>4}  {s['wr']:>6.1%}  {s['pnl_per']:>9.4f}")

        # Individual trade list for pre-London
        if label.startswith("06"):
            print(f"\n  Individual 06 UTC trades (complete list):")
            print(f"  {'':4}{'SYMBOL':<12}  {'STRATEGY':<20}  {'EXIT':<14}  {'WR':>5}  {'NET PNL':>9}  ENTRY_TS")
            print(f"  {'':4}{'-'*75}")
            for t in sorted(group, key=lambda x: x.get("entry_ts", 0)):
                won = "W" if float(t.get("net_pnl") or 0) > 0 else "L"
                strat = (t.get("strategy_id") or "?").split("_")[0][:19]
                ts = t.get("entry_ts", 0)
                from datetime import datetime, timezone
                dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if ts else "?"
                print(f"  {'':4}{t.get('symbol','?'):<12}  {strat:<20}  {(t.get('exit_method') or '?'):<14}  {won:>5}  {float(t.get('net_pnl') or 0):>9.4f}  {dt}")

    # ── Board question summary ────────────────────────────────────────────────
    print()
    print("  ┌─ PHASE-C.1 BOARD QUESTIONS ───────────────────────────────────────┐")
    print("  │ 1. Same symbols at 06 UTC as 07-12 UTC?                            │")
    print("  │ 2. Same strategies at 06 UTC as 07-12 UTC?                         │")
    print("  │ 3. Are 06 UTC exits predominantly FAST_FAIL or STOP_LOSS?          │")
    print("  │ 4. Is 06 UTC a session classification bug or a strategy misfire?    │")
    print("  │ 5. If 06 UTC trades removed: what is 07-12 UTC London WR?          │")
    print("  └────────────────────────────────────────────────────────────────────┘")
    print()
    print(f"  07-12 UTC London WR (without 06 UTC): {sc['wr']:.1%}  |  PnL/trade: {sc['pnl_per']:.4f}")
    print()
    print("  Paste to Claude/Board for Phase-C.1 verdict.")
    print("=" * 70)


if __name__ == "__main__":
    main()

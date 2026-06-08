"""
LONDON ATR Bucket Analysis
Board directive: before changing SESSION_MIN_ATR_PCT for LONDON,
prove which ATR buckets are profitable vs unprofitable.

Run while engine is live:
    python analyse_london_atr.py

Output: per-ATR-bucket WR, PnL, fee drag — paste to Claude/Board for decision.
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


def atr_bucket(atr_pct: float) -> str:
    if atr_pct is None or atr_pct <= 0:
        return "UNKNOWN"
    if atr_pct < 0.10:
        return "<0.10%"
    if atr_pct < 0.15:
        return "0.10-0.15%"
    if atr_pct < 0.20:
        return "0.15-0.20%"
    if atr_pct < 0.25:
        return "0.20-0.25%"
    if atr_pct < 0.30:
        return "0.25-0.30%"
    if atr_pct < 0.40:
        return "0.30-0.40%"
    return ">=0.40%"


def main():
    print("=" * 66)
    print("  LONDON ATR BUCKET ANALYSIS")
    print("  Board Directive: prove ATR vs WR relationship before filter change")
    print("=" * 66)

    trades_data = get("/api/trades")
    if "_error" in trades_data:
        print(f"  ERROR fetching trades: {trades_data['_error']}")
        print("  Is the engine running? (python main.py)")
        return

    trades = trades_data if isinstance(trades_data, list) else trades_data.get("trades", [])
    if not trades:
        print("  No trades available.")
        return

    print(f"  Total trades loaded: {len(trades)}")

    # Filter LONDON trades only
    london = [
        t for t in trades
        if (t.get("origin_session") or t.get("session") or "").upper() == "LONDON"
    ]
    print(f"  LONDON trades: {len(london)}")

    if len(london) < 10:
        print("  Insufficient LONDON trades for bucket analysis (need ≥10).")
        return

    # ── Bucket by ATR ─────────────────────────────────────────────────────────
    buckets: dict = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0, "fees": 0.0})
    atr_field_candidates = ["atr_pct", "entry_atr_pct", "atr_at_entry", "atr"]

    missing_atr = 0
    for t in london:
        atr_val = None
        for field in atr_field_candidates:
            v = t.get(field)
            if v and float(v) > 0:
                atr_val = float(v)
                # Convert to % if it looks like an absolute value (>1.0 means it's not a %)
                if atr_val > 1.0:
                    entry = float(t.get("entry_price") or 1)
                    atr_val = (atr_val / entry) * 100 if entry > 0 else None
                break

        if atr_val is None:
            missing_atr += 1
            # Try to compute from entry/sl distance as proxy
            entry = float(t.get("entry_price") or 0)
            sl = float(t.get("stop_loss") or 0)
            if entry > 0 and sl > 0:
                atr_val = abs(entry - sl) / entry * 100

        bucket = atr_bucket(atr_val)
        net_pnl = float(t.get("net_pnl") or t.get("pnl") or 0)
        fee = float(t.get("fee") or t.get("fees") or 0)

        buckets[bucket]["count"] += 1
        buckets[bucket]["fees"] += fee
        buckets[bucket]["pnl"] += net_pnl
        if net_pnl > 0:
            buckets[bucket]["wins"] += 1

    # ── Print results ─────────────────────────────────────────────────────────
    print(f"\n  (ATR missing/estimated from SL distance: {missing_atr}/{len(london)})")
    print()

    order = ["<0.10%", "0.10-0.15%", "0.15-0.20%", "0.20-0.25%",
             "0.25-0.30%", "0.30-0.40%", ">=0.40%", "UNKNOWN"]

    header = f"  {'ATR RANGE':<14}  {'COUNT':>6}  {'WR':>7}  {'NET PNL':>10}  {'FEES':>8}  {'PNL/TRADE':>10}  {'VERDICT'}"
    print(header)
    print("  " + "-" * 78)

    current_floor = 0.15  # current SESSION_MIN_ATR_PCT LONDON

    for b in order:
        d = buckets.get(b)
        if not d or d["count"] == 0:
            continue
        wr = d["wins"] / d["count"]
        pnl_per_trade = d["pnl"] / d["count"]
        fee_drag_pct = (d["fees"] / max(abs(d["pnl"]) + d["fees"], 0.001)) * 100

        # Verdict
        if wr >= 0.40 and pnl_per_trade > 0:
            verdict = "✅ KEEP"
        elif wr >= 0.30 and pnl_per_trade > 0:
            verdict = "⚠ MARGINAL"
        elif pnl_per_trade < 0:
            verdict = "❌ LOSING"
        else:
            verdict = "⚠ UNCLEAR"

        # Mark buckets below current floor
        below_floor = ""
        try:
            lo = float(b.split("%")[0].split("-")[0].replace("<","").replace(">=",""))
            if lo < current_floor:
                below_floor = " [below current floor]"
        except Exception:
            pass

        print(f"  {b+below_floor:<28}  {d['count']:>4}  {wr:>6.1%}  {d['pnl']:>10.4f}  "
              f"{d['fees']:>8.4f}  {pnl_per_trade:>10.4f}  {verdict}")

    # ── All LONDON summary ─────────────────────────────────────────────────────
    total_count = sum(d["count"] for d in buckets.values())
    total_wins  = sum(d["wins"]  for d in buckets.values())
    total_pnl   = sum(d["pnl"]   for d in buckets.values())
    total_fees  = sum(d["fees"]  for d in buckets.values())

    print("  " + "-" * 78)
    print(f"  {'LONDON TOTAL':<28}  {total_count:>4}  "
          f"{total_wins/total_count:>6.1%}  {total_pnl:>10.4f}  "
          f"{total_fees:>8.4f}  {total_pnl/total_count:>10.4f}")

    # ── Board recommendation template ──────────────────────────────────────────
    print()
    print("  ┌─ BOARD QUESTION ──────────────────────────────────────────────┐")
    print("  │ Which ATR buckets are LOSING in LONDON?                       │")
    print("  │ If 0.15-0.20% bucket is losing → raise floor to 0.20%        │")
    print("  │ If 0.20-0.25% is also losing   → raise floor to 0.25%        │")
    print("  │ If all buckets losing           → ATR is not the root cause   │")
    print("  └───────────────────────────────────────────────────────────────┘")
    print()
    print("  Paste this output to Claude/Board for ATR floor decision.")
    print("=" * 66)


if __name__ == "__main__":
    main()

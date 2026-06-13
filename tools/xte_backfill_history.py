#!/usr/bin/env python3
"""
XTE HISTORICAL BACKFILL — generate REAL evidence fast (no 200-day wait).

Replays your already-recorded historical trades + candles from the DataLake
(data/eow_lake.db) through the EXACT exit_truth_engine.evaluate(), reconstructing
each trade's open-position path candle-by-candle and producing real XTE
observation records. This is a BACKTEST on real market data + real outcomes —
legitimate evidence, generated in minutes instead of waiting for ~200 days of
live trading to reach 100 trades.

Honesty / caveats (stated, not hidden):
  • Real data, retrospective: tests XTE on PAST regimes; future may differ
    (standard backtest caveat). Records are tagged source="historical_backfill".
  • Candle-granularity (1m) path reconstruction vs live tick granularity — minor.
  • Trades whose candle window is missing in the lake are skipped (reported).
  This is FAR stronger than synthetic data and is real evidence — but a live
  campaign remains the gold standard for final confirmation.

Usage (run on the machine with the populated lake):
    python tools/xte_backfill_history.py                       # all trades → real archive, prints verdict
    python tools/xte_backfill_history.py --limit 2000          # cap trades scanned
    python tools/xte_backfill_history.py --reset               # clear target archive first
    python tools/xte_backfill_history.py --db data/eow_lake.db --archive reports/xte_observations/backfill_obs.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg

_WARMUP_MS = 30 * 60 * 1000   # 30 min of 1m candles before entry for buffers


def _connect_ro(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        raise SystemExit(f"DataLake not found: {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _avg(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _summarize(group):
    if not group:
        return {"n": 0}
    import datetime as _dt
    ts = [int(t.get("entry_ts", 0) or 0) for t in group if t.get("entry_ts")]
    def _d(ms):
        return _dt.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d") if ms else "?"
    regimes = {}
    for t in group:
        regimes[t.get("regime", "?")] = regimes.get(t.get("regime", "?"), 0) + 1
    pnls = [float(t.get("net_pnl", 0) or 0) for t in group]
    return {
        "n": len(group),
        "date_range": [_d(min(ts)) if ts else "?", _d(max(ts)) if ts else "?"],
        "avg_peak_r": _avg([t.get("peak_r") for t in group]),
        "avg_exit_r": _avg([t.get("r_multiple") for t in group]),
        "avg_net_pnl": _avg(pnls),
        "win_rate_pct": round(sum(1 for p in pnls if p >= 0) / len(pnls) * 100, 1),
        "top_regimes": dict(sorted(regimes.items(), key=lambda kv: -kv[1])[:3]),
    }


def _trades(conn, limit):
    cur = conn.execute("SELECT data FROM trades ORDER BY ts DESC LIMIT ?", (limit,))
    return [json.loads(r["data"]) for r in cur.fetchall()]


def _candles(conn, symbol, since_ts, until_ts, interval="1m", limit=10000):
    cur = conn.execute(
        """SELECT open,high,low,close,volume,ts FROM candles
           WHERE symbol=? AND interval=? AND ts>? AND ts<=? ORDER BY ts ASC LIMIT ?""",
        (symbol, interval, since_ts, until_ts, limit),
    )
    return [dict(r) for r in cur.fetchall()]


def _atr_pct(highs, lows, closes, period=14):
    n = len(closes)
    if n < 2:
        return 0.0
    trs = []
    for i in range(1, n):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    window = trs[-period:] if len(trs) >= period else trs
    atr = sum(window) / len(window) if window else 0.0
    last = closes[-1] if closes[-1] else 1.0
    return (atr / last * 100.0) if last else 0.0


def _backfill_one(trade, conn, observer) -> str:
    sym = trade.get("symbol")
    side = trade.get("side") or ("SHORT" if trade.get("is_short") else "LONG")
    entry = float(trade.get("entry_price", 0) or 0)
    init_sl = float(trade.get("stop_loss", 0) or trade.get("initial_stop_loss", 0) or 0)
    entry_ts = int(trade.get("entry_ts", 0) or 0)
    exit_ts = int(trade.get("exit_ts", 0) or 0)
    if not (sym and entry and init_sl and entry_ts and exit_ts) or exit_ts <= entry_ts:
        return "skip_fields"
    risk = abs(entry - init_sl)
    if risk <= 0:
        return "skip_risk"

    candles = _candles(conn, sym, entry_ts - _WARMUP_MS, exit_ts)
    in_trade = [c for c in candles if c["ts"] >= entry_ts]
    if len(in_trade) < 2:
        return "skip_candles"

    closes, highs, lows, vols = [], [], [], []
    atr_ema = 0.0
    peak_r = 0.0
    for c in candles:
        closes.append(c["close"]); highs.append(c["high"])
        lows.append(c["low"]); vols.append(c["volume"])
        if c["ts"] < entry_ts:
            continue
        atr_pct = _atr_pct(highs, lows, closes)
        atr_ema = atr_pct if atr_ema == 0.0 else atr_ema * 0.9 + atr_pct * 0.1
        # running peak R from candle extreme
        fav = (c["high"] - entry) if side == "LONG" else (entry - c["low"])
        peak_r = max(peak_r, fav / risk)
        pos = SimpleNamespace(symbol=sym, side=side, entry_price=entry,
                              stop_loss=init_sl, initial_stop_loss=init_sl,
                              peak_r=round(peak_r, 4), entry_ts=entry_ts,
                              regime=trade.get("regime", "UNKNOWN"))
        observer.observe(pos, price=c["close"], closes=closes, volumes=vols,
                         atr_pct=atr_pct, atr_ema=atr_ema)

    tr = SimpleNamespace(
        symbol=sym, side=side,
        r_multiple=float(trade.get("r_multiple", 0) or 0),
        peak_r=max(peak_r, float(trade.get("peak_r", 0) or 0)),
        net_pnl=float(trade.get("net_pnl", 0) or 0),
        regime=trade.get("regime", "UNKNOWN"),
        entry_ts=entry_ts, exit_ts=exit_ts,
        atr_pct=float(trade.get("atr_pct", 0) or 0),
        exit_method=trade.get("exit_method") or trade.get("exit_reason") or "HISTORICAL",
    )
    observer.on_close(sym, tr, tag="historical_backfill")
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="XTE historical backfill (real backtest evidence)")
    ap.add_argument("--db", default="data/eow_lake.db")
    ap.add_argument("--limit", type=int, default=20000)
    ap.add_argument("--append", action="store_true",
                    help="append to existing archive (default: RESET — a backfill is a full replay)")
    ap.add_argument("--archive", default="reports/xte_observations/backfill_obs.jsonl")
    ap.add_argument("--paths", default="reports/xte_observations/backfill_paths.jsonl")
    args = ap.parse_args()
    args.reset = not args.append   # default reset so re-runs never double-count

    print("\n  XTE HISTORICAL BACKFILL — real-data backtest (not synthetic)")
    cfg.XTE_OBSERVE_ARCHIVE = args.archive
    cfg.XTE_PATH_ARCHIVE = args.paths
    cfg.XTE_OBSERVE_PATH_ENABLED = True
    for p in (args.archive, args.paths):
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
        if args.reset and os.path.exists(p):
            os.remove(p)

    # import observer AFTER cfg paths set
    from core.truth.xte_observer import xte_observer
    conn = _connect_ro(args.db)
    trades = _trades(conn, args.limit)
    print(f"  loaded {len(trades)} historical trades from {args.db}")

    stats = {"ok": 0, "skip_fields": 0, "skip_risk": 0, "skip_candles": 0}
    kept, skipped = [], []
    for t in trades:
        r = _backfill_one(t, conn, xte_observer)
        stats[r] += 1
        (kept if r == "ok" else skipped).append(t)
    print(f"  backfilled={stats['ok']}  skipped: "
          f"fields={stats['skip_fields']} risk={stats['skip_risk']} no_candles={stats['skip_candles']}")

    from core.truth import xte_validation as xv
    rep = xv.full_report()
    iv, v = rep["interim_verdict"], rep["verdict"]
    print(f"\n  ── REAL EVIDENCE VERDICT (historical backtest) ──")
    print(f"    samples           : {iv.get('n')}")
    print(f"    interim early-stop : {iv.get('status')}  |  {iv.get('reason')}")
    if v.get("status") == "INSUFFICIENT_DATA":
        print(f"    final verdict     : INSUFFICIENT_DATA ({v.get('samples')}/{v.get('target')}) — rely on interim above")
    else:
        print(f"    final verdict     : {v.get('status')}")
        print(f"    +R per trade      : {v.get('avg_r_delta_per_trade')}  (bar >= {v.get('success_criteria',{}).get('min_r_per_trade')})  <-- the honest metric")
        print(f"    protect precision : {v.get('protect_precision_pct')}%")
        print(f"    gain concentration: top 5% of trades = {v.get('gain_concentration_top5pct')}% of total gain")
        print(f"    uplift% (context) : {v.get('economic_uplift_pct')}  (unreliable near breakeven — do NOT headline)")
    pcf = rep["path_counterfactual"]
    print(f"    coverage          : evaluated={pcf.get('evaluated')} improved={pcf.get('improved')} "
          f"worsened={pcf.get('worsened')} no_signal={pcf.get('no_protective_signal')}")
    rs = rep["robustness_split"]
    print(f"\n  ── WALK-FORWARD ROBUSTNESS (does it hold across time?) ──")
    if rs.get("per_segment"):
        for seg in rs["per_segment"]:
            print(f"    segment {seg['segment']}: n={seg['n']} +{seg['avg_r_delta_per_trade']}R/trade "
                  f"{'PASS' if seg['passes_bar'] else 'FAIL'}")
        print(f"    consistent_across_time: {rs['consistent_across_time']} — {rs['interpretation']}")
    else:
        print(f"    {rs.get('note')}")

    # selection-bias visibility
    total = stats["ok"] + stats["skip_candles"] + stats["skip_fields"] + stats["skip_risk"]
    cov = round(stats["ok"] / total * 100, 1) if total else 0.0
    print(f"\n  ── SELECTION BIAS (the main threat) ──")
    print(f"    candle coverage: {stats['ok']}/{total} trades = {cov}%  "
          f"({stats['skip_candles']} skipped for no candles)")
    k_sum, s_sum = _summarize(kept), _summarize(skipped)
    print(f"    KEPT    : {k_sum}")
    print(f"    SKIPPED : {s_sum}")
    # verdict on representativeness
    if s_sum.get("n"):
        same_era = k_sum["date_range"] != s_sum["date_range"]
        pk_gap = abs(k_sum["avg_peak_r"] - s_sum["avg_peak_r"])
        ex_gap = abs(k_sum["avg_exit_r"] - s_sum["avg_exit_r"])
        if k_sum["date_range"][0] > s_sum["date_range"][1] or s_sum["date_range"][0] > k_sum["date_range"][1]:
            print("    → DISJOINT eras: skips are a different time window (likely candle-retention).")
            print("       Backtest = that recent window only; representative of recent regime, not all history.")
        elif pk_gap < 0.2 and ex_gap < 0.2:
            print("    → Kept vs skipped look SIMILAR (peak_r/exit_r) → selection bias likely benign.")
        else:
            print(f"    ⚠ Kept vs skipped DIFFER (peak_r Δ={round(pk_gap,2)}, exit_r Δ={round(ex_gap,2)}) "
                  "→ bias may overstate the result; treat verdict with caution.")
    if cov < 80:
        print(f"    ⚠  {round(100-cov,1)}% of trades excluded — verdict is on a SUBSET.")

    print(f"\n    data_basis        : {iv.get('data_basis')}  (records tagged source=historical_backfill)")
    print("    ⚠  retrospective backtest — confirm on a forward/live slice before any acting role (X3).")
    if stats["ok"] == 0:
        print("\n  NOTE: 0 trades backfilled — the lake has trades but no matching candle\n"
              "  windows (or no trades). Real evidence needs both. Check db_stats / candle coverage.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

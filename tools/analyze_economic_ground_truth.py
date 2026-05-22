"""
FTD-ECO-TRUTH — Economic Ground Truth Analyzer

Reads persisted trade data directly (no live engine required) and produces:

  1. Fee-adjusted expectancy and gross/net comparison
  2. Economic classification breakdown (7 categories)
  3. Subsystem attribution (by RL rule type, session, cross-boundary)
  4. Payoff geometry (winner/loser duration, fee drag, asymmetry)
  5. Hold-duration bucket analysis (net expectancy per duration band)
  6. Session economics (origin + close session breakdowns)
  7. Economic survivability score (composite, 0–100)

Usage:
    python tools/analyze_economic_ground_truth.py
    python tools/analyze_economic_ground_truth.py --json
    python tools/analyze_economic_ground_truth.py --session NY
    python tools/analyze_economic_ground_truth.py --verbose
    python tools/analyze_economic_ground_truth.py --db path/to/data_lake.db
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

_HERE         = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
sys.path.insert(0, str(_PROJECT_ROOT))

DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "data_lake.db"


# ── DataLake reader ───────────────────────────────────────────────────────────

def _load_trades(db_path: Path, symbol: str = "", limit: int = 2000) -> list[dict]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        if symbol:
            cur = conn.execute(
                "SELECT data FROM trades WHERE symbol=? ORDER BY ts ASC LIMIT ?",
                (symbol, limit),
            )
        else:
            cur = conn.execute(
                "SELECT data FROM trades ORDER BY ts ASC LIMIT ?", (limit,)
            )
        rows = [json.loads(r["data"]) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


# ── Printer ───────────────────────────────────────────────────────────────────

def _pct(v: float | None, decimals: int = 1) -> str:
    return f"{v:.{decimals}f}%" if v is not None else "—"

def _val(v: float | None, decimals: int = 4) -> str:
    return f"{v:+.{decimals}f}" if v is not None else "—"


def _print_report(result: dict, verbose: bool = False) -> None:
    W = 72
    print(f"\n{'='*W}")
    print("  FTD-ECO-TRUTH — Economic Ground Truth Analyzer")
    print(f"{'='*W}")

    total = result.get("total_trades", 0)
    print(f"\n  Total trades:      {total}")
    if result.get("note"):
        print(f"  {result['note']}")
        print(f"\n{'='*W}\n")
        return

    # Expectancy overview
    print(f"\n  ── Expectancy Overview ──")
    print(f"  Total net PnL:     {_val(result.get('total_net_pnl'), 2)} USDT")
    print(f"  Net expectancy:    {_val(result.get('net_expectancy'),   4)} USDT/trade")
    print(f"  Gross expectancy:  {_val(result.get('gross_expectancy'), 4)} USDT/trade")

    # Fee drag distribution
    fd = result.get("fee_drag_distribution", {})
    if fd.get("count", 0) > 0:
        print(f"\n  ── Fee Drag Distribution (% of gross profit) ──")
        print(f"  Trades with measurable drag: {fd['count']}")
        print(f"  Mean:   {fd.get('mean', '—'):.1f}%   "
              f"Median: {fd.get('median', '—'):.1f}%   "
              f"Max: {fd.get('max', '—'):.1f}%")
        print(f"  Above 80% (UNSURVIVABLE): {fd.get('above_80pct_count', 0)}")
        print(f"  Above 50% (borderline):   {fd.get('above_50pct_count', 0)}")

    # Economic classification
    cls = result.get("economic_classification", {})
    if cls:
        print(f"\n  ── Economic Classification ──")
        labels = [
            ("TRUE_POSITIVE_ALPHA", "TRUE_POS_ALPHA"),
            ("SURVIVABLE",          "SURVIVABLE    "),
            ("NOISE_WIN",           "NOISE_WIN     "),
            ("MICRO_EDGE_ERODED",   "MICRO_ERODED  "),
            ("UNSURVIVABLE",        "UNSURVIVABLE  "),
            ("TRUE_NEGATIVE",       "TRUE_NEGATIVE "),
        ]
        for key, label in labels:
            row = cls.get(key, {})
            cnt = row.get("count", 0)
            if cnt == 0:
                continue
            share = row.get("share_pct", 0)
            exp   = _val(row.get("expectancy"), 4)
            bar   = "█" * min(int(share / 4), 25)
            print(f"  {label}: {cnt:>5}  ({share:>4.0f}%)  exp={exp}  {bar}")
        if cls.get("FALSE_EDGE", {}).get("portfolio_detected"):
            fe = cls["FALSE_EDGE"]
            print(f"\n  ⚠  FALSE_EDGE DETECTED: WR={fe.get('portfolio_wr','—')}%  "
                  f"avg_net={_val(fe.get('portfolio_avg_net'), 4)}")

    # Payoff geometry
    geo = result.get("payoff_geometry", {})
    if geo:
        print(f"\n  ── Payoff Geometry ──")
        print(f"  Fee-adjusted WR:       {_pct(geo.get('fee_adjusted_win_rate_pct'))}")
        print(f"  Payoff asymmetry:      {_val(geo.get('payoff_asymmetry_ratio'), 3)}×")
        print(f"  Avg win:               {_val(geo.get('avg_win_usdt'), 4)} USDT")
        print(f"  Avg loss:              {_val(geo.get('avg_loss_usdt'), 4)} USDT")
        awh = geo.get("avg_winner_hold_sec")
        alh = geo.get("avg_loser_hold_sec")
        print(f"  Avg winner hold:       {f'{awh/60:.1f} min' if awh is not None else '—'}")
        print(f"  Avg loser hold:        {f'{alh/60:.1f} min' if alh is not None else '—'}")
        print(f"  Winner fee drag:       {_pct(geo.get('avg_winner_fee_drag_pct'))}")
        print(f"  Loser fee drag:        {_pct(geo.get('avg_loser_fee_drag_pct'))}")

        if verbose:
            buckets = geo.get("hold_duration_buckets", [])
            if buckets:
                print(f"\n  Hold Duration Buckets:")
                for b in buckets:
                    cnt = b.get("count", 0)
                    if cnt == 0:
                        continue
                    exp = _val(b.get("avg_net_pnl"), 4)
                    print(f"    {b['bucket']:<12}: {cnt:>4} trades  avg_net={exp}")

    # Subsystem attribution
    sub = result.get("subsystem_attribution", {})
    if sub:
        print(f"\n  ── Subsystem Attribution ──")
        rows = [
            ("Rule1-UCB",      "RULE1_UCB_expectancy"),
            ("Rule4-Floor",    "RULE4_MIN_EXPLORE_expectancy"),
            ("Exploit",        "EXPLOIT_expectancy"),
            ("Unknown",        "UNKNOWN_expectancy"),
            ("Cross-boundary", "cross_boundary_expectancy"),
            ("Within-session", "within_session_expectancy"),
        ]
        for label, key in rows:
            v = sub.get(key)
            if v is not None:
                print(f"  {label:<18}: {_val(v, 4)} USDT/trade")
        cb = sub.get("cross_boundary_count", 0)
        ws = sub.get("within_session_count", 0)
        print(f"  Cross-boundary trades: {cb}  |  Within-session: {ws}")

    # Session economics
    sess_rows = result.get("session_economics", [])
    if sess_rows:
        print(f"\n  ── Session Economics ──")
        print(f"  {'Session':<8} {'OrigCount':>9} {'OrigExp':>8} {'OrigWR%':>7}  "
              f"{'CloseCount':>10} {'CloseExp':>9}")
        print(f"  {'-'*58}")
        for r in sess_rows:
            oe  = _val(r.get("origin_expectancy"), 4)
            owr = _pct(r.get("origin_win_rate_pct"))
            ce  = _val(r.get("close_expectancy"), 4)
            print(f"  {r['session']:<8} {r['origin_trade_count']:>9} {oe:>8} {owr:>7}  "
                  f"{r['close_trade_count']:>10} {ce:>9}")

    # Survivability score
    surv = result.get("survivability_score", {})
    if surv:
        score = surv.get("score", 0)
        tier  = surv.get("tier", "—")
        print(f"\n  ── Economic Survivability Score ──")
        bar = "█" * (score // 5)
        print(f"  Score: {score}/100  [{tier}]  {bar}")
        if verbose:
            ev = surv.get("evidence", {})
            for component, passed in ev.items():
                icon = "✓" if passed else "✗"
                print(f"    {icon} {component}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Economic ground truth analyzer")
    parser.add_argument("--db",      default=str(DEFAULT_DB_PATH),
                        help="Path to data_lake.db")
    parser.add_argument("--symbol",  default="",
                        help="Filter by symbol (empty = all)")
    parser.add_argument("--session", default="",
                        help="Filter by origin_session (e.g. NY)")
    parser.add_argument("--limit",   default=2000, type=int,
                        help="Max trades to read from DataLake")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.economic_truth import compute_economic_ground_truth

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]

    result = compute_economic_ground_truth(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

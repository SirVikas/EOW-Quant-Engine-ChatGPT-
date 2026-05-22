"""
FTD-EXPLORE-ATTR — Exploration Economic Survivability Analyzer

Reads persisted trade data directly (no live engine required) and produces:

  1. Per-type economic performance (Rule1-UCB / Rule4-floor / Exploit / Unknown)
       — WR, avg PnL, avg hold duration, avg fee drag

  2. Q-delta diagnostics
       — Directional Q improvement rate after Rule4 trades
       — Avg Q at entry for floor-explore contexts

  3. Exploration-to-profitability correlation

  4. Session-linked Rule4 diagnostics
       — Per-session Rule4 WR, Q-impact, avg PnL
       — NY-specific breakdown (persistent least-negative outlier)

  5. Survivability classification breakdown
       — EXPLORATION_RECOVERY / EXPLORATION_POSITIVE / EXPLORATION_NEGATIVE /
         EXPLORATION_NOISE / EXPLORATION_UNRESOLVED

  6. Longitudinal dynamics
       — Rule4 dependency ratio over time
       — Rolling 10/25-trade exploration effectiveness
       — Survival-rate correlation vs exploration share

Usage:
    python tools/analyze_exploration_economic_survivability.py
    python tools/analyze_exploration_economic_survivability.py --json
    python tools/analyze_exploration_economic_survivability.py --session NY
    python tools/analyze_exploration_economic_survivability.py --type RULE4_MIN_EXPLORE
    python tools/analyze_exploration_economic_survivability.py --db path/to/data_lake.db
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

_HERE         = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent

# Inject project root so imports work without installation
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


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 70
    print(f"\n{'='*W}")
    print("  FTD-EXPLORE-ATTR — Exploration Economic Survivability Analyzer")
    print(f"{'='*W}")

    total = result.get("total_trades", 0)
    exp_c = result.get("exploration_trades_count", 0)
    print(f"\n  Total trades:            {total}")
    print(f"  Exploration trades:      {exp_c}")

    if result.get("note"):
        print(f"\n  {result['note']}")
        print(f"\n{'='*W}\n")
        return

    # Per-type metrics
    print(f"\n  ── Per-Type Economic Performance ──")
    per_type = result.get("per_type_metrics", {})
    header = f"  {'Type':<22} {'Count':>6} {'WR%':>5} {'AvgPnL':>8} {'AvgHoldMin':>10} {'FeeDrag%':>8}"
    print(header)
    print(f"  {'-'*70}")
    for label, key in [
        ("RULE1_UCB (natural)",  "RULE1_UCB"),
        ("RULE4_FLOOR",          "RULE4_MIN_EXPLORE"),
        ("EXPLOIT (normal)",     "EXPLOIT"),
        ("UNKNOWN (legacy)",     "UNKNOWN"),
    ]:
        m = per_type.get(key, {})
        cnt = m.get("count", 0)
        if cnt == 0:
            continue
        wr  = f"{m['win_rate_pct']:.1f}" if m.get("win_rate_pct") is not None else "—"
        pnl = f"{m['avg_net_pnl']:+.4f}" if m.get("avg_net_pnl") is not None else "—"
        hold_ms = m.get("avg_hold_ms") or 0
        hold_min = f"{hold_ms / 60_000:.1f}" if hold_ms else "—"
        drag = f"{m['avg_fee_drag_pct']:.4f}" if m.get("avg_fee_drag_pct") is not None else "—"
        print(f"  {label:<22} {cnt:>6} {wr:>5} {pnl:>8} {hold_min:>10} {drag:>8}")

    # Q-delta
    qd = result.get("q_delta_diagnostics", {})
    if qd.get("rule4_count", 0) > 0:
        print(f"\n  ── Rule4 Q-Delta Diagnostics ──")
        print(f"  Rule4 trades:       {qd['rule4_count']}")
        qi = qd.get("q_improved_pct")
        print(f"  Q improved (proxy): {f'{qi:.1f}%' if qi is not None else '—'}")
        aqe = qd.get("avg_q_at_entry")
        print(f"  Avg Q at entry:     {f'{aqe:+.4f}' if aqe is not None else '—'}")
        apnl = qd.get("avg_net_pnl")
        print(f"  Avg net PnL:        {f'{apnl:+.4f}' if apnl is not None else '—'}")

    # Correlation
    corr = result.get("exploration_profitability_correlation")
    if corr is not None:
        print(f"\n  Exploration↔Profitability correlation: {corr:+.4f}")
        if corr > 0.1:
            print(f"  → Exploration POSITIVELY correlated with profitability")
        elif corr < -0.1:
            print(f"  → Exploration NEGATIVELY correlated with profitability")
        else:
            print(f"  → No significant correlation detected")

    # Session breakdown
    sess_rows = result.get("session_breakdown", [])
    if sess_rows:
        print(f"\n  ── Session-Linked Rule4 Diagnostics ──")
        print(f"  {'Session':<8} {'Total':>6} {'Rule4':>6} {'R4 WR%':>7} {'R4 AvgQ':>8} {'R4 AvgPnL':>10}")
        print(f"  {'-'*55}")
        for r in sess_rows:
            wr  = f"{r['rule4_wr_pct']:.1f}"  if r.get("rule4_wr_pct")      is not None else "—"
            aq  = f"{r['rule4_avg_q_entry']:+.4f}" if r.get("rule4_avg_q_entry") is not None else "—"
            ap  = f"{r['rule4_avg_net_pnl']:+.4f}" if r.get("rule4_avg_net_pnl") is not None else "—"
            print(f"  {r['session']:<8} {r['total_trades']:>6} {r['rule4_count']:>6} {wr:>7} {aq:>8} {ap:>10}")

    # NY highlight
    ny = result.get("ny_rule4_diagnostics", {})
    if ny.get("rule4_count", 0) > 0:
        print(f"\n  NY Rule4 Focus (persistent least-negative outlier):")
        print(f"    Count:      {ny['rule4_count']}")
        if ny.get("rule4_wr_pct") is not None:
            print(f"    WR:         {ny['rule4_wr_pct']:.1f}%")
        if ny.get("rule4_avg_q_entry") is not None:
            print(f"    Avg Q:      {ny['rule4_avg_q_entry']:+.4f}")
        if ny.get("rule4_avg_net_pnl") is not None:
            print(f"    Avg PnL:    {ny['rule4_avg_net_pnl']:+.4f}")

    # Cross-boundary
    cbe = result.get("cross_boundary_exploration_trades", 0)
    print(f"\n  Cross-boundary exploration trades: {cbe}")

    # Survivability
    surv = result.get("survivability_classification", {})
    total_exp = surv.get("total_exploration_trades", 0)
    if total_exp > 0:
        print(f"\n  ── Survivability Classification ──")
        print(f"  Total exploration trades: {total_exp}")
        for cat in (
            "EXPLORATION_RECOVERY", "EXPLORATION_POSITIVE",
            "EXPLORATION_NEGATIVE", "EXPLORATION_NOISE", "EXPLORATION_UNRESOLVED",
        ):
            cnt = surv.get(cat, 0)
            pct = cnt / total_exp * 100 if total_exp else 0
            bar = "█" * min(int(pct / 5), 20)
            print(f"  {cat:<26}: {cnt:>4}  ({pct:.0f}%)  {bar}")

    # Longitudinal
    ld = result.get("longitudinal_dynamics", {})
    if ld:
        print(f"\n  ── Longitudinal Dynamics ──")
        print(f"  Exploration share:       {ld.get('explore_share', 0):.1%}")
        print(f"  Rule4 dependency ratio:  {ld.get('rule4_dependency_ratio', 0):.1%}")
        sc = ld.get("survival_rate_correlation_vs_exploration")
        print(f"  Survival-rate corr:      {f'{sc:+.4f}' if sc is not None else '—'}")

        if verbose:
            r10 = ld.get("rolling_10_trade_windows_last5", [])
            if r10:
                print(f"\n  Rolling 10-trade windows (last 5):")
                for w in r10:
                    wr = f"{w['explore_wr_pct']:.1f}%" if w.get("explore_wr_pct") is not None else "—"
                    print(f"    [end={w['window_end']:>3}] share={w['explore_share_pct']:.1f}%  wr={wr}")
            r25 = ld.get("rolling_25_trade_windows_last5", [])
            if r25:
                print(f"\n  Rolling 25-trade windows (last 5):")
                for w in r25:
                    wr = f"{w['explore_wr_pct']:.1f}%" if w.get("explore_wr_pct") is not None else "—"
                    print(f"    [end={w['window_end']:>3}] share={w['explore_share_pct']:.1f}%  wr={wr}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploration economic survivability analyzer")
    parser.add_argument("--db",      default=str(DEFAULT_DB_PATH),
                        help="Path to data_lake.db")
    parser.add_argument("--symbol",  default="",
                        help="Filter by symbol (empty = all)")
    parser.add_argument("--session", default="",
                        help="Filter trades by origin_session (e.g. NY)")
    parser.add_argument("--type",    default="",
                        dest="explore_type",
                        help="Filter by explore_type (e.g. RULE4_MIN_EXPLORE)")
    parser.add_argument("--limit",   default=2000, type=int,
                        help="Max trades to read from DataLake")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.exploration_economics import compute_exploration_economics

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.explore_type:
        trades = [
            t for t in trades
            if (t.get("exploration_origin") or {}).get("explore_type", "") == args.explore_type
        ]

    result = compute_exploration_economics(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

"""
FTD-TF-SURVIV — Timeframe Economics Comparator

Reads persisted trade data directly (no live engine required) and produces:

  1. Side-by-side 1m / 5m / 15m economics comparison
  2. Fee drag reduction across timeframes
  3. Alpha persistence category (5 research categories)
  4. NY session survivability by timeframe
  5. Rule4 and exploration survivability by timeframe

Shadow 5m and 15m values are HYPOTHETICAL projections. See scope_note in output.

Usage:
    python tools/analyze_timeframe_survivability.py
    python tools/analyze_timeframe_survivability.py --json
    python tools/analyze_timeframe_survivability.py --session NY
    python tools/analyze_timeframe_survivability.py --verbose
    python tools/analyze_timeframe_survivability.py --db path/to/data_lake.db
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


# ── Formatters ────────────────────────────────────────────────────────────────

def _pct(v: float | None, decimals: int = 1) -> str:
    return f"{v:.{decimals}f}%" if v is not None else "—"

def _val(v: float | None, decimals: int = 4) -> str:
    return f"{v:+.{decimals}f}" if v is not None else "—"

def _score(v: int | None) -> str:
    return f"{v}/100" if v is not None else "—"

def _hold(v: float | None) -> str:
    if v is None:
        return "—"
    if v < 60:
        return f"{v:.0f}s"
    return f"{v/60:.1f}m"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 76
    print(f"\n{'='*W}")
    print("  FTD-TF-SURVIV — Timeframe Economics Comparator")
    print(f"{'='*W}")

    total = result.get("total_trades", 0)
    print(f"\n  Total trades:  {total}")
    if result.get("note"):
        print(f"  {result['note']}")
        print(f"\n{'='*W}\n")
        return

    print(f"\n  Scope: {result.get('scope_note', '')[:90]}...")

    # ── Timeframe Comparison Table ──────────────────────────────────────────
    tc = result.get("timeframe_comparison", {})
    s1  = tc.get("1m",  {})
    s5  = tc.get("5m",  {})
    s15 = tc.get("15m", {})

    print(f"\n  ── Timeframe Economics Comparison ──")
    print(f"  {'Metric':<26} {'1m (actual)':>14} {'5m (shadow)':>14} {'15m (shadow)':>14}")
    print(f"  {'-'*68}")

    rows = [
        ("Net expectancy (USDT)",  _val(s1.get("net_expectancy"),  4),
                                   _val(s5.get("net_expectancy"),  4),
                                   _val(s15.get("net_expectancy"), 4)),
        ("Gross expectancy (USDT)", _val(s1.get("gross_expectancy"),  4),
                                    _val(s5.get("gross_expectancy"),  4),
                                    _val(s15.get("gross_expectancy"), 4)),
        ("Win rate",               _pct(s1.get("win_rate_pct")),
                                   _pct(s5.get("win_rate_pct")),
                                   _pct(s15.get("win_rate_pct"))),
        ("Fee drag (mean)",        _pct(s1.get("fee_drag_mean_pct")),
                                   _pct(s5.get("fee_drag_mean_pct")),
                                   _pct(s15.get("fee_drag_mean_pct"))),
        ("Payoff asymmetry",       _val(s1.get("payoff_asymmetry"),  3) + "×",
                                   _val(s5.get("payoff_asymmetry"),  3) + "×",
                                   _val(s15.get("payoff_asymmetry"), 3) + "×"),
        ("Avg hold",               _hold(s1.get("avg_hold_sec")),
                                   _hold(s5.get("avg_hold_sec")),
                                   _hold(s15.get("avg_hold_sec"))),
        ("Survivability score",    _score(s1.get("survivability_score")),
                                   _score(s5.get("survivability_score")),
                                   _score(s15.get("survivability_score"))),
        ("Tier",                   s1.get("survivability_tier",  "—"),
                                   s5.get("survivability_tier",  "—"),
                                   s15.get("survivability_tier", "—")),
    ]
    for label, v1, v5, v15 in rows:
        print(f"  {label:<26} {v1:>14} {v5:>14} {v15:>14}")

    # ── Alpha Persistence ───────────────────────────────────────────────────
    cat = result.get("alpha_persistence_category", "—")
    print(f"\n  ── Alpha Persistence Category ──")
    print(f"  {cat}")
    category_meanings = {
        "TF_ALPHA_PERSISTENT":   "Alpha survives at all timeframes (score ≥ 75 everywhere)",
        "TIMEFRAME_CONSISTENT":  "Survivable across all TFs (score ≥ 50 everywhere)",
        "MICROSTRUCTURE_ERODED": "Fails at 1m but survives at 5m or 15m — 1m friction hypothesis confirmed",
        "HIGHER_TF_RECOVERY":    "Expectancy improves at higher TF — partial recovery signal",
        "TF_NOISE_COLLAPSE":     "Edge absent at all timeframes — no signal present",
    }
    print(f"  → {category_meanings.get(cat, '')}")

    # ── Fee Drag Reduction ──────────────────────────────────────────────────
    fdr = result.get("fee_drag_reduction", {})
    if fdr:
        print(f"\n  ── Fee Drag Reduction ──")
        print(f"  1m: {_pct(fdr.get('1m_mean_pct'))}  →  "
              f"5m: {_pct(fdr.get('5m_shadow_mean_pct'))}  →  "
              f"15m: {_pct(fdr.get('15m_shadow_mean_pct'))}")
        d5  = fdr.get("1m_to_5m_delta_pct")
        d15 = fdr.get("1m_to_15m_delta_pct")
        if d5 is not None:
            print(f"  1m→5m improvement:  {d5:+.2f}%  |  1m→15m improvement: "
                  f"{d15:+.2f}%" if d15 is not None else f"  1m→5m improvement: {d5:+.2f}%")

    # ── NY Session Comparison ───────────────────────────────────────────────
    ny = result.get("ny_session_comparison", {})
    print(f"\n  ── NY Session Comparison ──")
    if "note" in ny:
        print(f"  {ny['note']}")
    else:
        ny_cnt = ny.get("trade_count", 0)
        print(f"  NY trades: {ny_cnt}")
        print(f"  {'TF':<5} {'Net Exp':>10} {'Fee Drag':>10} {'WR':>7} {'Score':>8} {'Tier':>10}")
        print(f"  {'-'*50}")
        for tf in ("1m", "5m", "15m"):
            row = ny.get(tf, {})
            lbl = f"{tf} {'(shadow)' if tf != '1m' else '(actual)'}"
            print(f"  {lbl:<14} {_val(row.get('net_expectancy'),4):>10} "
                  f"{_pct(row.get('fee_drag_mean_pct')):>10} "
                  f"{_pct(row.get('win_rate_pct')):>7} "
                  f"{_score(row.get('survivability_score')):>8} "
                  f"{row.get('survivability_tier','—'):>10}")

    # ── Rule4 / Exploration Comparisons ────────────────────────────────────
    if verbose:
        for label_key, section_label in (
            ("rule4_comparison",       "Rule4 (RULE4_MIN_EXPLORE) Comparison"),
            ("exploration_comparison", "All Exploration Comparison"),
        ):
            sec = result.get(label_key, {})
            print(f"\n  ── {section_label} ──")
            if "note" in sec:
                print(f"  {sec['note']}")
            else:
                cnt = sec.get("trade_count", 0)
                print(f"  Trades: {cnt}")
                print(f"  {'TF':<5} {'Net Exp':>10} {'Fee Drag':>10} {'WR':>7} {'Score':>8}")
                print(f"  {'-'*42}")
                for tf in ("1m", "5m", "15m"):
                    row = sec.get(tf, {})
                    lbl = f"{tf} {'(shadow)' if tf != '1m' else '(actual)'}"
                    print(f"  {lbl:<14} {_val(row.get('net_expectancy'),4):>10} "
                          f"{_pct(row.get('fee_drag_mean_pct')):>10} "
                          f"{_pct(row.get('win_rate_pct')):>7} "
                          f"{_score(row.get('survivability_score')):>8}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Timeframe economics comparator — research instrumentation"
    )
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

    from core.timeframe_economics import compute_timeframe_survivability

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]

    result = compute_timeframe_survivability(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

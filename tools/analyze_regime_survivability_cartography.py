"""
FTD-REGIME-SURVIV — Regime Survivability Cartography Analyzer

Reads persisted trade data directly (no live engine required) and produces:

  1. Alpha landscape category (6 research labels)
  2. Survivability heatmap: top + bottom scoring regions
  3. Per-regime economics at 1m / 5m / 15m
  4. Regime × session survival matrix
  5. Exploration dependence by regime
  6. NY regime analysis
  7. Regime-transition survivability
  8. Ontology alignment economics

Shadow 5m/15m values are HYPOTHETICAL projections — see scope_note in output.

Usage:
    python tools/analyze_regime_survivability_cartography.py
    python tools/analyze_regime_survivability_cartography.py --json
    python tools/analyze_regime_survivability_cartography.py --verbose
    python tools/analyze_regime_survivability_cartography.py --db path/to/data_lake.db
    python tools/analyze_regime_survivability_cartography.py --session NY
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

def _pct(v: float | None, d: int = 1) -> str:
    return f"{v:.{d}f}%" if v is not None else "—"

def _val(v: float | None, d: int = 4) -> str:
    return f"{v:+.{d}f}" if v is not None else "—"

def _score(v: int | None) -> str:
    return f"{v}/100" if v is not None else "—"

def _cell_row(label: str, m: dict, w: int = 24) -> str:
    if "note" in m or "error" in m:
        return f"  {label:<{w}} (insufficient data)"
    return (
        f"  {label:<{w}} "
        f"exp={_val(m.get('net_expectancy'), 4):>10}  "
        f"drag={_pct(m.get('fee_drag_mean_pct')):>7}  "
        f"wr={_pct(m.get('win_rate_pct')):>6}  "
        f"score={_score(m.get('survivability_score')):>8}  "
        f"[{m.get('survivability_tier','—')}]"
    )


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 80
    print(f"\n{'='*W}")
    print("  FTD-REGIME-SURVIV — Regime Survivability Cartography")
    print(f"{'='*W}")

    total = result.get("total_trades", 0)
    print(f"\n  Total trades: {total}")
    if result.get("note"):
        print(f"  {result['note']}")
        print(f"\n{'='*W}\n")
        return

    print(f"  Scope: {result.get('scope_note','')[:88]}...")

    # ── Cartography Category ────────────────────────────────────────────────
    cat = result.get("cartography_category", "—")
    category_meanings = {
        "ALPHA_DESERT":           "No survivable structure detected at any dimension",
        "MICROSTRUCTURE_TRAP":    "Alpha fails at 1m but recovers at higher timeframes",
        "SESSION_ALPHA_POCKET":   "Survivable alpha localized to a specific session",
        "REGIME_ALPHA_CLUSTER":   "Survivable alpha localized to a specific regime",
        "EXPLORATION_DEPENDENT":  "Alpha survives only under exploration override",
        "STABLE_ALPHA_REGION":    "Broad survivable structure across multiple dimensions",
    }
    print(f"\n  ── Alpha Landscape Category ──")
    print(f"  {cat}")
    print(f"  → {category_meanings.get(cat, '')}")

    # ── Heatmap (top regions) ───────────────────────────────────────────────
    heatmap = result.get("survivability_heatmap", [])
    print(f"\n  ── Survivability Heatmap (top life-zones, sorted by score) ──")
    if not heatmap:
        print("  No cells met minimum trade count threshold.")
    else:
        print(f"  {'Region':<36} {'Score':>7} {'Tier':>10} {'Net Exp':>10} {'WR':>7}")
        print(f"  {'-'*72}")
        top = heatmap[:10] if verbose else heatmap[:6]
        for h in top:
            shadow_tag = "⁵ᵐ" if h.get("timeframe") == "5m" else "¹⁵ᵐ" if h.get("timeframe") == "15m" else ""
            region = f"{h['region']}{shadow_tag}"
            print(f"  {region:<36} {_score(h.get('score')):>7} "
                  f"{h.get('tier','—'):>10} "
                  f"{_val(h.get('net_expectancy'), 4):>10} "
                  f"{_pct(h.get('win_rate_pct')):>7}")

    # ── Bottom regions ──────────────────────────────────────────────────────
    if heatmap and verbose:
        desert = result.get("alpha_desert_regions", [])
        if desert:
            print(f"\n  ── Alpha Desert Zones (lowest scoring) ──")
            print(f"  {'Region':<36} {'Score':>7} {'Net Exp':>10}")
            print(f"  {'-'*55}")
            for h in desert[:5]:
                print(f"  {h['region']:<36} {_score(h.get('score')):>7} "
                      f"{_val(h.get('net_expectancy'), 4):>10}")

    # ── Regime Matrix ───────────────────────────────────────────────────────
    rm = result.get("regime_matrix", {})
    if rm:
        print(f"\n  ── Per-Regime Economics (1m actual) ──")
        print(f"  {'Regime':<24} {'Net Exp':>10}  {'Fee Drag':>7}  {'WR':>6}  {'Score':>8}  Tier")
        print(f"  {'-'*70}")
        for regime, m in rm.items():
            print(_cell_row(regime, m))

    # ── Regime × TF Matrix ──────────────────────────────────────────────────
    if verbose:
        rtm = result.get("regime_tf_matrix", {})
        if rtm:
            print(f"\n  ── Regime × Timeframe Matrix ──")
            for regime, tf_dict in rtm.items():
                print(f"\n  [{regime}]")
                for tf, m in tf_dict.items():
                    tag = " (shadow)" if tf != "1m" else " (actual)"
                    print(_cell_row(f"  {tf}{tag}", m, 30))

    # ── Regime × Session ────────────────────────────────────────────────────
    if verbose:
        rsm = result.get("regime_session_matrix", {})
        if rsm:
            print(f"\n  ── Regime × Session Matrix ──")
            for regime, sessions in rsm.items():
                print(f"\n  [{regime}]")
                for sess, m in sessions.items():
                    print(_cell_row(f"  {sess}", m, 12))

    # ── NY Regime Analysis ──────────────────────────────────────────────────
    ny = result.get("ny_regime_analysis", {})
    print(f"\n  ── NY Session Regime Analysis ──")
    if isinstance(ny, dict) and "note" in ny:
        print(f"  {ny['note']}")
    elif isinstance(ny, dict):
        for regime, tf_dict in ny.items():
            if isinstance(tf_dict, dict):
                print(f"\n  NY [{regime}]")
                for tf, m in tf_dict.items():
                    tag = " (shadow)" if tf != "1m" else " (actual)"
                    print(_cell_row(f"    {tf}{tag}", m, 18))

    # ── Exploration Dependence ──────────────────────────────────────────────
    expl = result.get("exploration_dependence", {})
    if expl:
        print(f"\n  ── Exploration Dependence ──")
        for etype, m in expl.items():
            print(_cell_row(etype, m))

    # ── Regime Transition ───────────────────────────────────────────────────
    if verbose:
        rt = result.get("regime_transition_survivability", {})
        if rt:
            print(f"\n  ── Regime-Transition Survivability ──")
            print(f"  Transition trades: {rt.get('transition_trade_count', 0)}  |  "
                  f"Stable: {rt.get('stable_trade_count', 0)}")
            if "transition_metrics" in rt:
                print(_cell_row("  Transition", rt["transition_metrics"]))
            if "stable_metrics" in rt:
                print(_cell_row("  Stable-regime", rt["stable_metrics"]))
            if "transition_note" in rt:
                print(f"  {rt['transition_note']}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regime survivability cartography — research instrumentation"
    )
    parser.add_argument("--db",      default=str(DEFAULT_DB_PATH),
                        help="Path to data_lake.db")
    parser.add_argument("--symbol",  default="",
                        help="Filter by symbol (empty = all)")
    parser.add_argument("--session", default="",
                        help="Filter by origin_session (e.g. NY)")
    parser.add_argument("--regime",  default="",
                        help="Filter by regime (e.g. MEAN_REVERTING)")
    parser.add_argument("--limit",   default=2000, type=int,
                        help="Max trades to read from DataLake")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.regime_cartography import compute_regime_survivability_cartography

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    result = compute_regime_survivability_cartography(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

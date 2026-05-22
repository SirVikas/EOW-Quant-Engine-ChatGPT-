"""
FTD-CIL — Protected Counterfactual Intervention Laboratory Analyzer

Reads persisted trade data (no live engine required) and runs all 8
intervention profiles against the historical trade stream, producing:

  1. Intervention ranking by net expectancy delta
  2. Per-intervention classification (BENEFICIAL_ADAPTATION, COSMETIC_STABILITY, …)
  3. Survivability and opportunity density impact analysis
  4. Ontology stabilization diagnostics
  5. Cognitive overfitting detection
  6. Replay confidence scores

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/counterfactual-interventions

Usage:
    python tools/analyze_counterfactual_interventions.py
    python tools/analyze_counterfactual_interventions.py --json
    python tools/analyze_counterfactual_interventions.py --verbose
    python tools/analyze_counterfactual_interventions.py --db path/to/data_lake.db
    python tools/analyze_counterfactual_interventions.py --session NY
    python tools/analyze_counterfactual_interventions.py --regime TRENDING
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

def _badge(classification: str) -> str:
    return {
        "BENEFICIAL_ADAPTATION":  "[  BENEFICIAL  ]",
        "COSMETIC_STABILITY":     "[ COSMETIC     ]",
        "OPPORTUNITY_COLLAPSE":   "[!!OPP COLLAPSE]",
        "FRAGILE_OPTIMIZATION":   "[ FRAGILE OPT  ]",
        "ONTOLOGY_STABILIZATION": "[ ONTOL STAB   ]",
        "COGNITIVE_OVERFITTING":  "[!!COG OVERFIT ]",
        "INSUFFICIENT_DATA":      "[ INSUFFICIENT ]",
    }.get(classification, f"[{classification[:13]:^15}]")


def _conf_badge(tier: str) -> str:
    return {"HIGH": "[HIGH ]", "MODERATE": "[MOD  ]", "LOW": "[LOW  ]",
            "INSUFFICIENT": "[INSUF]"}.get(tier, f"[{tier[:5]:^5}]")


def _pct(v) -> str:
    if v is None: return "   —   "
    return f"{v:+.1f}%"


def _val(v, d=4) -> str:
    if v is None: return "    —    "
    return f"{v:+.{d}f}"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 82
    print(f"\n{'='*W}")
    print("  FTD-CIL — Protected Counterfactual Intervention Laboratory")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    if "note" in result:
        print(f"\n  {result['note']}")
        print(f"  Total trades: {result.get('total_trades', 0)}")
        print(f"\n{'='*W}\n")
        return

    total = result.get("total_trades", 0)
    print(f"\n  Total trades in replay window: {total}")

    # ── Baseline ─────────────────────────────────────────────────────────────
    b = result.get("baseline", {})
    print(f"\n  ── Baseline Economics (unmodified replay) ──")
    print(f"  Net expectancy:   {_val(b.get('net_expectancy'), 4)}")
    print(f"  Survivability:    {b.get('survivability_score', '—')}/100  [{b.get('survivability_tier', '—')}]")
    print(f"  Win rate:         {_pct(b.get('win_rate_pct'))}")
    print(f"  Fee drag:         {_pct(b.get('fee_drag_mean_pct'))}")
    print(f"  Plasticity proxy: {b.get('plasticity_proxy', 0):.4f} bits")
    print(f"  Ontology drift:   {b.get('ontology_drift_proxy', 0):.1f}")

    # ── Intervention Ranking ─────────────────────────────────────────────────
    ranking = result.get("intervention_ranking", [])
    print(f"\n  ── Intervention Ranking (by net expectancy delta) ──")
    print(f"  {'Intervention':<34} {'Conf':>6} {'NE Δ':>10} {'Surv Δ':>8} {'Opp% Δ':>8} Classification")
    print(f"  {'-'*78}")
    for entry in ranking:
        name   = entry["intervention"]
        idata  = result.get("interventions", {}).get(name, {})
        conf   = idata.get("replay_confidence", {})
        deltas = entry
        print(
            f"  {name:<34} "
            f"{_conf_badge(conf.get('tier','?')):>6} "
            f"{_val(deltas.get('net_expectancy_delta'), 4):>10} "
            f"{_val(deltas.get('survivability_delta'), 1):>8} "
            f"{_pct(deltas.get('opportunity_density_delta_pct')):>8}  "
            f"{_badge(idata.get('classification',''))}"
        )

    # ── Detection Summary ────────────────────────────────────────────────────
    print(f"\n  ── Detection Summary ──")
    flags = {
        "Beneficial adaptation detected": result.get("beneficial_adaptation_detected"),
        "Opportunity collapse detected":  result.get("opportunity_collapse_detected"),
        "Ontology stabilization detected": result.get("ontology_stabilization_detected"),
        "Cognitive overfitting detected": result.get("cognitive_overfitting_detected"),
    }
    for label, val in flags.items():
        symbol = "YES" if val else "no"
        print(f"  {label:<38} {symbol}")

    top = result.get("top_intervention")
    if top:
        print(f"\n  Top intervention: {top}")

    # ── Per-intervention detail ──────────────────────────────────────────────
    if verbose:
        interventions = result.get("interventions", {})
        print(f"\n  ── Per-Intervention Detail ──")
        for name, data in interventions.items():
            cls    = data.get("classification", "")
            count  = data.get("trade_count", 0)
            deltas = data.get("deltas", {})
            conf   = data.get("replay_confidence", {})
            print(f"\n  [{name}]  {_badge(cls)}  trades={count}  conf={_conf_badge(conf.get('tier','?'))}")
            print(f"    {data.get('description', '')}")
            print(f"    NE Δ={_val(deltas.get('net_expectancy_delta'),4)}  "
                  f"Surv Δ={_val(deltas.get('survivability_delta'),1)}  "
                  f"Drag Δ={_pct(deltas.get('fee_drag_delta'))}  "
                  f"WR Δ={_pct(deltas.get('win_rate_delta'))}")
            print(f"    Opp% Δ={_pct(deltas.get('opportunity_density_delta_pct'))}  "
                  f"Plasticity Δ={deltas.get('plasticity_delta', '—')!s:.6}  "
                  f"Drift Δ={_val(deltas.get('ontology_drift_delta'),1)}  "
                  f"Explore Δ={_pct(deltas.get('exploration_dependence_delta'))}")
            if "error" in data:
                print(f"    ERROR: {data['error']}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Counterfactual intervention laboratory — research instrumentation"
    )
    parser.add_argument("--db",      default=str(DEFAULT_DB_PATH),
                        help="Path to data_lake.db")
    parser.add_argument("--symbol",  default="",
                        help="Filter by symbol (empty = all)")
    parser.add_argument("--session", default="",
                        help="Pre-filter by origin_session (e.g. NY)")
    parser.add_argument("--regime",  default="",
                        help="Pre-filter by regime (e.g. TRENDING)")
    parser.add_argument("--limit",   default=2000, type=int,
                        help="Max trades to read from DataLake")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.counterfactual_lab import compute_counterfactual_interventions

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = compute_counterfactual_interventions(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

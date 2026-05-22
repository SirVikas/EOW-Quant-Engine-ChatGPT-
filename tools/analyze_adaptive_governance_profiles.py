"""
FTD-GAGS — Guarded Adaptive Governance Simulator CLI

Reads persisted trade data (no live engine required) and runs all 6 compound
policy stacks against all 6 governance profiles, producing:

  1. Per-compound trade retention and baseline delta summary
  2. Per-profile governance scores and best compound recommendation
  3. Governance outcome classification per profile
  4. Cross-profile conflict detection
  5. Regime specialization risk (HHI)
  6. Overfitting risk analysis
  7. Consensus compound (plurality vote)

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/adaptive-governance-simulator

Usage:
    python tools/analyze_adaptive_governance_profiles.py
    python tools/analyze_adaptive_governance_profiles.py --json
    python tools/analyze_adaptive_governance_profiles.py --verbose
    python tools/analyze_adaptive_governance_profiles.py --db path/to/data_lake.db
    python tools/analyze_adaptive_governance_profiles.py --session NY
    python tools/analyze_adaptive_governance_profiles.py --regime TRENDING
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

def _cls_badge(cls: str) -> str:
    return {
        "GOVERNANCE_STABLE":         "[ STABLE       ]",
        "ECONOMIC_AUTHORITARIANISM": "[!!ECON AUTH   ]",
        "PLASTICITY_OVEREXPANSION":  "[ PLAST OVEREX ]",
        "ONTOLOGY_FRAGMENTATION":    "[!!ONTOL FRAG  ]",
        "ECOLOGICAL_COLLAPSE":       "[!!ECOL COLLAP ]",
        "BALANCED_ADAPTATION":       "[  BALANCED    ]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _tier_badge(tier: str) -> str:
    return {
        "HIGH":     "[HIGH ]",
        "MODERATE": "[MOD  ]",
        "LOW":      "[LOW  ]",
        "MINIMAL":  "[MIN  ]",
    }.get(tier, f"[{tier[:5]:^5}]")


def _pct(v) -> str:
    if v is None:
        return "   —   "
    return f"{v:+.1f}%"


def _val(v, d: int = 4) -> str:
    if v is None:
        return "    —    "
    return f"{v:+.{d}f}"


def _score(v) -> str:
    if v is None:
        return " — "
    return f"{v:.1f}"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 86
    print(f"\n{'='*W}")
    print("  FTD-GAGS — Guarded Adaptive Governance Simulator & Policy Arbitration Engine")
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
    print(f"\n  ── Baseline Economics ──")
    print(f"  Net expectancy:   {_val(b.get('net_expectancy'), 4)}")
    print(f"  Survivability:    {b.get('survivability_score', '—')}/100")
    print(f"  Plasticity proxy: {b.get('plasticity_proxy', 0):.4f} bits")
    print(f"  Ontology drift:   {b.get('ontology_drift_proxy', 0):.1f}")
    print(f"  Win rate:         {_pct(b.get('win_rate_pct'))}")

    # ── Compound Stacks ───────────────────────────────────────────────────────
    stacks = result.get("compound_stacks", {})
    print(f"\n  ── Compound Policy Stacks ──")
    print(f"  {'Compound':<28} {'Trades':>7} {'Retention':>10}  Interventions")
    print(f"  {'-'*75}")
    for name, data in stacks.items():
        count     = data.get("trade_count", 0)
        retention = f"{count/max(total,1)*100:.1f}%" if total else "—"
        i_list    = ", ".join(data.get("interventions", []))
        print(f"  {name:<28} {count:>7} {retention:>10}  [{i_list}]")

    # ── Governance Profile Arbitration ────────────────────────────────────────
    profiles = result.get("governance_profiles", {})
    print(f"\n  ── Governance Profile Arbitration ──")
    print(f"  {'Profile':<28} {'Score':>6} {'Best Compound':<24} Classification")
    print(f"  {'-'*82}")
    for gp_name, gp_data in profiles.items():
        score   = gp_data.get("best_score", 0.0)
        best    = gp_data.get("best_compound", "—")
        cls     = gp_data.get("governance_classification", "")
        print(
            f"  {gp_name:<28} {_score(score):>6} "
            f"{(best or '—'):<24} {_cls_badge(cls)}"
        )

    # ── Risk Summary ──────────────────────────────────────────────────────────
    print(f"\n  ── Risk Summary ──")
    rsr = result.get("regime_specialization_risk", {})
    ofr = result.get("overfitting_risk", {})
    print(f"  Regime specialization risk: {_score(rsr.get('score'))}  "
          f"{_tier_badge(rsr.get('tier','?'))}  HHI×100")
    print(f"  Overfitting risk:           {_score(ofr.get('score'))}  "
          f"{_tier_badge(ofr.get('tier','?'))}")

    # ── Conflict Detection ────────────────────────────────────────────────────
    ca = result.get("conflict_analysis", {})
    print(f"\n  ── Conflict Detection ──")
    print(f"  Conflicts detected:         {ca.get('conflict_count', 0)}")
    print(f"  Consensus reachable:        {'YES' if ca.get('consensus_reachable') else 'no'}")
    for conflict in ca.get("conflicts", []):
        p1, p2 = conflict["profiles"]
        ctype  = conflict["conflict_type"]
        c1 = conflict["choices"].get(p1, "?")
        c2 = conflict["choices"].get(p2, "?")
        print(f"    [{ctype}]  {p1} → {c1}  vs  {p2} → {c2}")

    consensus = result.get("consensus_compound")
    if consensus:
        print(f"\n  Consensus compound: {consensus}")
    else:
        print(f"\n  Consensus compound: (no plurality — profiles disagree)")

    # ── Per-profile verbose detail ────────────────────────────────────────────
    if verbose:
        print(f"\n  ── Per-Profile Detail ──")
        for gp_name, gp_data in profiles.items():
            cls = gp_data.get("governance_classification", "")
            print(f"\n  [{gp_name}]  {_cls_badge(cls)}")
            print(f"    {gp_data.get('description', '')}")
            print(f"    Weights: { {k: v for k, v in gp_data.get('weights', {}).items() if v > 0} }")
            scores = gp_data.get("compound_scores", {})
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            print(f"    Compound ranking:")
            for cname, cscore in ranked:
                marker = " ← best" if cname == gp_data.get("best_compound") else ""
                print(f"      {cname:<28} {cscore:.1f}{marker}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Adaptive governance simulator — research instrumentation"
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

    from core.governance_simulator import compute_adaptive_governance

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = compute_adaptive_governance(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

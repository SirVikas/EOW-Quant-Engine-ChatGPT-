"""
FTD-GRVL — Guarded Reality Verification Layer CLI

Reads persisted trade data (no live engine required), runs the full
divergence analytics stack, and produces a pilot-readiness assessment:

  1. Pilot state (PAPER_ONLY → CONSTITUTION_LOCKDOWN)
  2. Reality-alignment classification
  3. Divergence metrics (8 dimensions, 0–100)
  4. Pilot survivability score
  5. Simulation-reality confidence
  6. Research-only recommendations (all auto_authorized=False)
  7. Audit entry summary
  8. Hard pilot constitutional principles verification

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/reality-verification

Usage:
    python tools/analyze_reality_verification.py
    python tools/analyze_reality_verification.py --json
    python tools/analyze_reality_verification.py --verbose
    python tools/analyze_reality_verification.py --db path/to/data_lake.db
    python tools/analyze_reality_verification.py --session NY
    python tools/analyze_reality_verification.py --regime TRENDING
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

def _pilot_badge(state: str) -> str:
    return {
        "PAPER_ONLY":             "[ PAPER ONLY   ]",
        "SHADOW_MARKET":          "[ SHADOW MKT   ]",
        "MICRO_PILOT":            "[ MICRO PILOT  ]",
        "HUMAN_CONFIRM_REQUIRED": "[!!HUMAN CONFIRM]",
        "AUTO_DISABLED":          "[!!AUTO DISABLED]",
        "CONSTITUTION_LOCKDOWN":  "[!!LOCKDOWN    ]",
    }.get(state, f"[{state[:13]:^13}]")


def _cls_badge(cls: str) -> str:
    return {
        "REALITY_ALIGNED":          "[ ALIGNED      ]",
        "FRICTION_EROSION":         "[!FRICTION     ]",
        "LIQUIDITY_FRAGILE":        "[!LIQ FRAGILE  ]",
        "LATENCY_SENSITIVE":        "[!LATENCY SENS ]",
        "MICROSTRUCTURE_DEPENDENT": "[!!MICROSTR DEP]",
        "PILOT_NOT_RECOMMENDED":    "[!!NO PILOT    ]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _conf_badge(tier: str) -> str:
    return {
        "HIGH":         "[ HIGH    ]",
        "ADEQUATE":     "[ ADEQUATE]",
        "LOW":          "[!LOW     ]",
        "INSUFFICIENT": "[!!INSUF  ]",
    }.get(tier, f"[{tier[:8]:^8}]")


def _surv_badge(tier: str) -> str:
    return {
        "STRONG":   "[ STRONG  ]",
        "ADEQUATE": "[ ADEQUATE]",
        "MARGINAL": "[!MARGINAL]",
        "WEAK":     "[!!WEAK   ]",
    }.get(tier, f"[{tier[:8]:^8}]")


def _risk_tier_badge(tier: str) -> str:
    return {
        "HIGH":         "[HIGH ]",
        "MODERATE":     "[MOD  ]",
        "LOW":          "[LOW  ]",
        "MINIMAL":      "[MIN  ]",
        "STRONG":       "[STRG ]",
        "ADEQUATE":     "[OK-  ]",
        "MARGINAL":     "[MARG ]",
        "WEAK":         "[WEAK ]",
        "FRAGILE":      "[FRAG ]",
        "CRITICAL":     "[CRIT ]",
        "SENSITIVE":    "[SENS ]",
        "ROBUST":       "[ROBU ]",
        "RESILIENT":    "[RES  ]",
        "NEUTRAL":      "[NEUT ]",
        "MILD":         "[MILD ]",
    }.get(tier, f"[{tier[:5]:^5}]")


def _priority_badge(p: str) -> str:
    return {
        "CRITICAL": "[CRIT]",
        "HIGH":     "[HIGH]",
        "MEDIUM":   "[MED ]",
        "LOW":      "[LOW ]",
    }.get(p, f"[{p[:4]:^4}]")


def _score(v) -> str:
    if v is None:
        return " — "
    return f"{v:.1f}"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 88
    print(f"\n{'='*W}")
    print("  FTD-GRVL — Guarded Reality Verification Layer & Pilot Readiness Assessment")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Pilot Status ──────────────────────────────────────────────────────────
    pilot_state = result.get("pilot_state", "—")
    pilot_desc  = result.get("pilot_state_description", "")
    cls         = result.get("reality_classification", "—")
    surv        = result.get("pilot_survivability", {})
    conf        = result.get("simulation_reality_confidence", {})

    print(f"\n  ── Pilot Status ──")
    print(f"  Pilot state:              {_pilot_badge(pilot_state)}  {pilot_state}")
    print(f"  Reality classification:   {_cls_badge(cls)}  {cls}")
    print(f"  Pilot survivability:      {_score(surv.get('score'))}/100  {_surv_badge(surv.get('tier','?'))}")
    print(f"  Reality confidence:       {_score(conf.get('score'))}/100  {_conf_badge(conf.get('tier','?'))}")
    print(f"  Trades analyzed:          {result.get('total_trades', 0)}")
    print(f"  Description: {pilot_desc}")

    # ── Baseline Economics ────────────────────────────────────────────────────
    econ = result.get("baseline_economics", {})
    if econ:
        print(f"\n  ── Baseline Economics ──")
        print(f"  Net expectancy:     {_score(econ.get('net_expectancy'))}")
        print(f"  Gross expectancy:   {_score(econ.get('gross_expectancy'))}")
        print(f"  Total fees:         {_score(econ.get('total_fees'))}")
        print(f"  Total slippage:     {_score(econ.get('total_slippage'))}")
        print(f"  Fee/gross ratio:    {_score(econ.get('fee_gross_ratio'))}%")
        print(f"  Slip/gross ratio:   {_score(econ.get('slip_gross_ratio'))}%")

    # ── Divergence Metrics ────────────────────────────────────────────────────
    dm = result.get("divergence_metrics", {})
    print(f"\n  ── Reality Divergence Metrics ──")
    print(f"  {'Metric':<36} {'Score':>6} Tier")
    print(f"  {'-'*62}")
    metric_labels = {
        "fill_divergence":            "Fill Divergence",
        "slippage_divergence":        "Slippage Divergence",
        "latency_divergence":         "Latency Divergence",
        "liquidity_survivability":    "Liquidity Survivability",
        "spread_fragility":           "Spread Fragility",
        "market_impact_sensitivity":  "Market Impact Sensitivity",
    }
    for key, label in metric_labels.items():
        data = dm.get(key, {})
        score = data.get("score", 0.0)
        tier  = data.get("tier", "?")
        print(f"  {label:<36} {_score(score):>6} {_risk_tier_badge(tier)}")

    # ── Spread Stress Scenarios ───────────────────────────────────────────────
    sf = dm.get("spread_fragility", {})
    scenarios = sf.get("scenarios", {})
    if scenarios and verbose:
        print(f"\n  ── Spread Stress Scenarios ──")
        for mult, data in sorted(scenarios.items()):
            print(f"  {mult:>4}× spread: {data.get('survival_pct', 0):.1f}% trades survive"
                  f"  (net_expectancy: {_score(data.get('net_expectancy'))})")

    # ── Audit Entry ───────────────────────────────────────────────────────────
    ae = result.get("audit_entry", {})
    if ae:
        print(f"\n  ── Audit Entry ──")
        print(f"  Entry ID:             {ae.get('entry_id', '—')}")
        print(f"  Human approval req:   {'YES' if ae.get('human_approval_required') else 'no'}")
        print(f"  Auto-authorized:      {'!!! YES' if ae.get('auto_authorized') else 'no (constitutional)'}")
        print(f"  Immutable:            {'YES' if ae.get('immutable') else 'no'}")

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = result.get("recommendations", [])
    print(f"\n  ── Recommendations ({len(recs)}) ──")
    for rec in recs:
        prio   = rec.get("priority", "?")
        rtype  = rec.get("type", "?")
        action = rec.get("action_required", "?")
        auto   = rec.get("auto_authorized", "?")
        print(f"  {_priority_badge(prio)} [{rtype}]")
        print(f"    {rec.get('summary', '')}")
        print(f"    Action: {action}  |  Auto-authorized: {auto}")

    # ── Pilot Hard Principles ─────────────────────────────────────────────────
    if verbose:
        hp = result.get("pilot_hard_principles", {})
        print(f"\n  ── Pilot Hard Principles ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<38} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Guarded reality verification — pilot readiness assessment"
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

    from core.reality_verification import compute_reality_verification as _crv

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = _crv(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

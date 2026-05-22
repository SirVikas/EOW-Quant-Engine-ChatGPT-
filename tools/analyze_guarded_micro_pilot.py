"""
FTD-GMPD — Ultra-Guarded Micro Pilot Execution Doctrine CLI

Reads persisted trade data (no live engine required), runs the full
pilot governance analytics stack, and produces a constitutional
micro-pilot readiness assessment:

  1. Pilot state (PAPER_ONLY → CONSTITUTION_LOCKDOWN)
  2. Reality classification (REALITY_CONSISTENT → PILOT_LOCKDOWN_RECOMMENDED)
  3. Execution readiness (paper corpus quality)
  4. Reconciliation metrics (fill, slippage, latency, fee drag, hold economics)
  5. Confirmation chain integrity
  6. Kill-switch advisory
  7. Research-only recommendations (all auto_authorized=False)
  8. Pilot opportunity suggestion (human confirmation required)
  9. Audit entry summary
 10. Hard constitutional pilot principles verification

IMPORTANT: All output is research-only. No production state is modified.
The pilot ledger is session-scoped in memory — this CLI uses an empty
ledger (no execution reconciliation available offline).
For live diagnostics use GET /api/learning-intelligence/guarded-micro-pilot

Usage:
    python tools/analyze_guarded_micro_pilot.py
    python tools/analyze_guarded_micro_pilot.py --json
    python tools/analyze_guarded_micro_pilot.py --verbose
    python tools/analyze_guarded_micro_pilot.py --db path/to/data_lake.db
    python tools/analyze_guarded_micro_pilot.py --session NY
    python tools/analyze_guarded_micro_pilot.py --regime TRENDING
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
        "PAPER_ONLY":               "[ PAPER ONLY   ]",
        "SHADOW_OBSERVATION":       "[ SHADOW OBS   ]",
        "HUMAN_ARMED_MICRO":        "[ ARMED MICRO  ]",
        "SINGLE_CONFIRM_EXECUTION": "[ SINGLE CNFRM ]",
        "MANUAL_KILL_SWITCH":       "[!!KILL SWITCH ]",
        "CONSTITUTION_LOCKDOWN":    "[!!LOCKDOWN    ]",
    }.get(state, f"[{state[:13]:^13}]")


def _cls_badge(cls: str) -> str:
    return {
        "REALITY_CONSISTENT":         "[ CONSISTENT   ]",
        "EXECUTION_DRIFT":            "[!EXEC DRIFT   ]",
        "SLIPPAGE_COLLAPSE":          "[!!SLIP COLPSE ]",
        "LIQUIDITY_FAILURE":          "[!!LIQ FAILURE ]",
        "HUMAN_REVIEW_ESCALATION":    "[!!HMN ESCAL   ]",
        "PILOT_LOCKDOWN_RECOMMENDED": "[!!LOCKDOWN REC]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _surv_badge(tier: str) -> str:
    return {
        "STRONG":   "[ STRONG  ]",
        "ADEQUATE": "[ ADEQUATE]",
        "MARGINAL": "[!MARGINAL]",
        "WEAK":     "[!!WEAK   ]",
    }.get(tier, f"[{tier[:8]:^8}]")


def _read_badge(tier: str) -> str:
    return {
        "ADEQUATE":     "[ ADEQUATE  ]",
        "DEVELOPING":   "[ DEVELOPING]",
        "EARLY":        "[!EARLY     ]",
        "INSUFFICIENT": "[!!INSUF    ]",
    }.get(tier, f"[{tier[:10]:^10}]")


def _integrity_badge(integ: str) -> str:
    return {
        "INTACT":  "[ INTACT ]",
        "EMPTY":   "[ EMPTY  ]",
        "VIOLATED": "[!!VIOLAT]",
        "UNKNOWN": "[?UNKNOWN]",
    }.get(integ, f"[{integ[:7]:^7}]")


def _ks_badge(engage: bool) -> str:
    return "[!!ENGAGE]" if engage else "[ OK     ]"


def _tier_badge(tier: str) -> str:
    return {
        "MINIMAL":      "[MIN  ]",
        "LOW":          "[LOW  ]",
        "MODERATE":     "[MOD  ]",
        "HIGH":         "[HIGH ]",
        "CRITICAL":     "[CRIT ]",
        "INSUFFICIENT": "[INSUF]",
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
    print("  FTD-GMPD — Ultra-Guarded Micro Pilot Execution Doctrine")
    print("             & Human Confirmation Exchange Bridge")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Pilot Status ──────────────────────────────────────────────────────────
    pilot_state = result.get("pilot_state", "—")
    pilot_desc  = result.get("pilot_state_description", "")
    cls         = result.get("pilot_classification", "—")
    surv        = result.get("pilot_survivability", {})
    read        = result.get("execution_readiness", {})

    print(f"\n  ── Pilot Status ──")
    print(f"  Pilot state:           {_pilot_badge(pilot_state)}  {pilot_state}")
    print(f"  Classification:        {_cls_badge(cls)}  {cls}")
    print(f"  Pilot survivability:   {_score(surv.get('score'))}/100  {_surv_badge(surv.get('tier','?'))}")
    print(f"  Execution readiness:   {_score(read.get('score'))}/100  {_read_badge(read.get('tier','?'))}")
    print(f"  Trades analyzed:       {result.get('total_trades', 0)}")
    print(f"  Pilot ledger depth:    {result.get('pilot_ledger_depth', 0)}")
    print(f"  Description: {pilot_desc}")

    # ── Execution Readiness ───────────────────────────────────────────────────
    print(f"\n  ── Execution Readiness ──")
    print(f"  Net expectancy:      {_score(read.get('net_expectancy'))}")
    print(f"  Fee coverage:        {read.get('fee_coverage', 0.0):.1%}")
    print(f"  Slippage coverage:   {read.get('slippage_coverage', 0.0):.1%}")

    # ── Confirmation Chain ────────────────────────────────────────────────────
    chain = result.get("confirmation_chain_integrity", {})
    ks    = result.get("kill_switch_advisory", {})
    print(f"\n  ── Constitutional Safety ──")
    print(f"  Confirmation chain:    {_integrity_badge(chain.get('integrity','?'))}  "
          f"all_confirmed={chain.get('all_human_confirmed','?')}")
    print(f"  Unauthorized entries:  {chain.get('unauthorized_entries', 0)}")
    print(f"  Execution entries:     {chain.get('execution_entries', 0)}")
    print(f"  Kill-switch advisory:  {_ks_badge(ks.get('engage', False))}  "
          f"{ks.get('reason', '—')}")

    # ── Reconciliation Metrics ────────────────────────────────────────────────
    rm = result.get("reconciliation_metrics", {})
    print(f"\n  ── Execution Reconciliation Metrics ──")
    print(f"  {'Metric':<34} {'Score':>6} Tier        Samples")
    print(f"  {'-'*64}")
    metric_labels = {
        "fill_quality":                  "Fill Quality",
        "slippage_reconciliation":       "Slippage Reconciliation",
        "latency_reconciliation":        "Latency Reconciliation",
        "fee_drag_reconciliation":       "Fee Drag Reconciliation",
        "hold_economics_reconciliation": "Hold Economics Reconciliation",
    }
    for key, label in metric_labels.items():
        m     = rm.get(key, {})
        score = m.get("score", 0.0)
        tier  = m.get("tier", "?")
        n     = m.get("sample_count", 0)
        print(f"  {label:<34} {_score(score):>6} {_tier_badge(tier)}  {n}")

    # ── Pilot Opportunity ─────────────────────────────────────────────────────
    opp = result.get("pilot_opportunity", {})
    print(f"\n  ── Pilot Opportunity (Research Suggestion) ──")
    print(f"  Available:             {'YES — requires human confirmation' if opp.get('available') else 'NO'}")
    print(f"  Expected net expect:   {_score(opp.get('expected_net_expectancy'))}")
    print(f"  Expected slippage:     {_score(opp.get('expected_slippage_pct'))}%")
    print(f"  Recommended exposure:  {opp.get('recommended_exposure', '—')}")
    print(f"  Auto-authorized:       {'!!! YES' if opp.get('auto_authorized') else 'no (constitutional)'}")
    print(f"  Human confirm req:     {'YES' if opp.get('human_confirmation_required') else 'no'}")

    # ── Audit Entry ───────────────────────────────────────────────────────────
    ae = result.get("audit_entry", {})
    if ae:
        print(f"\n  ── Audit Entry ──")
        print(f"  Entry ID:              {ae.get('entry_id', '—')}")
        print(f"  Entry type:            {ae.get('entry_type', '—')}")
        print(f"  Human approval req:    {'YES' if ae.get('human_approval_required') else 'no'}")
        print(f"  Auto-authorized:       {'!!! YES' if ae.get('auto_authorized') else 'no (constitutional)'}")
        print(f"  Immutable:             {'YES' if ae.get('immutable') else 'no'}")

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

    # ── Hard Principles ───────────────────────────────────────────────────────
    if verbose:
        hp = result.get("pilot_hard_principles", {})
        print(f"\n  ── Hard Constitutional Pilot Principles ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<38} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Guarded micro-pilot doctrine — constitutional pilot readiness assessment"
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

    from core.micro_pilot_doctrine import compute_guarded_micro_pilot as _cgmp

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    # Offline: no session-scoped pilot ledger available — pass empty list
    result = _cgmp(trades, pilot_ledger=[])

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

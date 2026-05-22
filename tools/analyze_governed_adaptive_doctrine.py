"""
FTD-GADD — Guarded Adaptive Deployment Doctrine CLI

Reads persisted trade data (no live engine required), runs the full analytics
stack (CIL + GAGS + offline proxy state), and produces a constitutional
governance assessment:

  1. Governance state (OBSERVATION_ONLY → CONSTITUTION_LOCKDOWN)
  2. Constitutional risk diagnostics (6 metrics, 0–100)
  3. Constitutional classification
  4. Constitutional stability score
  5. Research-only recommendations (all auto_authorized=False)
  6. Audit entry summary
  7. Hard constitutional principles verification

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/governed-adaptive-doctrine

Usage:
    python tools/analyze_governed_adaptive_doctrine.py
    python tools/analyze_governed_adaptive_doctrine.py --json
    python tools/analyze_governed_adaptive_doctrine.py --verbose
    python tools/analyze_governed_adaptive_doctrine.py --db path/to/data_lake.db
    python tools/analyze_governed_adaptive_doctrine.py --session NY
    python tools/analyze_governed_adaptive_doctrine.py --regime TRENDING
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

def _state_badge(state: str) -> str:
    return {
        "OBSERVATION_ONLY":      "[ OBSERVING    ]",
        "SANDBOX_REPLAY":        "[ SANDBOX      ]",
        "HUMAN_REVIEW_REQUIRED": "[!!HUMAN REVIEW]",
        "GUARDED_EXPERIMENT":    "[ GUARDED EXP  ]",
        "AUTO_DISABLED":         "[!!AUTO DISABLED]",
        "CONSTITUTION_LOCKDOWN": "[!!LOCKDOWN    ]",
    }.get(state, f"[{state[:13]:^13}]")


def _cls_badge(cls: str) -> str:
    return {
        "CONSTITUTIONALLY_STABLE":  "[ STABLE       ]",
        "OVERSIGHT_DEPENDENT":      "[ OVERSIGHT DEP]",
        "ADAPTIVE_DRIFT_RISK":      "[!!DRIFT RISK  ]",
        "RECOMMENDATION_OVERREACH": "[!!OVERREACH   ]",
        "GOVERNANCE_FRAGMENTATION": "[!!FRAGMENTED  ]",
        "LOCKDOWN_RECOMMENDED":     "[!!LOCKDOWN REC]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _stab_badge(tier: str) -> str:
    return {
        "STRONG":   "[ STRONG  ]",
        "ADEQUATE": "[ ADEQUATE]",
        "WEAKENED": "[!WEAKENED]",
        "CRITICAL": "[!!CRITICAL]",
    }.get(tier, f"[{tier[:8]:^8}]")


def _risk_tier_badge(tier: str) -> str:
    return {
        "HIGH":     "[HIGH ]",
        "MODERATE": "[MOD  ]",
        "LOW":      "[LOW  ]",
        "MINIMAL":  "[MIN  ]",
        "INTACT":   "[OK   ]",
        "ADEQUATE": "[OK-  ]",
        "DEGRADED": "[DEGR ]",
        "COMPROMISED": "[COMP ]",
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
    print("  FTD-GADD — Guarded Adaptive Deployment Doctrine & Human Override Constitution")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Governance State ──────────────────────────────────────────────────────
    gov_state = result.get("governance_state", "—")
    gov_desc  = result.get("governance_state_description", "")
    cls       = result.get("constitutional_classification", "—")
    cs        = result.get("constitutional_stability", {})

    print(f"\n  ── Constitutional Status ──")
    print(f"  Governance state:         {_state_badge(gov_state)}  {gov_state}")
    print(f"  Classification:           {_cls_badge(cls)}  {cls}")
    print(f"  Constitutional stability: {_score(cs.get('score'))}/100  {_stab_badge(cs.get('tier','?'))}")
    print(f"  Description: {gov_desc}")

    # ── Risk Diagnostics ──────────────────────────────────────────────────────
    rd = result.get("risk_diagnostics", {})
    print(f"\n  ── Constitutional Risk Diagnostics ──")
    print(f"  {'Metric':<32} {'Score':>6} Tier")
    print(f"  {'-'*60}")
    metric_labels = {
        "autonomous_drift_risk":         "Autonomous Drift Risk",
        "overfitting_escalation_risk":   "Overfitting Escalation Risk",
        "governance_instability":        "Governance Instability",
        "human_override_integrity":      "Human Override Integrity",
        "recommendation_confidence":     "Recommendation Confidence",
        "sandbox_production_divergence": "Sandbox-Production Divergence",
    }
    for key, label in metric_labels.items():
        data = rd.get(key, {})
        score = data.get("score", 0.0)
        tier  = data.get("tier", "?")
        print(f"  {label:<32} {_score(score):>6} {_risk_tier_badge(tier)}")

    # ── Audit Ledger ──────────────────────────────────────────────────────────
    depth     = result.get("audit_ledger_depth", 0)
    integrity = result.get("audit_ledger_integrity", {})
    ae        = result.get("audit_entry", {})
    print(f"\n  ── Audit Ledger ──")
    print(f"  Session audit depth:  {depth} entries")
    print(f"  Ledger integrity:     {integrity.get('integrity', '—')}")
    print(f"  Autonomous actions:   {integrity.get('autonomous_actions', 0)}")
    if ae:
        print(f"  Current entry ID:     {ae.get('entry_id', '—')}")
        print(f"  Human approval req:   {'YES' if ae.get('human_approval_required') else 'no'}")
        print(f"  Auto-authorized:      {'!!! YES' if ae.get('auto_authorized') else 'no (constitutional)'}")

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = result.get("recommendations", [])
    print(f"\n  ── Recommendations ({len(recs)}) ──")
    for rec in recs:
        prio    = rec.get("priority", "?")
        rtype   = rec.get("type", "?")
        action  = rec.get("action_required", "?")
        auto    = rec.get("auto_authorized", "?")
        print(f"  {_priority_badge(prio)} [{rtype}]")
        print(f"    {rec.get('summary', '')}")
        print(f"    Action: {action}  |  Auto-authorized: {auto}")

    # ── Human Override Constitution ───────────────────────────────────────────
    if verbose:
        hp = result.get("human_override_constitution", {})
        print(f"\n  ── Human Override Constitution ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<38} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Governed adaptive doctrine — constitutional governance assessment"
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

    from core.counterfactual_lab   import compute_counterfactual_interventions as _cci
    from core.governance_simulator import compute_adaptive_governance          as _cag
    from core.deployment_doctrine  import compute_governed_adaptive_doctrine   as _cgad

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    # Build proxy state from offline trade data (no live engine access)
    cil_result = _cci(trades)
    gag_result = _cag(trades)

    # Derive lightweight RL proxy from trade exploration fractions
    explore_count = sum(
        1 for t in trades
        if (t.get("exploration_origin") or {}).get("was_exploration_trade")
    )
    explore_ratio  = round(explore_count / max(len(trades), 1), 3)
    win_count      = sum(1 for t in trades if (t.get("net_pnl") or 0.0) > 0)
    profitable_pct = round(win_count / max(len(trades), 1), 3)

    state = {
        "counterfactual":  cil_result,
        "governance":      gag_result,
        "memory_pressure": {},   # offline: no live memory state available
        "rl": {
            "explore_ratio":  explore_ratio,
            "profitable_pct": profitable_pct,
            "total_contexts": 0,
        },
        "audit_ledger": [],
    }

    result = _cgad(state)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

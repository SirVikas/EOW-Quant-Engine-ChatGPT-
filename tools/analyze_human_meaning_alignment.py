"""
FTD-HMAO — Constitutional Human Meaning Alignment
& Purpose Integrity Observatory CLI

Reads persisted trade data (no live engine required), segments the full
trade history, and produces a constitutional human meaning alignment assessment:

  1. Alignment classification (HUMAN_ALIGNED → ALIGNMENT_LOCKDOWN_RISK)
  2. Alignment integrity score (0–100)
  3. 8 alignment integrity metrics
  4. Alignment lineage (early/mid/late epoch health labels + trajectory)
  5. Research-only recommendations (all auto_authorized=False)
  6. Audit entry summary
  7. Hard constitutional alignment principles

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/human-meaning-alignment

Usage:
    python tools/analyze_human_meaning_alignment.py
    python tools/analyze_human_meaning_alignment.py --json
    python tools/analyze_human_meaning_alignment.py --verbose
    python tools/analyze_human_meaning_alignment.py --db path/to/data_lake.db
    python tools/analyze_human_meaning_alignment.py --session NY
    python tools/analyze_human_meaning_alignment.py --regime TRENDING
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

def _load_trades(db_path: Path, symbol: str = "", limit: int = 5000) -> list[dict]:
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
        "HUMAN_ALIGNED":              "[ ALIGNED     ]",
        "INTERPRETABILITY_WEAKENING": "[!INTERP      ]",
        "METRIC_DETACHMENT_RISK":     "[!!DETACHMENT ]",
        "PURPOSE_DRIFT_ACCELERATION": "[!!DRIFT      ]",
        "HUMAN_ACCOUNTABILITY_DECAY": "[!!ACCOUNT    ]",
        "ALIGNMENT_LOCKDOWN_RISK":    "[!!LOCKDOWN   ]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _int_badge(tier: str) -> str:
    return {
        "HUMAN_ALIGNED": "[ ALIGNED    ]",
        "ADEQUATE":      "[ ADEQUATE   ]",
        "VULNERABLE":    "[!VULNERABLE ]",
        "CRITICAL":      "[!!CRITICAL  ]",
    }.get(tier, f"[{tier[:10]:^10}]")


def _traj_badge(t: str) -> str:
    return {
        "IMPROVING": "[↑ IMPROV]",
        "STABLE":    "[→ STABLE]",
        "DECLINING": "[↓ DECLIN]",
        "UNKNOWN":   "[? UNKNWN]",
    }.get(t, f"[?{t[:5]:^5}]")


def _health_badge(h: str) -> str:
    return {
        "ALIGNED":  "[ALIGN]",
        "EMERGING": "[EMRG ]",
        "DRIFTING": "[DRFT ]",
    }.get(h, f"[{h[:5]:^5}]")


def _tier_badge(tier: str) -> str:
    return {
        "INTERPRETABLE": "[INTERP]",
        "EXPLAINABLE":   "[EXPLN ]",
        "TRACEABLE":     "[TRACE ]",
        "READABLE":      "[READB ]",
        "ALIGNED":       "[ALIGN ]",
        "CONTINUOUS":    "[CONT  ]",
        "STABLE":        "[STABL ]",
        "RETAINED":      "[RETND ]",
        "ADEQUATE":      "[ADEQ  ]",
        "LIMITED":       "[LMTD  ]",
        "PARTIAL":       "[PART  ]",
        "DEGRADED":      "[DEGD  ]",
        "MODERATE":      "[MOD   ]",
        "WEAKENING":     "[WEAK  ]",
        "COMPROMISED":   "[COMP  ]",
        "DRIFTING":      "[DRFT  ]",
        "SHIFTING":      "[SHFT  ]",
        "OPAQUE":        "[OPAQ  ]",
        "UNTRACEABLE":   "[UNTR  ]",
        "UNREADABLE":    "[UNRD  ]",
        "DETACHED":      "[DTCH  ]",
        "DEGRADING":     "[DEGRD ]",
        "LOST":          "[LOST  ]",
        "INSUFFICIENT":  "[INSUF ]",
    }.get(tier, f"[{tier[:6]:^6}]")


def _score(v) -> str:
    if v is None:
        return " — "
    return f"{v:.1f}"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 88
    print(f"\n{'='*W}")
    print("  FTD-HMAO — Constitutional Human Meaning Alignment")
    print("             & Purpose Integrity Observatory")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Alignment Status ──────────────────────────────────────────────────────
    cls   = result.get("alignment_classification", "—")
    desc  = result.get("classification_description", "")
    integ = result.get("alignment_integrity_score", {})
    total = result.get("total_trades", 0)

    print(f"\n  ── Alignment Status ──")
    print(f"  Classification:         {_cls_badge(cls)}  {cls}")
    print(f"  Alignment integrity:    {_score(integ.get('score'))}/100  {_int_badge(integ.get('tier','?'))}")
    print(f"  Trades analyzed:        {total}")
    print(f"  Description: {desc}")

    # ── Alignment Metrics ─────────────────────────────────────────────────────
    am = result.get("alignment_metrics", {})
    print(f"\n  ── Alignment Integrity Metrics ──")
    print(f"  {'Metric':<48} {'Score':>6} Tier")
    print(f"  {'-'*68}")
    metric_labels = {
        "human_interpretability":          "Human Interpretability (regime/session/exploration)",
        "recommendation_explainability":   "Recommendation Explainability (fee/slip/PnL diversity)",
        "causal_traceability":             "Causal Traceability (ID + timestamp coverage)",
        "governance_readability":          "Governance Readability (regime/session/explore)",
        "optimization_drift":              "Optimization Drift (wr extremity + explore deficit)",
        "human_accountability_continuity": "Human Accountability Continuity (audit chain)",
        "purpose_alignment_stability":     "Purpose Alignment Stability (temporal drift)",
        "human_value_retention":           "Human Value Retention (economic field coverage)",
    }
    for key, label in metric_labels.items():
        m     = am.get(key, {})
        score = m.get("score", 0.0)
        tier  = m.get("tier", "?")
        print(f"  {label:<48} {_score(score):>6} {_tier_badge(tier)}")

    # ── Alignment Lineage ─────────────────────────────────────────────────────
    lin    = result.get("alignment_lineage", {})
    epochs = lin.get("epochs", {})
    if epochs:
        print(f"\n  ── Alignment Lineage ──")
        print(f"  Trajectory: {_traj_badge(lin.get('alignment_trajectory','?'))}  "
              f"({lin.get('total_trades',0)} total trades)")
        print(f"  {'Epoch':<8}  {'Trades':>6}  {'Regime':<14} {'Explore':>7} "
              f"{'Win%':>5} {'Health':<8}")
        print(f"  {'-'*60}")
        for name in ("early", "mid", "late"):
            ep = epochs.get(name)
            if not ep:
                continue
            print(f"  {name:<8}  {ep.get('trade_count',0):>6}  "
                  f"{ep.get('dominant_regime','?'):<14} "
                  f"{ep.get('exploration_ratio',0):.3f}  "
                  f"{ep.get('win_rate',0)*100:>5.1f}  "
                  f"{_health_badge(ep.get('alignment_health','?'))}")

    # ── Audit Entry ───────────────────────────────────────────────────────────
    ae = result.get("audit_entry", {})
    if ae:
        print(f"\n  ── Audit Entry ──")
        print(f"  Entry ID:              {ae.get('entry_id', '—')}")
        print(f"  Human approval req:    {'YES' if ae.get('human_approval_required') else 'no'}")
        print(f"  Auto-authorized:       {'!!! YES' if ae.get('auto_authorized') else 'no (constitutional)'}")
        print(f"  Immutable:             {'YES' if ae.get('immutable') else 'no'}")

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = result.get("recommendations", [])
    print(f"\n  ── Recommendations ({len(recs)}) ──")
    _prio_badge = {
        "CRITICAL": "[CRIT]", "HIGH": "[HIGH]",
        "MEDIUM": "[MED ]", "LOW": "[LOW ]",
    }
    for rec in recs:
        prio  = rec.get("priority", "?")
        badge = _prio_badge.get(prio, f"[{prio[:4]:^4}]")
        print(f"  {badge} [{rec.get('type', '?')}]")
        print(f"    {rec.get('summary', '')}")
        print(f"    Action: {rec.get('action_required','?')}  |  Auto-authorized: {rec.get('auto_authorized','?')}")

    # ── Hard Constitutional Alignment Principles ──────────────────────────────
    if verbose:
        hp = result.get("alignment_hard_principles", {})
        print(f"\n  ── Hard Constitutional Alignment Principles ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<50} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Human meaning alignment observatory — constitutional purpose integrity assessment"
    )
    parser.add_argument("--db",      default=str(DEFAULT_DB_PATH),
                        help="Path to data_lake.db")
    parser.add_argument("--symbol",  default="",
                        help="Filter by symbol (empty = all)")
    parser.add_argument("--session", default="",
                        help="Pre-filter by origin_session (e.g. NY)")
    parser.add_argument("--regime",  default="",
                        help="Pre-filter by regime (e.g. TRENDING)")
    parser.add_argument("--limit",   default=5000, type=int,
                        help="Max trades to read from DataLake (default 5000)")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.alignment_observatory import compute_human_meaning_alignment as _chma

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = _chma(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

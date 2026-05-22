"""
FTD-EIOD — Constitutional Scientific Method Doctrine
& Epistemic Integrity Observatory CLI

Reads persisted trade data (no live engine required), segments the full
trade history, and produces a constitutional epistemic integrity assessment:

  1. Epistemic classification (SCIENTIFICALLY_HEALTHY → EPISTEMIC_LOCKDOWN_RISK)
  2. Epistemic integrity score (0–100)
  3. 8 epistemic integrity metrics
  4. Epistemic lineage (early/mid/late epoch health labels + trajectory)
  5. Research-only recommendations (all auto_authorized=False)
  6. Audit entry summary
  7. Hard constitutional epistemic principles

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/epistemic-integrity-observatory

Usage:
    python tools/analyze_epistemic_integrity.py
    python tools/analyze_epistemic_integrity.py --json
    python tools/analyze_epistemic_integrity.py --verbose
    python tools/analyze_epistemic_integrity.py --db path/to/data_lake.db
    python tools/analyze_epistemic_integrity.py --session NY
    python tools/analyze_epistemic_integrity.py --regime TRENDING
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
        "SCIENTIFICALLY_HEALTHY":        "[ HEALTHY     ]",
        "EVIDENCE_INSUFFICIENCY":        "[!EVIDENCE    ]",
        "IDEOLOGICAL_SELF_CONFIRMATION": "[!!IDEOLOGICAL]",
        "CONTRADICTION_SUPPRESSION":     "[!!CONTRAD    ]",
        "FALSIFICATION_FAILURE":         "[!!FALSIF     ]",
        "EPISTEMIC_LOCKDOWN_RISK":       "[!!LOCKDOWN   ]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _int_badge(tier: str) -> str:
    return {
        "SCIENTIFICALLY_HEALTHY": "[ HEALTHY    ]",
        "ADEQUATE":               "[ ADEQUATE   ]",
        "VULNERABLE":             "[!VULNERABLE ]",
        "CRITICAL":               "[!!CRITICAL  ]",
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
        "HEALTHY":  "[HLTHY]",
        "EMERGING": "[EMRG ]",
        "RIGID":    "[RIGID]",
    }.get(h, f"[{h[:5]:^5}]")


def _tier_badge(tier: str) -> str:
    return {
        "SUFFICIENT":  "[SUFF ]",
        "MARGINAL":    "[MRGN ]",
        "SPARSE":      "[SPAR ]",
        "INSUFFICIENT":"[INSUF]",
        "HIGH":        "[HIGH ]",
        "ADEQUATE":    "[ADEQ ]",
        "LOW":         "[LOW  ]",
        "DEEP":        "[DEEP ]",
        "SHALLOW":     "[SHLL ]",
        "TOLERANT":    "[TOLR ]",
        "MODERATE":    "[MOD  ]",
        "RIGID":       "[RGID ]",
        "SUPPRESSED":  "[SUPR ]",
        "EXTINCT":     "[EXT  ]",
        "ACTIVE":      "[ACT  ]",
        "PASSIVE":     "[PASV ]",
        "DORMANT":     "[DORM ]",
        "FLEXIBLE":    "[FLEX ]",
        "LOCKED":      "[LOCK ]",
        "PLASTIC":     "[PLAS ]",
        "CRYSTALLIZED":"[CRYS ]",
    }.get(tier, f"[{tier[:5]:^5}]")


def _score(v) -> str:
    if v is None:
        return " — "
    return f"{v:.1f}"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 88
    print(f"\n{'='*W}")
    print("  FTD-EIOD — Constitutional Scientific Method Doctrine")
    print("             & Epistemic Integrity Observatory")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Epistemic Status ──────────────────────────────────────────────────────
    cls   = result.get("epistemic_classification", "—")
    desc  = result.get("classification_description", "")
    integ = result.get("epistemic_integrity_score", {})
    total = result.get("total_trades", 0)

    print(f"\n  ── Epistemic Status ──")
    print(f"  Classification:         {_cls_badge(cls)}  {cls}")
    print(f"  Epistemic integrity:    {_score(integ.get('score'))}/100  {_int_badge(integ.get('tier','?'))}")
    print(f"  Trades analyzed:        {total}")
    print(f"  Description: {desc}")

    # ── Epistemic Metrics ─────────────────────────────────────────────────────
    em = result.get("epistemic_metrics", {})
    print(f"\n  ── Epistemic Integrity Metrics ──")
    print(f"  {'Metric':<44} {'Score':>6} Tier")
    print(f"  {'-'*64}")
    metric_labels = {
        "evidence_sufficiency":              "Evidence Sufficiency",
        "replay_statistical_confidence":     "Replay Statistical Confidence (CI width)",
        "governance_evidence_depth":         "Governance Evidence Depth",
        "contradiction_tolerance":           "Contradiction Tolerance (regime std)",
        "minority_hypothesis_survivability": "Minority Hypothesis Survivability",
        "falsification_rate":                "Falsification Rate (explore × volatility)",
        "consensus_rigidity":                "Consensus Rigidity (HHI)",
        "epistemic_plasticity":              "Epistemic Plasticity (belief updating)",
    }
    for key, label in metric_labels.items():
        m     = em.get(key, {})
        score = m.get("score", 0.0)
        tier  = m.get("tier", "?")
        print(f"  {label:<44} {_score(score):>6} {_tier_badge(tier)}")

    # ── Epistemic Lineage ─────────────────────────────────────────────────────
    lin    = result.get("epistemic_lineage", {})
    epochs = lin.get("epochs", {})
    if epochs:
        print(f"\n  ── Epistemic Lineage ──")
        print(f"  Trajectory: {_traj_badge(lin.get('epistemic_trajectory','?'))}  "
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
                  f"{_health_badge(ep.get('epistemic_health','?'))}")

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

    # ── Hard Constitutional Epistemic Principles ──────────────────────────────
    if verbose:
        hp = result.get("epistemic_hard_principles", {})
        print(f"\n  ── Hard Constitutional Epistemic Principles ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<50} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Epistemic integrity observatory — constitutional scientific-method assessment"
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

    from core.epistemic_observatory import compute_epistemic_integrity as _cei

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = _cei(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

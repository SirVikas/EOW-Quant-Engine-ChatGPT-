"""
FTD-CKPD — Constitutional Knowledge Preservation & Catastrophic Recovery
Doctrine CLI

Reads persisted trade data (no live engine required), computes a constitutional
recovery and knowledge preservation assessment:

  1. Archive snapshot (field-coverage analysis across all trades)
  2. Recovery classification (CONSTITUTIONALLY_RECOVERABLE →
     RECOVERY_LOCKDOWN_RECOMMENDED)
  3. Recovery survivability score (0–100)
  4. 7 recovery metrics + constitutional continuity confidence
  5. 3-scenario catastrophic disruption analysis
  6. Recovery lineage (early/mid/late epoch summaries)
  7. Research-only recommendations (all auto_authorized=False)
  8. Audit entry summary
  9. Hard constitutional recovery principles

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/constitutional-recovery-observatory

Usage:
    python tools/analyze_constitutional_recovery.py
    python tools/analyze_constitutional_recovery.py --json
    python tools/analyze_constitutional_recovery.py --verbose
    python tools/analyze_constitutional_recovery.py --db path/to/data_lake.db
    python tools/analyze_constitutional_recovery.py --session NY
    python tools/analyze_constitutional_recovery.py --regime TRENDING
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
        "CONSTITUTIONALLY_RECOVERABLE":  "[ RECOVERABLE ]",
        "PARTIAL_MEMORY_FRAGMENTATION":  "[!PARTIAL MEM ]",
        "AUDIT_CONTINUITY_WEAKENING":    "[!AUDIT WEAK  ]",
        "GOVERNANCE_LINEAGE_DECAY":      "[!!GOV DECAY  ]",
        "CATASTROPHIC_KNOWLEDGE_RISK":   "[!!CATASTROPH ]",
        "RECOVERY_LOCKDOWN_RECOMMENDED": "[!!LOCKDOWN   ]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _surv_badge(tier: str) -> str:
    return {
        "RESILIENT":   "[ RESILIENT  ]",
        "RECOVERABLE": "[ RECOVERABL]",
        "FRAGILE":     "[!FRAGILE   ]",
        "CRITICAL":    "[!!CRITICAL ]",
    }.get(tier, f"[{tier[:10]:^10}]")


def _tier_badge(tier: str) -> str:
    return {
        "INTACT":        "[INTCT]",
        "ADEQUATE":      "[ADEQ ]",
        "DEGRADED":      "[DEGR ]",
        "FRAGMENTED":    "[FRAG ]",
        "CONTINUOUS":    "[CONT ]",
        "MODERATE":      "[MOD  ]",
        "GAPPED":        "[GAPD ]",
        "HIGH":          "[HIGH ]",
        "LOW":           "[LOW  ]",
        "INSUFFICIENT":  "[INSUF]",
        "COMPLETE":      "[CMPL ]",
        "PARTIAL":       "[PART ]",
        "MISSING":       "[MISS ]",
        "COMPROMISED":   "[COMP ]",
        "WEAKENED":      "[WEAK ]",
        "REDUNDANT":     "[REDN ]",
        "SPARSE":        "[SPAR ]",
        "CRITICAL":      "[CRIT ]",
        "CONFIDENT":     "[CONF ]",
        "UNCERTAIN":     "[UNCE ]",
    }.get(tier, f"[{tier[:5]:^5}]")


def _bool_badge(v: bool) -> str:
    return "YES" if v else "no "


def _score(v) -> str:
    if v is None:
        return " — "
    return f"{v:.1f}"


def _pct(v) -> str:
    return f"{v * 100:.1f}%"


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False) -> None:
    W = 88
    print(f"\n{'='*W}")
    print("  FTD-CKPD — Constitutional Knowledge Preservation")
    print("             & Catastrophic Recovery Doctrine")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Recovery Status ───────────────────────────────────────────────────────
    cls   = result.get("recovery_classification", "—")
    desc  = result.get("classification_description", "")
    surv  = result.get("recovery_survivability_score", {})
    total = result.get("total_trades", 0)

    print(f"\n  ── Recovery Status ──")
    print(f"  Classification:         {_cls_badge(cls)}  {cls}")
    print(f"  Recovery survivability: {_score(surv.get('score'))}/100  {_surv_badge(surv.get('tier','?'))}")
    print(f"  Trades analyzed:        {total}")
    print(f"  Description: {desc}")

    # ── Archive Snapshot ──────────────────────────────────────────────────────
    snap = result.get("archive_snapshot", {})
    if snap.get("total_trades", 0) > 0:
        print(f"\n  ── Archive Snapshot ──")
        print(f"  {'Field':<28} Coverage")
        print(f"  {'-'*42}")
        for field, label in [
            ("entry_ts_coverage",  "Entry timestamp"),
            ("exit_ts_coverage",   "Exit timestamp"),
            ("net_pnl_coverage",   "Net PnL"),
            ("gross_pnl_coverage", "Gross PnL"),
            ("fee_coverage",       "Fees"),
            ("slippage_coverage",  "Slippage"),
            ("regime_coverage",    "Regime"),
            ("session_coverage",   "Session"),
            ("explore_coverage",   "Exploration origin"),
            ("trade_id_coverage",  "Trade ID"),
        ]:
            print(f"  {label:<28} {_pct(snap.get(field, 0.0))}")
        print(f"  {'Distinct regimes':<28} {snap.get('distinct_regimes', 0)}")
        print(f"  {'Distinct sessions':<28} {snap.get('distinct_sessions', 0)}")
        print(f"  {'Dominant regime':<28} {snap.get('dominant_regime', '?')}")

    # ── Recovery Metrics ──────────────────────────────────────────────────────
    rm = result.get("recovery_metrics", {})
    print(f"\n  ── Recovery Metrics ──")
    print(f"  {'Metric':<42} {'Score':>6} Tier")
    print(f"  {'-'*64}")
    metric_labels = {
        "archive_integrity":               "Archive Integrity (fragmentation risk)",
        "ledger_continuity":               "Ledger Continuity (temporal gaps)",
        "reconstruction_confidence":       "Reconstruction Confidence (econ params)",
        "governance_lineage_completeness": "Governance Lineage Completeness",
        "audit_survivability":             "Audit Survivability (provenance)",
        "knowledge_redundancy":            "Knowledge Redundancy (diversity)",
        "constitutional_continuity_confidence": "Constitutional Continuity Confidence",
    }
    for key, label in metric_labels.items():
        m     = rm.get(key, {})
        score = m.get("score", 0.0)
        tier  = m.get("tier", "?")
        print(f"  {label:<42} {_score(score):>6} {_tier_badge(tier)}")

    # ── Catastrophic Scenario Analysis ────────────────────────────────────────
    sa = result.get("scenario_analysis", {})
    if sa:
        print(f"\n  ── Catastrophic Scenario Analysis ──")
        scenario_labels = {
            "fifty_percent_data_loss":        "50% DataLake loss",
            "eighteen_month_temporal_gap":    "18-month temporal gap",
            "governance_metadata_corruption": "Governance metadata corruption",
        }
        for key, label in scenario_labels.items():
            s = sa.get(key, {})
            recon = "YES" if s.get("reconstructible") else "no"
            conf  = _score(s.get("confidence"))
            print(f"  {label:<38}  Reconstructible: {recon:3}  Confidence: {conf}/100")

    # ── Recovery Lineage ──────────────────────────────────────────────────────
    lin = result.get("recovery_lineage", {})
    epochs = lin.get("epochs", {})
    if epochs:
        print(f"\n  ── Recovery Lineage ──")
        print(f"  Dominant governance ideology: {lin.get('dominant_governance_ideology', '?')}")
        print(f"  {'Epoch':<8}  {'Trades':>6}  {'Regime':<14} {'Explore':>7} {'NE':>8} "
              f"{'FeeCov':>6} {'Viability':<12}")
        print(f"  {'-'*70}")
        for epoch_name in ("early", "mid", "late"):
            ep = epochs.get(epoch_name)
            if not ep:
                continue
            print(f"  {epoch_name:<8}  {ep.get('trade_count',0):>6}  "
                  f"{ep.get('dominant_regime','?'):<14} "
                  f"{ep.get('exploration_ratio',0):.3f}  "
                  f"{_score(ep.get('net_expectancy')):>8}  "
                  f"{_pct(ep.get('fee_coverage',0)):>6}  "
                  f"{ep.get('reconstruction_viability','?')}")

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
        prio = rec.get("priority", "?")
        badge = _prio_badge.get(prio, f"[{prio[:4]:^4}]")
        print(f"  {badge} [{rec.get('type', '?')}]")
        print(f"    {rec.get('summary', '')}")
        print(f"    Action: {rec.get('action_required','?')}  |  Auto-authorized: {rec.get('auto_authorized','?')}")

    # ── Hard Constitutional Recovery Principles ───────────────────────────────
    if verbose:
        hp = result.get("recovery_hard_principles", {})
        print(f"\n  ── Hard Constitutional Recovery Principles ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<50} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Constitutional recovery observatory — knowledge preservation assessment"
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

    from core.recovery_observatory import compute_constitutional_recovery as _ccr

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = _ccr(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

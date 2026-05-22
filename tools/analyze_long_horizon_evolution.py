"""
FTD-LHEO — Long-Horizon Constitutional Evolution Observatory CLI

Reads persisted trade data (no live engine required), segments the full
trade history into temporal eras, and produces a constitutional long-horizon
evolution assessment:

  1. Eras analysed + era-by-era cognitive snapshots
  2. Evolutionary classification (CONSTITUTIONALLY_RESILIENT → LONG_HORIZON_LOCKDOWN_RISK)
  3. Long-horizon stability score (0–100)
  4. 8 constitutional continuity metrics
  5. Cognitive lineage (early/mid/late era with trajectories)
  6. Research-only recommendations (all auto_authorized=False)
  7. Audit entry summary
  8. Hard constitutional evolution principles

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/long-horizon-evolution

Usage:
    python tools/analyze_long_horizon_evolution.py
    python tools/analyze_long_horizon_evolution.py --json
    python tools/analyze_long_horizon_evolution.py --verbose
    python tools/analyze_long_horizon_evolution.py --db path/to/data_lake.db
    python tools/analyze_long_horizon_evolution.py --session NY
    python tools/analyze_long_horizon_evolution.py --regime TRENDING
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
        "CONSTITUTIONALLY_RESILIENT":  "[ RESILIENT    ]",
        "IDEOLOGICAL_RIGIDIFICATION":  "[!IDEOLOGICAL  ]",
        "EXPLORATION_EXTINCTION":      "[!!EXPL EXTINCT]",
        "SURVIVABILITY_MONOCULTURE":   "[!!MONOCULTURE ]",
        "ADAPTIVE_MEMORY_DECAY":       "[!!MEM DECAY   ]",
        "LONG_HORIZON_LOCKDOWN_RISK":  "[!!LOCKDOWN    ]",
    }.get(cls, f"[{cls[:13]:^13}]")


def _stab_badge(tier: str) -> str:
    return {
        "RESILIENT":    "[ RESILIENT ]",
        "ADEQUATE":     "[ ADEQUATE  ]",
        "VULNERABLE":   "[!VULNERABLE]",
        "CRITICAL":     "[!!CRITICAL ]",
        "INSUFFICIENT": "[!!INSUF    ]",
    }.get(tier, f"[{tier[:10]:^10}]")


def _traj_badge(traj: str) -> str:
    return {
        "IMPROVING": "[↑ IMPROV]",
        "STABLE":    "[→ STABLE]",
        "DECLINING": "[↓ DECLIN]",
    }.get(traj, f"[?{traj[:5]:^5}]")


def _tier_badge(tier: str) -> str:
    return {
        "STABLE":          "[STBL ]",
        "MODERATE":        "[MOD  ]",
        "VOLATILE":        "[VOLA ]",
        "UNSTABLE":        "[UNST ]",
        "MINIMAL":         "[MIN  ]",
        "LOW":             "[LOW  ]",
        "HIGH":            "[HIGH ]",
        "CRITICAL":        "[CRIT ]",
        "DIVERSE":         "[DIV  ]",
        "CONCENTRATED":    "[CONC ]",
        "MONOCULTURE":     "[MONO ]",
        "HEALTHY":         "[OK   ]",
        "DECLINING":       "[DECL ]",
        "RAPID_DECAY":     "[RDCY ]",
        "EXTINCT":         "[EXT  ]",
        "HIGH_DIVERSITY":  "[HDIV ]",
        "LOW_DIVERSITY":   "[LDIV ]",
        "CRITICALLY_LOW":  "[CRIT ]",
        "INSUFFICIENT":    "[INSUF]",
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
    print("  FTD-LHEO — Long-Horizon Constitutional Evolution Observatory")
    print("             & Intergenerational Drift Doctrine")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    # ── Evolution Status ──────────────────────────────────────────────────────
    cls   = result.get("evolution_classification", "—")
    desc  = result.get("classification_description", "")
    stab  = result.get("long_horizon_stability", {})
    eras  = result.get("eras_analyzed", 0)
    total = result.get("total_trades", 0)

    print(f"\n  ── Evolution Status ──")
    print(f"  Classification:         {_cls_badge(cls)}  {cls}")
    print(f"  Long-horizon stability: {_score(stab.get('score'))}/100  {_stab_badge(stab.get('tier','?'))}")
    print(f"  Trades analyzed:        {total}  ({eras} era{'s' if eras != 1 else ''})")
    print(f"  Description: {desc}")

    # ── Era Snapshots ─────────────────────────────────────────────────────────
    snapshots = result.get("era_snapshots", [])
    if snapshots:
        print(f"\n  ── Era Snapshots ──")
        print(f"  {'Era':>3}  {'Trades':>6}  {'Regime':<14} {'Explore':>7} {'Win%':>5} "
              f"{'NE':>8} {'H-HHI':>6}")
        print(f"  {'-'*70}")
        for s in snapshots:
            print(f"  {s.get('era_index',0):>3}  {s.get('trade_count',0):>6}  "
                  f"{s.get('dominant_regime','?'):<14} "
                  f"{s.get('exploration_ratio',0):.3f}  "
                  f"{s.get('win_rate',0)*100:>5.1f}  "
                  f"{_score(s.get('net_expectancy')):>8}  "
                  f"{s.get('regime_hhi',0):>6.1f}")

    # ── Constitutional Continuity Metrics ──────────────────────────────────────
    em = result.get("evolution_metrics", {})
    print(f"\n  ── Constitutional Continuity Metrics ──")
    print(f"  {'Metric':<38} {'Score':>6} Tier")
    print(f"  {'-'*60}")
    metric_labels = {
        "constitutional_stability":          "Constitutional Stability (instability)",
        "drift_acceleration":                "Drift Acceleration",
        "governance_ideology_concentration": "Governance Ideology Concentration",
        "plasticity_half_life":              "Plasticity Half-Life (decay rate)",
        "exploration_extinction_risk":       "Exploration Extinction Risk",
        "survivability_monoculture_risk":    "Survivability Monoculture Risk",
        "cognitive_diversity_retention":     "Cognitive Diversity Loss",
        "long_horizon_replay_dependence":    "Long-Horizon Replay Dependence",
    }
    for key, label in metric_labels.items():
        m     = em.get(key, {})
        score = m.get("score", 0.0)
        tier  = m.get("tier", "?")
        print(f"  {label:<38} {_score(score):>6} {_tier_badge(tier)}")

    # ── Cognitive Lineage ─────────────────────────────────────────────────────
    lin = result.get("cognitive_lineage", {})
    if lin.get("eras", 0) >= 2:
        print(f"\n  ── Cognitive Lineage ──")
        traj = lin.get("trajectory", {})
        for metric, direction in traj.items():
            print(f"  {metric:<28} {_traj_badge(direction)}")
        if verbose:
            for label, era in [("Early", lin.get("early_era")), ("Mid", lin.get("mid_era")),
                                ("Late", lin.get("late_era"))]:
                if era:
                    print(f"\n  {label} era (index={era.get('era_index','?')}):")
                    print(f"    net_expectancy={_score(era.get('net_expectancy'))}  "
                          f"explore={era.get('exploration_ratio',0):.3f}  "
                          f"win={era.get('win_rate',0)*100:.1f}%  "
                          f"regime={era.get('dominant_regime','?')}")

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
    for rec in recs:
        prio   = rec.get("priority", "?")
        rtype  = rec.get("type", "?")
        action = rec.get("action_required", "?")
        auto   = rec.get("auto_authorized", "?")
        print(f"  {_priority_badge(prio)} [{rtype}]")
        print(f"    {rec.get('summary', '')}")
        print(f"    Action: {action}  |  Auto-authorized: {auto}")

    # ── Hard Constitutional Evolution Principles ───────────────────────────────
    if verbose:
        hp = result.get("evolution_hard_principles", {})
        print(f"\n  ── Hard Constitutional Evolution Principles ──")
        for principle, value in hp.items():
            symbol = "YES" if value else "no"
            print(f"  {principle:<42} {symbol}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Long-horizon evolution observatory — constitutional continuity assessment"
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
                        help="Max trades to read from DataLake (default 5000 for long-horizon coverage)")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.evolution_observatory import compute_long_horizon_evolution as _clhe

    trades = _load_trades(Path(args.db), symbol=args.symbol, limit=args.limit)

    if args.session:
        trades = [t for t in trades if t.get("origin_session", "") == args.session]
    if args.regime:
        trades = [t for t in trades if t.get("regime", "") == args.regime]

    if not trades:
        print(f"\nNo trades found — run the engine first to populate the DataLake.")
        return

    result = _clhe(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

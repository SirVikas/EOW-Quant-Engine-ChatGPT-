"""
FTD-ONTOLOGY-DRIFT — Memory Pressure & Ontology Drift Analyzer

Reads persisted trade data (no live engine required) and synthesizes a
synthetic state dict from trade-level proxies to produce:

  1. Cognitive state classification (6 research labels)
  2. Memory pressure diagnostics: negmem density, Q entropy, plasticity,
     fossilization risk
  3. Ontology drift heatmap: 5 pairwise belief comparisons
  4. Per-pair drift detail

NOTE: This tool operates in offline mode — it reconstructs proxy metrics
from trade records since live engine objects (RL Q-table, NegMem, PatternEngine)
are not available from a static DB. Drift scores derived here are APPROXIMATE.
For live diagnostics use GET /api/learning-intelligence/memory-pressure-dynamics.

Usage:
    python tools/analyze_memory_pressure_and_ontology_drift.py
    python tools/analyze_memory_pressure_and_ontology_drift.py --json
    python tools/analyze_memory_pressure_and_ontology_drift.py --verbose
    python tools/analyze_memory_pressure_and_ontology_drift.py --db path/to/data_lake.db
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

def _load_trades(db_path: Path, limit: int = 2000) -> list[dict]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur  = conn.execute(
            "SELECT data FROM trades ORDER BY ts ASC LIMIT ?", (limit,)
        )
        rows = [json.loads(r["data"]) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


# ── Proxy state builder ───────────────────────────────────────────────────────

def _build_proxy_state(trades: list[dict]) -> dict:
    """
    Reconstruct approximate memory-system belief metrics from closed trade records.

    Proxy mapping (offline — not the same as live engine state):
      RL profitable_pct   → fraction of trades with net_pnl > 0
      NegMem density      → fraction of trades with net_pnl < 0 (rollback proxy)
      Pattern formation   → trades with ≥20 samples not reachable from trade records;
                            use a placeholder (0 formed, 0 total)
      Ecology regimes     → win-rate per regime computed from trade records
      AlphaContext        → profitable/toxic context fraction from exploration_origin
    """
    if not trades:
        return {}

    profitable   = [t for t in trades if (t.get("net_pnl") or 0.0) > 0]
    losing       = [t for t in trades if (t.get("net_pnl") or 0.0) <= 0]
    total        = len(trades)

    rl_pct = len(profitable) / total if total > 0 else 0.0

    # Regime win-rate for ecology proxy
    from collections import defaultdict
    regime_groups: dict = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in trades:
        regime = t.get("regime", "UNKNOWN") or "UNKNOWN"
        regime_groups[regime]["total"] += 1
        if (t.get("net_pnl") or 0.0) > 0:
            regime_groups[regime]["wins"] += 1

    eco_regimes = {
        r: {
            "n_trades": d["total"],
            "win_rate": round(d["wins"] / d["total"], 3) if d["total"] > 0 else 0.0,
            "weight":   1.0 + (d["wins"] / d["total"] - 0.5) * 2 if d["total"] > 0 else 1.0,
        }
        for r, d in regime_groups.items()
    }

    # Regime avg Q proxy: positive if win_rate > 50%, negative otherwise
    regime_avg_q = {
        r: round((d["wins"] / d["total"] - 0.5) * 2, 3)
        for r, d in regime_groups.items()
        if d["total"] > 0
    }

    # AlphaContext proxy from exploration_origin
    explore_profitable = sum(
        1 for t in trades
        if (t.get("exploration_origin") or {}).get("was_exploration_trade") is True
        and (t.get("net_pnl") or 0.0) > 0
    )
    explore_total = max(sum(
        1 for t in trades
        if (t.get("exploration_origin") or {}).get("was_exploration_trade") is True
    ), 1)

    # Construct proxy NegMem count: losing trades without NegMem data
    nm_permanent = len(losing)
    nm_total     = max(total, 1)
    nm_entries   = [
        {
            "key_str": f"{t.get('regime','UNKNOWN')}|LOW|{t.get('symbol','UNKNOWN')}|proxy|LONG",
            "permanent": (t.get("net_pnl") or 0.0) <= 0,
            "rollbacks": 1,
            "score": 0.9,
        }
        for t in trades
    ]

    # Proxy Q values from per-trade gross_pnl (not a real Q-table)
    q_values   = [float(t.get("gross_pnl") or 0.0) for t in trades]
    q_velocities = [abs(float(t.get("net_pnl") or 0.0)) for t in trades]

    return {
        "rl": {
            "profitable_pct":  rl_pct,
            "total_contexts":  total,
            "q_values":        q_values,
            "q_velocities":    q_velocities,
            "toxic_count":     len(losing),
            "explore_ratio":   explore_profitable / explore_total,
            "regime_avg_q":    regime_avg_q,
        },
        "negmem": {
            "count":   {"permanent": nm_permanent, "temporary": 0, "total": nm_total},
            "entries": nm_entries,
        },
        "patterns": {
            "total_patterns":       0,
            "formed_patterns":      0,
            "formed_pattern_dicts": [],
        },
        "ecology": {"regimes": eco_regimes},
        "alpha_context": {
            "profitable_count": explore_profitable,
            "toxic_count":      explore_total - explore_profitable,
            "total_contexts":   explore_total,
        },
    }


# ── Formatters ────────────────────────────────────────────────────────────────

def _tier_badge(tier: str) -> str:
    return {
        "HIGH_DRIFT":     "[!!HIGH DRIFT]",
        "MODERATE_DRIFT": "[ MODERATE  ]",
        "LOW_DRIFT":      "[   LOW     ]",
        "ALIGNED":        "[  ALIGNED  ]",
        "HIGH":           "[  HIGH     ]",
        "MODERATE":       "[ MODERATE  ]",
        "LOW":            "[   LOW     ]",
        "CRITICAL":       "[ CRITICAL  ]",
        "MEDIUM":         "[  MEDIUM   ]",
        "MINIMAL":        "[  MINIMAL  ]",
    }.get(tier, f"[{tier:^12}]")


def _print_report(result: dict, verbose: bool = False) -> None:
    W = 80
    print(f"\n{'='*W}")
    print("  FTD-ONTOLOGY-DRIFT — Memory Pressure & Ontology Drift Dynamics")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    print(f"\n  NOTE: Offline proxy mode — metrics derived from trade records.")
    print(f"  For live diagnostics use /api/learning-intelligence/memory-pressure-dynamics")

    # ── Cognitive State ─────────────────────────────────────────────────────
    cs = result.get("cognitive_state", "—")
    category_meanings = {
        "HEALTHY_PLASTICITY":      "Memory systems are fluid; beliefs update readily",
        "PREMATURE_FOSSILIZATION":  "Learning rigidity detected; NegMem & low Q-entropy may lock out exploration",
        "ONTOLOGY_FRAGMENTATION":  "Memory subsystems hold strongly divergent beliefs",
        "ADAPTIVE_CONVERGENCE":    "Systems converging — Q-learning improving with manageable drift",
        "MEMORY_SATURATION":       "Both NegMem and Pattern formation are densely saturated",
        "ECOLOGICAL_AMNESIA":      "NegMem empty while RL context space is large — ecosystem may have lost negative signal",
    }
    print(f"\n  ── Cognitive State ──")
    print(f"  {cs}")
    print(f"  → {category_meanings.get(cs, '')}")

    # ── Memory Pressure ─────────────────────────────────────────────────────
    mp = result.get("memory_pressure", {})
    if mp:
        print(f"\n  ── Memory Pressure Diagnostics ──")
        print(f"  NegMem density:       {mp.get('negmem_density_pct', 0):.1f}%  "
              f"  ({mp.get('negmem_permanent_count', 0)} permanent / {mp.get('negmem_total_count', 0)} total)")
        print(f"  Pattern formation:    {mp.get('pattern_formation_rate_pct', 0):.1f}%  "
              f"  ({mp.get('pattern_formed', 0)} formed / {mp.get('pattern_total', 0)} total)")
        print(f"  Q entropy:            {mp.get('q_entropy_bits', 0):.4f} bits  "
              f"  (sampled {mp.get('q_values_sampled', 0)} contexts)")
        print(f"  Avg Q velocity:       {mp.get('avg_q_velocity', 0):.6f}")
        print(f"  Exploration rate:     {mp.get('exploration_rate_pct', 0):.1f}%")
        print(f"  Cognitive compression:{mp.get('cognitive_compression_ratio', 0):.1f}%")

        pl = mp.get("plasticity", {})
        fr = mp.get("fossilization_risk", {})
        print(f"\n  Plasticity:        {pl.get('score', 0):>3}/100  {_tier_badge(pl.get('tier', ''))}")
        print(f"  Fossilization risk:{fr.get('score', 0):>3}/100  {_tier_badge(fr.get('tier', ''))}")

        if verbose:
            print(f"\n  Plasticity components:  {pl.get('components', {})}")
            print(f"  Fossilization components: {fr.get('components', {})}")

    # ── Drift Heatmap ────────────────────────────────────────────────────────
    heatmap = result.get("drift_heatmap", [])
    print(f"\n  ── Ontology Drift Heatmap ──")
    print(f"  {'Pair':<28} {'Score':>7} {'Tier':>14}")
    print(f"  {'-'*52}")
    for h in heatmap:
        print(f"  {h['pair']:<28} {h['drift_score']:>7.1f} {_tier_badge(h['tier']):>14}")

    # ── Pair Detail ──────────────────────────────────────────────────────────
    if verbose:
        od = result.get("ontology_drift", {})
        print(f"\n  ── Pair Detail ──")
        for pair, m in od.items():
            print(f"\n  [{pair}]")
            for k, v in m.items():
                if k in ("drift_score", "tier", "interpretation", "note"):
                    print(f"    {k:<28} {v}")
                elif k == "per_regime" and isinstance(v, dict):
                    print(f"    per_regime:")
                    for regime, rd in v.items():
                        print(f"      {regime}: {rd}")

    # ── Summary Stats ────────────────────────────────────────────────────────
    ss = result.get("summary_stats", {})
    if ss:
        print(f"\n  ── Summary Stats ──")
        print(f"  Pairs evaluated: {ss.get('total_pairs', 0)}")
        print(f"  Avg drift score: {ss.get('avg_drift', 0):.1f}")
        print(f"  Max drift score: {ss.get('max_drift', 0):.1f}")
        print(f"  Min drift score: {ss.get('min_drift', 0):.1f}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Memory pressure & ontology drift — research instrumentation (offline proxy mode)"
    )
    parser.add_argument("--db",      default=str(DEFAULT_DB_PATH),
                        help="Path to data_lake.db")
    parser.add_argument("--limit",   default=2000, type=int,
                        help="Max trades to read from DataLake")
    parser.add_argument("--json",    action="store_true", dest="emit_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from core.memory_pressure_analytics import compute_memory_pressure_dynamics

    trades = _load_trades(Path(args.db), limit=args.limit)
    if not trades:
        print(f"\nNo trades found in {args.db} — run the engine first to populate the DataLake.")
        return

    state  = _build_proxy_state(trades)
    result = compute_memory_pressure_dynamics(state)

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result, verbose=args.verbose)


if __name__ == "__main__":
    main()

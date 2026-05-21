"""
FTD-DECISION-SNAP — Decision Snapshot Inspector

Research utility for longitudinal ontology-state analysis.
Reads all trades from DataLake and reports:
  1. Snapshot coverage % — how many trades have a decision_snapshot
  2. Pipeline-separated ontology distributions (Q-values, ecology scores, boost mults)
  3. Ontology-state drift — snapshot field presence over time (by trade index)
  4. Suppression event summary (if suppression_events.jsonl exists)

Usage:
    python tools/inspect_decision_snapshots.py
    python tools/inspect_decision_snapshots.py --db path/to/data_lake.db
    python tools/inspect_decision_snapshots.py --json
    python tools/inspect_decision_snapshots.py --suppression
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
DEFAULT_DB  = _PROJECT_ROOT / "data" / "data_lake.db"
DEFAULT_SUP = _PROJECT_ROOT / "data" / "suppression_events.jsonl"


# ── DataLake loader ───────────────────────────────────────────────────────────

def _load_trades(db_path: Path) -> list[dict]:
    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT data FROM trades ORDER BY ts ASC")
        rows = cur.fetchall()
    except sqlite3.OperationalError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()
    trades = []
    for (blob,) in rows:
        try:
            trades.append(json.loads(blob))
        except json.JSONDecodeError:
            pass
    return trades


# ── Snapshot analysis ─────────────────────────────────────────────────────────

def _has_snap(trade: dict) -> bool:
    snap = trade.get("decision_snapshot")
    return isinstance(snap, dict) and bool(snap)


def _analyse_coverage(trades: list[dict]) -> dict:
    total = len(trades)
    with_snap = sum(1 for t in trades if _has_snap(t))
    without   = total - with_snap
    return {
        "total_trades":    total,
        "with_snapshot":   with_snap,
        "without_snapshot": without,
        "coverage_pct":    round(with_snap / total * 100, 1) if total else 0.0,
        "migration_note":  (
            "Trades without snapshots were executed before FTD-DECISION-SNAP "
            "was deployed.  Coverage should be 100% for all new trades."
        ),
    }


def _analyse_by_pipeline(trades: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        snap = t.get("decision_snapshot") or {}
        pipeline = snap.get("pipeline") or t.get("origin_pipeline", "UNKNOWN")
        buckets[pipeline].append(t)

    result = {}
    for pipeline, tlist in buckets.items():
        q_vals = []
        boosts = []
        surv   = []
        for t in tlist:
            snap = t.get("decision_snapshot") or {}
            rl = snap.get("rl", {})
            if rl.get("q_value") is not None:
                q_vals.append(rl["q_value"])
            eco = snap.get("ecology", {})
            if eco.get("survival_rate") is not None:
                surv.append(eco["survival_rate"])
            alpha = snap.get("alpha_context", {})
            if alpha.get("boost_mult") is not None:
                boosts.append(alpha["boost_mult"])
        result[pipeline] = {
            "trade_count":         len(tlist),
            "rl_q_value": {
                "count": len(q_vals),
                "mean":  round(mean(q_vals), 4) if q_vals else None,
                "min":   round(min(q_vals), 4) if q_vals else None,
                "max":   round(max(q_vals), 4) if q_vals else None,
                "stdev": round(stdev(q_vals), 4) if len(q_vals) > 1 else None,
            },
            "ecology_survival_rate": {
                "count": len(surv),
                "mean":  round(mean(surv), 4) if surv else None,
            },
            "alpha_boost_mult": {
                "count": len(boosts),
                "mean":  round(mean(boosts), 4) if boosts else None,
                "min":   round(min(boosts), 4) if boosts else None,
                "max":   round(max(boosts), 4) if boosts else None,
            },
        }
    return result


def _analyse_drift(trades: list[dict], window: int = 20) -> dict:
    """
    Split trade history into early / mid / recent windows and compare
    snapshot field presence rates.  Detects ontology state decay over time.
    """
    snapped = [t for t in trades if _has_snap(t)]
    if len(snapped) < 3:
        return {"note": "Insufficient snapshot-bearing trades for drift analysis (need ≥3)"}

    def _field_rates(tlist: list[dict]) -> dict:
        n = len(tlist)
        rl = sum(1 for t in tlist if "rl" in (t.get("decision_snapshot") or {}))
        eco = sum(1 for t in tlist if "ecology" in (t.get("decision_snapshot") or {}))
        alpha = sum(1 for t in tlist if "alpha_context" in (t.get("decision_snapshot") or {}))
        return {
            "n": n,
            "rl_pct":    round(rl / n * 100, 1),
            "eco_pct":   round(eco / n * 100, 1),
            "alpha_pct": round(alpha / n * 100, 1),
        }

    chunk = max(1, len(snapped) // 3)
    return {
        "early_trades":  _field_rates(snapped[:chunk]),
        "mid_trades":    _field_rates(snapped[chunk:2*chunk]),
        "recent_trades": _field_rates(snapped[2*chunk:]),
        "note": "Declining % across windows would indicate ontology field collection regression.",
    }


def _analyse_sessions(trades: list[dict]) -> dict:
    session_counts: Counter = Counter()
    for t in trades:
        if _has_snap(t):
            label = (t.get("decision_snapshot") or {}).get("session_label", "UNKNOWN")
            session_counts[label] += 1
    return dict(session_counts)


# ── Suppression log analysis ──────────────────────────────────────────────────

def _analyse_suppression(sup_path: Path) -> dict:
    if not sup_path.exists():
        return {"note": f"No suppression log found at {sup_path}"}
    lines = sup_path.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    total = len(events)
    by_gate: Counter     = Counter(e.get("gate", "?") for e in events)
    by_session: Counter  = Counter(e.get("session", "?") for e in events)
    by_pipeline: Counter = Counter(e.get("pipeline", "?") for e in events)
    by_regime: Counter   = Counter(e.get("regime", "?") for e in events)
    return {
        "total_suppression_events": total,
        "by_gate":     dict(by_gate.most_common()),
        "by_session":  dict(by_session.most_common()),
        "by_pipeline": dict(by_pipeline.most_common()),
        "by_regime":   dict(by_regime.most_common()),
    }


# ── Report printing ───────────────────────────────────────────────────────────

def _print_report(coverage: dict, pipeline: dict, drift: dict,
                  sessions: dict, suppression: dict | None) -> None:
    w = 62
    print(f"\n{'='*w}")
    print("  FTD-DECISION-SNAP — Decision Snapshot Inspector")
    print(f"{'='*w}")

    print(f"\n  Coverage")
    print(f"    Total trades        : {coverage['total_trades']}")
    print(f"    With snapshot       : {coverage['with_snapshot']}")
    print(f"    Without snapshot    : {coverage['without_snapshot']}")
    print(f"    Coverage            : {coverage['coverage_pct']:.1f}%")
    print(f"    Note: {coverage['migration_note'][:55]}...")

    print(f"\n  Pipeline-Separated Ontology Distributions")
    for pl, data in pipeline.items():
        print(f"\n    [{pl}]  trades={data['trade_count']}")
        q = data["rl_q_value"]
        if q["count"]:
            print(f"      RL Q-value   : n={q['count']}  "
                  f"mean={q['mean']:+.4f}  min={q['min']:+.4f}  max={q['max']:+.4f}")
        eco = data["ecology_survival_rate"]
        if eco["count"]:
            print(f"      Survival rate: n={eco['count']}  mean={eco['mean']:.4f}")
        a = data["alpha_boost_mult"]
        if a["count"]:
            print(f"      Alpha boost  : n={a['count']}  "
                  f"mean={a['mean']:.4f}  min={a['min']:.4f}  max={a['max']:.4f}")

    print(f"\n  Ontology-State Drift (field presence across trade history)")
    if "note" in drift and len(drift) == 1:
        print(f"    {drift['note']}")
    else:
        for window, stats in [("Early", drift.get("early_trades", {})),
                               ("Mid",   drift.get("mid_trades", {})),
                               ("Recent",drift.get("recent_trades", {}))]:
            n = stats.get("n", 0)
            print(f"    {window:8s} (n={n:3d}): "
                  f"RL={stats.get('rl_pct', 0):.0f}%  "
                  f"Eco={stats.get('eco_pct', 0):.0f}%  "
                  f"Alpha={stats.get('alpha_pct', 0):.0f}%")
        print(f"    {drift.get('note', '')[:60]}")

    print(f"\n  Sessions in snapshots: {sessions}")

    if suppression:
        print(f"\n  Suppression Event Summary")
        print(f"    Total events : {suppression.get('total_suppression_events', 0)}")
        print(f"    By gate      : {suppression.get('by_gate', {})}")
        print(f"    By pipeline  : {suppression.get('by_pipeline', {})}")
        print(f"    By session   : {suppression.get('by_session', {})}")

    print(f"\n{'='*w}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect decision snapshot coverage and ontology distributions")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to data_lake.db")
    parser.add_argument("--json", action="store_true", dest="emit_json",
                        help="Emit JSON instead of human-readable report")
    parser.add_argument("--suppression", action="store_true", dest="show_sup",
                        help="Include suppression event analysis")
    args = parser.parse_args()

    trades     = _load_trades(Path(args.db))
    coverage   = _analyse_coverage(trades)
    pipeline   = _analyse_by_pipeline(trades)
    drift      = _analyse_drift(trades)
    sessions   = _analyse_sessions(trades)
    suppression = _analyse_suppression(DEFAULT_SUP) if args.show_sup else None

    result = {
        "coverage":   coverage,
        "by_pipeline": pipeline,
        "drift":      drift,
        "sessions":   sessions,
    }
    if suppression is not None:
        result["suppression"] = suppression

    if args.emit_json:
        print(json.dumps(result, indent=2))
    else:
        _print_report(coverage, pipeline, drift, sessions, suppression)


if __name__ == "__main__":
    main()

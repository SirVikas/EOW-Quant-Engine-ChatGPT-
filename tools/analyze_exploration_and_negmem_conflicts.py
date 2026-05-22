"""
FTD-EXPLORE-OBSERVABILITY — Exploration Persistence & NegativeMemory Conflict Analyzer

Reads persisted data files directly (no live engine required) and produces:

  1. Exploration persistence timeline
       — lifetime event counts by rule, session, pipeline, context, Q-band
       — restart-aware: lifetime vs last-restart reconstruction
       — chronological event log excerpt

  2. NegativeMemory sensitivity report
       — all patterns classified into ontology conflict categories
       — quarantine-at-low-sample events
       — toxic-at-high-WR events
       — avg losses before quarantine / before permanent ban

  3. Ontology conflict heatmap
       — CONFLICT_POSITIVE_WR: WR > 0 but NegMem banned (key signal)
       — CONFLICT_NEGATIVE_WR: WR = 0 but NegMem healthy

Usage:
    python tools/analyze_exploration_and_negmem_conflicts.py
    python tools/analyze_exploration_and_negmem_conflicts.py --json
    python tools/analyze_exploration_and_negmem_conflicts.py --explore-log path/to/exploration_events.jsonl
    python tools/analyze_exploration_and_negmem_conflicts.py --negmem path/to/negative_memory.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

_HERE         = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent

DEFAULT_EXPLORE_LOG = _PROJECT_ROOT / "data"    / "exploration_events.jsonl"
DEFAULT_NEGMEM_PATH = _PROJECT_ROOT / "reports" / "learning_memory" / "negative_memory.jsonl"
DEFAULT_PATTERN_IDX = _PROJECT_ROOT / "reports" / "learning_memory" / "pattern_index.jsonl"

TEMP_REMOVAL_THRESHOLD = 0.10   # mirrors negative_memory.py constant
SESSION_ORDER          = ["ASIA", "LONDON", "NY", "LATE"]


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def _load_negmem(path: Path) -> dict[str, dict]:
    """
    NegativeMemory JSONL has one entry per (key_str, cycle) — latest wins.
    Returns {key_str: latest_entry}.
    """
    entries = _load_jsonl(path)
    latest: dict[str, dict] = {}
    for e in entries:
        ks = e.get("key_str", "")
        if ks:
            latest[ks] = e   # later entries overwrite earlier ones
    return latest


def _load_pattern_index(path: Path) -> list[dict]:
    return _load_jsonl(path)


# ── Exploration analysis ──────────────────────────────────────────────────────

def analyse_exploration(events: list[dict]) -> dict:
    if not events:
        return {
            "total_events": 0,
            "note": "No exploration events recorded yet.",
        }

    rule_counts:     dict[str, int] = defaultdict(int)
    session_counts:  dict[str, int] = defaultdict(int)
    pipeline_counts: dict[str, int] = defaultdict(int)
    context_counts:  dict[str, int] = defaultdict(int)
    q_values:        list[float]    = []

    q_bands: dict[str, int] = {
        "(-0.15,-0.10)": 0,
        "(-0.10,-0.05)": 0,
        "(-0.05, 0.00)": 0,
        "[0.00, +inf)":  0,
        "other":         0,
    }

    for ev in events:
        rule_counts[ev.get("rule",     "UNKNOWN")] += 1
        session_counts[ev.get("session",  "UNKNOWN")] += 1
        pipeline_counts[ev.get("pipeline", "UNKNOWN")] += 1
        context_counts[ev.get("context",  "UNKNOWN")] += 1
        q = ev.get("q_value", 0.0)
        q_values.append(q)
        if q >= 0:
            q_bands["[0.00, +inf)"]  += 1
        elif q > -0.05:
            q_bands["(-0.05, 0.00)"] += 1
        elif q > -0.10:
            q_bands["(-0.10,-0.05)"] += 1
        elif q > -0.15:
            q_bands["(-0.15,-0.10)"] += 1
        else:
            q_bands["other"]         += 1

    context_table = sorted(
        [{"context": k, "count": v} for k, v in context_counts.items()],
        key=lambda x: -x["count"],
    )
    session_table = sorted(
        [{"session": k, "count": v} for k, v in session_counts.items()],
        key=lambda x: SESSION_ORDER.index(x["session"]) if x["session"] in SESSION_ORDER else 99,
    )

    return {
        "total_events":       len(events),
        "rule_breakdown":     dict(rule_counts),
        "session_breakdown":  session_table,
        "pipeline_breakdown": dict(pipeline_counts),
        "context_breakdown":  context_table[:20],
        "q_band_distribution": q_bands,
        "avg_q_at_grant":     round(mean(q_values), 4) if q_values else None,
        "chronological_last10": events[-10:],
    }


# ── NegativeMemory sensitivity ────────────────────────────────────────────────

def analyse_negmem(
    negmem_index: dict[str, dict],
    patterns:     list[dict],
) -> dict:
    aligned_positive    = []
    aligned_negative    = []
    conflict_pos_wr     = []
    conflict_neg_wr     = []

    quarantine_lt5 = 0
    toxic_wr_gt50  = 0

    all_rollbacks  = [e.get("rollbacks", 0) for e in negmem_index.values()]
    perm_rollbacks = [e.get("rollbacks", 0) for e in negmem_index.values()
                      if e.get("permanent")]

    def _is_banned(entry: dict | None) -> bool:
        if entry is None:
            return False
        if entry.get("permanent"):
            return True
        return entry.get("score", 0.0) >= TEMP_REMOVAL_THRESHOLD

    classified = []
    for pat in patterns:
        key_data = pat.get("key", {})
        if isinstance(key_data, dict):
            ks = "|".join([
                key_data.get("regime", ""),
                key_data.get("volatility", ""),
                key_data.get("instrument", ""),
                key_data.get("parameter", ""),
                key_data.get("direction", ""),
            ])
        else:
            ks = str(key_data)

        samples  = max(pat.get("samples", 1), 1)
        success  = pat.get("success", 0)
        wr       = success / samples
        nm_entry = negmem_index.get(ks)
        banned   = _is_banned(nm_entry)
        wr_pos   = wr > 0.0

        if   wr_pos and not banned:  cat = "ALIGNED_POSITIVE"
        elif not wr_pos and banned:  cat = "ALIGNED_NEGATIVE"
        elif wr_pos and banned:      cat = "CONFLICT_POSITIVE_WR"
        else:                        cat = "CONFLICT_NEGATIVE_WR"

        if cat == "ALIGNED_POSITIVE":    aligned_positive.append(ks)
        elif cat == "ALIGNED_NEGATIVE":  aligned_negative.append(ks)
        elif cat == "CONFLICT_POSITIVE_WR": conflict_pos_wr.append(ks)
        else:                            conflict_neg_wr.append(ks)

        if banned and samples < 5:
            quarantine_lt5 += 1
        if banned and wr > 0.50:
            toxic_wr_gt50 += 1

        classified.append({
            "key":              ks,
            "samples":          pat.get("samples", 0),
            "successes":        success,
            "wr_pct":           round(wr * 100, 1),
            "negmem_banned":    banned,
            "negmem_rollbacks": nm_entry.get("rollbacks", 0) if nm_entry else 0,
            "negmem_score":     round(nm_entry.get("score", 0.0), 3) if nm_entry else None,
            "negmem_permanent": nm_entry.get("permanent", False) if nm_entry else False,
            "category":         cat,
        })

    total         = len(patterns)
    conflict_total = len(conflict_pos_wr) + len(conflict_neg_wr)

    return {
        "total_patterns": total,
        "ontology_conflict_summary": {
            "aligned_positive":    len(aligned_positive),
            "aligned_negative":    len(aligned_negative),
            "conflict_positive_wr": len(conflict_pos_wr),
            "conflict_negative_wr": len(conflict_neg_wr),
            "conflict_total":      conflict_total,
            "conflict_ratio":      round(conflict_total / max(total, 1), 3),
        },
        "negmem_sensitivity": {
            "quarantine_events_at_n_lt_5":     quarantine_lt5,
            "toxic_promotions_at_wr_gt_50pct": toxic_wr_gt50,
            "avg_losses_before_quarantine": (
                round(mean(all_rollbacks), 2) if all_rollbacks else None
            ),
            "avg_losses_before_permanent_ban": (
                round(mean(perm_rollbacks), 2) if perm_rollbacks else None
            ),
            "total_negmem_entries": len(negmem_index),
            "permanent_bans":       sum(1 for e in negmem_index.values() if e.get("permanent")),
        },
        "conflict_positive_wr_keys": conflict_pos_wr,
        "per_pattern": sorted(classified, key=lambda x: -x["negmem_rollbacks"]),
    }


# ── Report printing ───────────────────────────────────────────────────────────

def _print_report(exp: dict, nm: dict, verbose: bool = False) -> None:
    W = 68
    print(f"\n{'='*W}")
    print("  FTD-EXPLORE-OBSERVABILITY — Exploration & NegMem Conflict Analyzer")
    print(f"{'='*W}")

    # Exploration
    print(f"\n  ── Exploration Persistence Timeline ──")
    print(f"  Total events (lifetime): {exp.get('total_events', 0)}")
    rb = exp.get("rule_breakdown", {})
    print(f"  Rule 1 (min explore):   {rb.get('RULE1_MIN_EXPLORE', 0)}")
    print(f"  Rule 4 (floor explore): {rb.get('RULE4_FLOOR_EXPLORE', 0)}")

    sess = exp.get("session_breakdown", [])
    if sess:
        print(f"\n  Session distribution:")
        for s in sess:
            print(f"    {s['session']:<10}: {s['count']}")

    pipe = exp.get("pipeline_breakdown", {})
    if pipe:
        print(f"\n  Pipeline distribution:")
        for p, c in pipe.items():
            print(f"    {p:<20}: {c}")

    q_bands = exp.get("q_band_distribution", {})
    if q_bands:
        print(f"\n  Q-band distribution at grant:")
        for band, cnt in q_bands.items():
            print(f"    {band:<18}: {cnt}")

    ctx_table = exp.get("context_breakdown", [])
    if ctx_table and verbose:
        print(f"\n  Top contexts (by event count):")
        for row in ctx_table[:10]:
            print(f"    {row['context']:<55}: {row['count']}")

    avg_q = exp.get("avg_q_at_grant")
    if avg_q is not None:
        print(f"\n  Avg Q-value at grant: {avg_q:+.4f}")

    # NegativeMemory forensics
    print(f"\n  ── NegativeMemory Sensitivity Forensics ──")
    ocs = nm.get("ontology_conflict_summary", {})
    total_pats = nm.get("total_patterns", 0)
    print(f"  Total patterns tracked: {total_pats}")
    print(f"  ALIGNED_POSITIVE    : {ocs.get('aligned_positive', 0)}")
    print(f"  ALIGNED_NEGATIVE    : {ocs.get('aligned_negative', 0)}")
    print(f"  CONFLICT_POSITIVE_WR: {ocs.get('conflict_positive_wr', 0)}  ← WR>0 but NegMem banned")
    print(f"  CONFLICT_NEGATIVE_WR: {ocs.get('conflict_negative_wr', 0)}  ← WR=0 but NegMem healthy")
    cr = ocs.get("conflict_ratio", 0)
    print(f"  Ontology conflict ratio: {cr:.1%}")

    ns = nm.get("negmem_sensitivity", {})
    print(f"\n  NegMem Sensitivity Metrics:")
    print(f"  Quarantine at n < 5   : {ns.get('quarantine_events_at_n_lt_5', 0)}")
    print(f"  Toxic at WR > 50%     : {ns.get('toxic_promotions_at_wr_gt_50pct', 0)}")
    alq = ns.get("avg_losses_before_quarantine")
    print(f"  Avg losses → quarantine: {f'{alq:.2f}' if alq is not None else '—'}")
    alpb = ns.get("avg_losses_before_permanent_ban")
    print(f"  Avg losses → perm ban  : {f'{alpb:.2f}' if alpb is not None else '—'}")

    cflts = nm.get("conflict_positive_wr_keys", [])
    if cflts:
        print(f"\n  CONFLICT_POSITIVE_WR patterns (WR>0 + NegMem banned):")
        for k in cflts[:10]:
            print(f"    {k}")

    if verbose:
        per_pat = nm.get("per_pattern", [])
        if per_pat:
            print(f"\n  Per-pattern classification:")
            print(f"  {'Key':<55} {'Samples':>7} {'WR%':>5} {'Rollbacks':>9} {'Category'}")
            for row in per_pat[:20]:
                print(
                    f"  {row['key']:<55} {row['samples']:>7} "
                    f"{row['wr_pct']:>4.1f}% {row['negmem_rollbacks']:>9}  {row['category']}"
                )

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploration persistence & NegativeMemory conflict analyzer")
    parser.add_argument("--explore-log", default=str(DEFAULT_EXPLORE_LOG),
                        help="Path to exploration_events.jsonl")
    parser.add_argument("--negmem",      default=str(DEFAULT_NEGMEM_PATH),
                        help="Path to negative_memory.jsonl")
    parser.add_argument("--patterns",    default=str(DEFAULT_PATTERN_IDX),
                        help="Path to pattern_index.jsonl")
    parser.add_argument("--json",        action="store_true", dest="emit_json")
    parser.add_argument("--verbose",     action="store_true")
    args = parser.parse_args()

    events   = _load_jsonl(Path(args.explore_log))
    negmem   = _load_negmem(Path(args.negmem))
    patterns = _load_pattern_index(Path(args.patterns))

    exp_result = analyse_exploration(events)
    nm_result  = analyse_negmem(negmem, patterns)

    if args.emit_json:
        print(json.dumps({"exploration": exp_result, "negmem_forensics": nm_result}, indent=2))
    else:
        _print_report(exp_result, nm_result, verbose=args.verbose)


if __name__ == "__main__":
    main()

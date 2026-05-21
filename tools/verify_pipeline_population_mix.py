"""
FTD-PATH-ATTR — Historical Pipeline Population Mix Verifier

Reads all trades from the DataLake SQLite database and reports the breakdown
of origin_pipeline values across the historical trade record.

Trades recorded before FTD-PATH-ATTR was deployed will show origin_pipeline
as "UNKNOWN" (field absent in older JSON blobs) or the literal string "UNKNOWN"
(default value on the dataclass).  This script disambiguates them so the
migration boundary is visible.

Usage:
    python tools/verify_pipeline_population_mix.py
    python tools/verify_pipeline_population_mix.py --db path/to/custom.db
    python tools/verify_pipeline_population_mix.py --json  # emit JSON

Output sections:
  1. Pipeline mix counts (PAPER_SPEED / PRIMARY_STRATEGY / UNKNOWN / legacy)
  2. Strategy ID breakdown per pipeline bucket (top-10 by count)
  3. Temporal boundary — earliest trade with a real attribution vs. "UNKNOWN"
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ── Resolve project root so script works from any cwd ────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent

DEFAULT_DB = _PROJECT_ROOT / "data" / "data_lake.db"


def _load_trades(db_path: Path) -> list[dict]:
    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT data FROM trades ORDER BY ts ASC")
        rows = cur.fetchall()
    except sqlite3.OperationalError as exc:
        print(f"[ERROR] Query failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    trades = []
    for (blob,) in rows:
        try:
            trades.append(json.loads(blob))
        except json.JSONDecodeError:
            pass  # skip malformed blobs silently
    return trades


def _classify(trade: dict) -> str:
    op = trade.get("origin_pipeline")
    if op in ("PAPER_SPEED", "PRIMARY_STRATEGY"):
        return op
    # Legacy trade: field absent or default "UNKNOWN" — infer from strategy_id
    sid = trade.get("strategy_id", "")
    if sid.endswith("_PAPER_SPEED"):
        return "INFERRED_PAPER_SPEED"
    if sid:
        return "INFERRED_PRIMARY_STRATEGY"
    return "LEGACY_NO_STRATEGY"


def _analyse(trades: list[dict]) -> dict:
    pipeline_counts: Counter = Counter()
    strategy_by_pipeline: dict[str, Counter] = defaultdict(Counter)
    earliest_attributed: dict | None = None
    earliest_unknown_ts: int | None = None

    for t in trades:
        bucket = _classify(t)
        pipeline_counts[bucket] += 1
        strategy_by_pipeline[bucket][t.get("strategy_id", "<none>")] += 1

        op = t.get("origin_pipeline")
        ts = t.get("exit_ts", t.get("entry_ts", 0))
        if op in ("PAPER_SPEED", "PRIMARY_STRATEGY"):
            if earliest_attributed is None or ts < earliest_attributed.get("ts", float("inf")):
                earliest_attributed = {"ts": ts, "trade_id": t.get("trade_id"), "pipeline": op}
        else:
            if earliest_unknown_ts is None or ts < earliest_unknown_ts:
                earliest_unknown_ts = ts

    total = len(trades)
    return {
        "total_trades": total,
        "pipeline_mix": dict(pipeline_counts),
        "pipeline_pct": {
            k: round(v / total * 100, 1) if total else 0.0
            for k, v in pipeline_counts.items()
        },
        "top_strategies_by_pipeline": {
            bucket: dict(ctr.most_common(10))
            for bucket, ctr in strategy_by_pipeline.items()
        },
        "temporal_boundary": {
            "earliest_attributed_trade": earliest_attributed,
            "earliest_unattributed_exit_ts": earliest_unknown_ts,
            "migration_note": (
                "Trades with PAPER_SPEED or PRIMARY_STRATEGY in origin_pipeline "
                "were recorded after FTD-PATH-ATTR deployment. All earlier trades "
                "are INFERRED or LEGACY."
            ),
        },
    }


def _print_report(result: dict) -> None:
    total = result["total_trades"]
    print(f"\n{'='*60}")
    print("  FTD-PATH-ATTR — Pipeline Population Mix Report")
    print(f"{'='*60}")
    print(f"  Total trades in DataLake : {total}")
    print()
    print("  Pipeline breakdown:")
    for bucket, count in sorted(result["pipeline_mix"].items()):
        pct = result["pipeline_pct"][bucket]
        print(f"    {bucket:<35} {count:>6}  ({pct:.1f}%)")
    print()
    print("  Top strategies per pipeline bucket (max 10 each):")
    for bucket, strats in result["top_strategies_by_pipeline"].items():
        print(f"\n    [{bucket}]")
        for sid, cnt in sorted(strats.items(), key=lambda x: -x[1]):
            print(f"      {sid:<40} {cnt}")
    tb = result["temporal_boundary"]
    print()
    print("  Temporal boundary:")
    ea = tb["earliest_attributed_trade"]
    if ea:
        print(f"    Earliest attributed trade : {ea['trade_id']} "
              f"(pipeline={ea['pipeline']}, exit_ts={ea['ts']})")
    else:
        print("    Earliest attributed trade : None — no attributed trades yet")
    eu = tb["earliest_unattributed_exit_ts"]
    print(f"    Earliest unattributed ts  : {eu}")
    print(f"\n    Note: {tb['migration_note']}")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify pipeline population mix in DataLake")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to data_lake.db")
    parser.add_argument("--json", action="store_true", dest="emit_json",
                        help="Emit JSON instead of human-readable report")
    args = parser.parse_args()

    db_path = Path(args.db)
    trades  = _load_trades(db_path)
    result  = _analyse(trades)

    if args.emit_json:
        print(json.dumps(result, indent=2))
    else:
        _print_report(result)


if __name__ == "__main__":
    main()

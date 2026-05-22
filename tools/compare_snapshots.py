"""
FTD-UDCA CLI: Compare Snapshots.

Diffs two snapshot records or compares two snapshot eras
(early vs late chronological split).

Usage:
    python tools/compare_snapshots.py --two [--simulate N] [--json] [--verbose]
    python tools/compare_snapshots.py --eras [--simulate N] [--split FRAC]
                                             [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.replay_explorer import compare_snapshots, compare_eras
from core.snapshot_manager import create_snapshot_record, SNAPSHOT_TYPES


def _simulate_snapshots(n: int) -> list:
    types = sorted(SNAPSHOT_TYPES)
    snaps = []
    base  = 1_700_000_000_000
    for i in range(n):
        s = create_snapshot_record(
            snapshot_type=types[i % len(types)],
            app_version=f"1.{i // len(types)}.0",
            trade_count=i * 100,
            label=f"snap-{i+1}",
            triggered_by="CLI_COMPARE",
            generation_ts=base + i * 3_600_000,
        )
        snaps.append(s)
    return snaps


def _print_comparison(result: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  Snapshot Comparison")
    print(f"{'='*60}")
    print(f"  Snapshot A      : {result.get('snapshot_a_id', '')}")
    print(f"  Snapshot B      : {result.get('snapshot_b_id', '')}")
    print(f"  Elapsed (ms)    : {result.get('elapsed_ms', 0):,}")
    print()
    changed = []
    if result.get("version_changed"):
        changed.append(f"  Version         : {result['version_a']} → {result['version_b']}")
    if result.get("type_changed"):
        changed.append(f"  Snapshot Type   : {result['type_a']} → {result['type_b']}")
    if result.get("hash_changed"):
        changed.append(f"  Hash            : {result['hash_a_prefix']}... → {result['hash_b_prefix']}...")
    if result.get("trade_count_delta", 0) != 0:
        changed.append(f"  Trade Count     : {result['trade_count_a']:,} → {result['trade_count_b']:,}"
                       f"  (delta={result['trade_count_delta']:+,})")

    if changed:
        print("  Changes detected:")
        for c in changed:
            print(c)
    else:
        print("  No changes detected between snapshots.")

    print(f"\n  Both immutable  : {result.get('both_immutable', False)}")
    print(f"{'='*60}\n")


def _print_era_comparison(result: dict) -> None:
    def _fmt_era(era: dict) -> None:
        print(f"    Count          : {era.get('count', 0)}")
        print(f"    Versions       : {', '.join(era.get('versions', []))}")
        stypes = era.get("snapshot_types", {})
        if stypes:
            print(f"    Types          : {stypes}")

    print(f"\n{'='*60}")
    print(f"  Era Comparison — {result.get('era_a_label')} vs {result.get('era_b_label')}")
    print(f"{'='*60}")
    print(f"\n  {result.get('era_a_label')}:")
    _fmt_era(result.get("era_a", {}))
    print(f"\n  {result.get('era_b_label')}:")
    _fmt_era(result.get("era_b", {}))

    print(f"\n  Count delta     : {result.get('count_delta', 0):+d}")
    print(f"  Trade delta     : {result.get('trade_delta', 0):+,}")
    print(f"  Version overlap : {result.get('version_overlap', [])}")
    only_a = result.get("types_only_in_a", [])
    only_b = result.get("types_only_in_b", [])
    if only_a:
        print(f"  Types only in A : {only_a}")
    if only_b:
        print(f"  Types only in B : {only_b}")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare PHOENIX snapshot records or eras."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--two",  action="store_true",
                       help="Compare first and last snapshots from simulation.")
    group.add_argument("--eras", action="store_true",
                       help="Compare early vs late era (chronological split).")
    parser.add_argument("--simulate", type=int, default=14, metavar="N",
                        help="Number of simulated snapshots (default: 14).")
    parser.add_argument("--split", type=float, default=0.5, metavar="FRAC",
                        help="Fraction for era split (default: 0.5 = 50/50).")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    snaps = _simulate_snapshots(args.simulate)

    if args.two:
        if len(snaps) < 2:
            print("ERROR: need at least 2 snapshots (use --simulate N with N >= 2).",
                  file=sys.stderr)
            sys.exit(1)
        result = compare_snapshots(snaps[0], snaps[-1])
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_comparison(result)
        sys.exit(0 if result.get("compare_healthy") else 1)

    # eras
    split_idx = max(1, int(len(snaps) * args.split))
    era_a = snaps[:split_idx]
    era_b = snaps[split_idx:]
    result = compare_eras(era_a, era_b, "EARLY_ERA", "LATE_ERA")
    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_era_comparison(result)
    sys.exit(0 if result.get("compare_healthy") else 1)


if __name__ == "__main__":
    main()

"""
FTD-UEI CLI: Reconstruct Snapshot Lineage.

Creates sample snapshot records and displays a lineage timeline.
In production, the snapshot ledger comes from the session in main.py;
this tool demonstrates lineage reconstruction from arbitrary snapshot data.

Usage:
    python tools/reconstruct_snapshot_lineage.py [--simulate N]
                                                  [--type SNAPSHOT_TYPE]
                                                  [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.snapshot_manager import (
    create_snapshot_record, get_snapshot_health,
    get_latest_snapshot, get_snapshots_by_type,
    SNAPSHOT_TYPES, SNAPSHOT_TYPE_DESCRIPTIONS,
)


def _simulate_snapshots(n: int) -> list:
    types = ["HOURLY", "DAILY", "MILESTONE", "VERSION_TRANSITION",
             "GOVERNANCE_TRANSITION", "EPISTEMIC_SHIFT", "CATASTROPHIC_EVENT"]
    snapshots = []
    base_ts = 1_700_000_000_000
    for i in range(n):
        s_type  = types[i % len(types)]
        version = f"1.{i // 7}.0"
        snap    = create_snapshot_record(
            snapshot_type=s_type,
            app_version=version,
            trade_count=i * 100,
            label=f"Simulated snapshot {i+1}",
            triggered_by="CLI_SIMULATE",
            generation_ts=base_ts + i * 3_600_000,
        )
        snapshots.append(snap)
    return snapshots


def _print_lineage(snapshots: list, health: dict, verbose: bool) -> None:
    print(f"\n{'='*64}")
    print(f"  PHOENIX Snapshot Lineage Reconstruction")
    print(f"{'='*64}")
    print(f"  Total snapshots : {health.get('total_snapshots', 0)}")
    print(f"  Versions covered: {', '.join(health.get('app_versions_covered', []))}")
    latest = health.get("latest_snapshot_id", "-")
    print(f"  Latest snapshot : {latest}")

    by_type = health.get("snapshot_by_type", {})
    if by_type:
        print(f"\n  Snapshot breakdown:")
        for t, cnt in sorted(by_type.items()):
            desc = SNAPSHOT_TYPE_DESCRIPTIONS.get(t, "")
            print(f"    {t:30s} ×{cnt:3d}  — {desc}")

    if verbose and snapshots:
        print(f"\n  Lineage timeline ({len(snapshots)} entries):")
        for snap in snapshots:
            sid   = snap.get("snapshot_id", "")
            ts    = snap.get("timestamp_ms", 0)
            stype = snap.get("snapshot_type", "")
            ver   = snap.get("app_version", "")
            fp    = snap.get("reconstruction_hash", "")[:12]
            print(f"    {sid:35s}  ver={ver:8s}  hash={fp}...")

    print(f"{'='*64}")
    healthy = health.get("lineage_healthy", True)
    print(f"  Lineage Health  : {'HEALTHY' if healthy else 'DEGRADED'}")
    print(f"{'='*64}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruct PHOENIX snapshot lineage."
    )
    parser.add_argument(
        "--simulate", type=int, default=14, metavar="N",
        help="Generate N simulated snapshot records (default: 14).",
    )
    parser.add_argument(
        "--type", dest="filter_type", default=None,
        help=f"Filter to one snapshot type. Available: {', '.join(sorted(SNAPSHOT_TYPES))}",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    snapshots = _simulate_snapshots(args.simulate)

    if args.filter_type:
        t = args.filter_type.upper()
        if t not in SNAPSHOT_TYPES:
            print(
                f"ERROR: unknown snapshot type '{t}'. "
                f"Available: {', '.join(sorted(SNAPSHOT_TYPES))}",
                file=sys.stderr,
            )
            sys.exit(1)
        snapshots = get_snapshots_by_type(snapshots, t)

    health = get_snapshot_health(snapshots)

    if args.as_json:
        out = {
            "snapshot_health": health,
            "snapshots": snapshots if args.verbose else [],
        }
        print(json.dumps(out, indent=2, default=str))
        return

    _print_lineage(snapshots, health, verbose=args.verbose)


if __name__ == "__main__":
    main()

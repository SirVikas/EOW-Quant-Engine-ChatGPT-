"""
FTD-UDCA CLI: Replay Report Lineage.

Replays the lineage of a PHOENIX report across simulated snapshots,
or prints a full replay timeline with version transition annotations.

Usage:
    python tools/replay_lineage.py --report REPORT_ID [--simulate N]
                                    [--json] [--verbose]
    python tools/replay_lineage.py --timeline [--simulate N]
                                    [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.replay_explorer import (
    replay_lineage, get_replay_timeline, get_replay_health,
)
from core.snapshot_manager import create_snapshot_record, SNAPSHOT_TYPES
from core.report_registry import REPORT_REGISTRY


def _simulate_snapshots(n: int) -> list:
    types = sorted(SNAPSHOT_TYPES)
    snaps = []
    base  = 1_700_000_000_000
    for i in range(n):
        s = create_snapshot_record(
            snapshot_type=types[i % len(types)],
            app_version=f"1.{i // len(types)}.0",
            trade_count=i * 100,
            label=f"snapshot-{i+1}",
            triggered_by="CLI_REPLAY",
            generation_ts=base + i * 3_600_000,
        )
        snaps.append(s)
    return snaps


def _print_lineage(result: dict, verbose: bool) -> None:
    print(f"\n{'='*66}")
    print(f"  PHOENIX Lineage Replay — {result.get('report_name', result.get('report_id', ''))}")
    print(f"{'='*66}")
    print(f"  Report ID      : {result.get('report_id', '')}")
    print(f"  Family         : {result.get('report_family', '')}")
    print(f"  Dependencies   : {result.get('dependency_count', 0)}")
    if result.get("dependencies"):
        print(f"    {', '.join(result['dependencies'])}")
    print(f"  Replay Events  : {result.get('replay_event_count', 0)}")
    if verbose:
        for ev in result.get("replay_events", []):
            stype = ev.get("snapshot_type", "")
            ver   = ev.get("app_version", "")
            tc    = ev.get("trade_count", 0)
            fp    = ev.get("reconstruction_hash_prefix", "")
            print(f"    {ev['snapshot_id']:35s}  {stype:20s}  ver={ver}  trades={tc}  hash={fp}...")
    print(f"{'='*66}\n")


def _print_timeline(result: dict, verbose: bool) -> None:
    print(f"\n{'='*66}")
    print(f"  PHOENIX Replay Timeline")
    print(f"{'='*66}")
    print(f"  Total Events       : {result.get('event_count', 0)}")
    print(f"  Version Transitions: {result.get('version_transitions', 0)}")
    if verbose:
        for ev in result.get("events", []):
            idx   = ev.get("index", 0)
            sid   = ev.get("snapshot_id", "")
            stype = ev.get("snapshot_type", "")
            ver   = ev.get("app_version", "")
            vt    = " [VERSION CHANGE]" if ev.get("version_transition") else ""
            print(f"  {idx:3d}. {sid:35s}  {stype:22s}  v{ver}{vt}")
    print(f"{'='*66}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay PHOENIX report lineage or full snapshot timeline."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", metavar="REPORT_ID",
                       help=f"Report ID to replay. Available: {sorted(REPORT_REGISTRY.keys())}")
    group.add_argument("--timeline", action="store_true",
                       help="Print full replay timeline for all snapshots.")
    parser.add_argument("--simulate", type=int, default=14, metavar="N",
                        help="Number of simulated snapshots (default: 14).")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    snaps = _simulate_snapshots(args.simulate)

    if args.timeline:
        result = get_replay_timeline(snaps)
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_timeline(result, verbose=args.verbose)
        sys.exit(0 if result.get("replay_healthy") else 1)

    report_id = args.report.upper()
    if report_id not in REPORT_REGISTRY:
        print(f"ERROR: unknown report_id '{report_id}'. "
              f"Available: {sorted(REPORT_REGISTRY.keys())}", file=sys.stderr)
        sys.exit(1)

    result = replay_lineage(report_id, snaps)
    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_lineage(result, verbose=args.verbose)
    sys.exit(0 if result.get("replay_healthy") else 1)


if __name__ == "__main__":
    main()

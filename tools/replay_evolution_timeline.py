"""
FTD-IREL CLI: Replay Evolution Timeline.

Replays the institutional evolution timeline from simulated snapshots,
showing version transitions, governance events, and milestone events.

Usage:
    python tools/replay_evolution_timeline.py [--simulate N] [--json] [--verbose]
    python tools/replay_evolution_timeline.py --lineage [--simulate N] [--json] [--verbose]
    python tools/replay_evolution_timeline.py --regime  [--simulate N] [--json]
    python tools/replay_evolution_timeline.py --drift   [--simulate N] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.timeline_visualization import (
    build_evolution_timeline,
    build_snapshot_lineage_graph,
    build_regime_transition_map,
    build_governance_drift_flow,
    get_timeline_health,
)
from core.snapshot_manager import create_snapshot_record, SNAPSHOT_TYPES


def _simulate_snapshots(n: int) -> list:
    types = sorted(SNAPSHOT_TYPES)
    base  = 1_700_000_000_000
    snaps = []
    for i in range(n):
        s = create_snapshot_record(
            snapshot_type=types[i % len(types)],
            app_version=f"1.{i // len(types)}.0",
            trade_count=i * 80,
            label=f"snap-{i+1}",
            triggered_by="CLI_IREL_TIMELINE",
            generation_ts=base + i * 3_600_000,
        )
        snaps.append(s)
    return snaps


def _print_timeline(result: dict, verbose: bool) -> None:
    print(f"\n{'='*66}")
    print(f"  IREL Evolution Timeline")
    print(f"{'='*66}")
    print(f"  Events              : {result.get('event_count', 0)}")
    print(f"  Version transitions : {len(result.get('version_transitions', []))}")
    print(f"  Governance events   : {len(result.get('governance_events', []))}")
    print(f"  Milestone events    : {len(result.get('milestone_events', []))}")
    if verbose:
        print()
        for ev in result.get("events", []):
            flags = ""
            if ev.get("is_version_transition"): flags += " [VER]"
            if ev.get("is_governance_event"):   flags += " [GOV]"
            if ev.get("is_milestone"):          flags += " [MILESTONE]"
            if ev.get("is_critical"):           flags += " [CRITICAL]"
            print(f"  {ev['index']:3d}. {ev['snapshot_id']:32s}  "
                  f"v{ev['app_version']:8s}  {ev['snapshot_type']:22s}{flags}")
    if result.get("version_transitions"):
        print(f"\n  Version transitions:")
        for vt in result["version_transitions"]:
            print(f"    {vt['from_version']:8s} → {vt['to_version']:8s}  "
                  f"at {vt['at_snapshot_id']}")
    print(f"\n  Timeline healthy    : {result.get('timeline_healthy', False)}")
    print(f"{'='*66}\n")


def _print_lineage(result: dict, verbose: bool) -> None:
    print(f"\n{'='*66}")
    print(f"  IREL Snapshot Lineage Graph")
    print(f"{'='*66}")
    print(f"  Nodes               : {result.get('node_count', 0)}")
    print(f"  Edges               : {result.get('edge_count', 0)}")
    print(f"  Root                : {result.get('root_node', '')}")
    print(f"  Leaf                : {result.get('leaf_node', '')}")
    print(f"  Version epochs      : {list(result.get('version_epochs', {}).keys())}")
    if verbose and result.get("nodes"):
        print(f"\n  Nodes:")
        for n in result["nodes"][:15]:
            root = " [ROOT]" if n.get("is_root") else ""
            leaf = " [LEAF]" if n.get("is_leaf") else ""
            print(f"    {n['index']:3d}. {n['id']:32s}  "
                  f"v{n['app_version']:8s}  {n['snapshot_type']}{root}{leaf}")
    print(f"\n  Graph healthy       : {result.get('graph_healthy', False)}")
    print(f"{'='*66}\n")


def _print_regime(result: dict) -> None:
    print(f"\n{'='*66}")
    print(f"  IREL Regime Transition Map")
    print(f"{'='*66}")
    print(f"  Total transitions   : {result.get('total_transitions', 0)}")
    print(f"  Unique versions     : {result.get('unique_versions', [])}")
    print(f"  Unique types        : {result.get('unique_types', [])}")
    for t in result.get("transitions", [])[:10]:
        print(f"  {t['from_version']:8s}→{t['to_version']:8s}  "
              f"{t['from_type']:22s}→{t['to_type']}")
    print(f"\n  Map healthy         : {result.get('map_healthy', False)}")
    print(f"{'='*66}\n")


def _print_drift(result: dict) -> None:
    print(f"\n{'='*66}")
    print(f"  IREL Governance Drift Flow")
    print(f"{'='*66}")
    print(f"  Governance events   : {result.get('governance_events', 0)}")
    print(f"  Drift detected      : {result.get('drift_detected', False)}")
    for sig in result.get("drift_signals", []):
        print(f"  SIGNAL: {sig.get('signal_type')}  {sig}")
    print(f"\n  Flow healthy        : {result.get('flow_healthy', False)}")
    print(f"{'='*66}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay IREL evolution timeline or snapshot lineage."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--timeline", action="store_true", default=True,
                       help="Show evolution timeline (default).")
    group.add_argument("--lineage", action="store_true",
                       help="Show snapshot lineage graph.")
    group.add_argument("--regime", action="store_true",
                       help="Show regime transition map.")
    group.add_argument("--drift", action="store_true",
                       help="Show governance drift flow.")
    parser.add_argument("--simulate", type=int, default=14, metavar="N",
                        help="Number of simulated snapshots (default: 14).")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    snaps = _simulate_snapshots(args.simulate)
    health = get_timeline_health(snaps)

    if args.lineage:
        result = build_snapshot_lineage_graph(snaps)
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_lineage(result, verbose=args.verbose)
        sys.exit(0 if result.get("graph_healthy") else 1)

    if args.regime:
        result = build_regime_transition_map(snaps)
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_regime(result)
        sys.exit(0 if result.get("map_healthy") else 1)

    if args.drift:
        result = build_governance_drift_flow(snaps)
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_drift(result)
        sys.exit(0 if result.get("flow_healthy") else 1)

    # Default: evolution timeline
    result = build_evolution_timeline(snaps)
    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_timeline(result, verbose=args.verbose)
    sys.exit(0 if result.get("timeline_healthy") else 1)


if __name__ == "__main__":
    main()

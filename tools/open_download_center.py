"""
FTD-UDCA CLI: Open Download Center Governance Report.

Prints a constitutional institutional download center governance assessment:
archive browser health, replay explorer health, export preview integrity,
visualization health, and institutional search operability.

Usage:
    python tools/open_download_center.py [--json] [--verbose]
                                          [--simulate-snapshots N]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.download_dashboard import compute_download_center_governance
from core.snapshot_manager import create_snapshot_record, SNAPSHOT_TYPES
from core.report_taxonomy import BUNDLE_MEMBERSHIP


def _print_report(report: dict, verbose: bool) -> None:
    score = report.get("download_center_health_score", 0.0)
    tier  = report.get("download_center_health_tier", "UNKNOWN")
    error = report.get("error", "")

    print(f"\n{'='*66}")
    print(f"  PHOENIX Unified Institutional Download Center")
    print(f"  Constitutional Archive Experience Governance Assessment")
    print(f"{'='*66}")

    if error:
        print(f"  ERROR: {error}")
        print(f"{'='*66}\n")
        return

    print(f"  Health Score    : {score:.1f} / 100")
    print(f"  Health Tier     : {tier}")
    print(f"  Total Reports   : {report.get('total_reports', 0)}")
    print(f"  Snapshots       : {report.get('snapshots_assessed', 0)}")

    sections = [
        ("archive_browser_health",      "Archive Browser",      "browser_healthy"),
        ("replay_explorer_health",       "Replay Explorer",      "replay_healthy"),
        ("export_preview_health",        "Export Preview",       "preview_healthy"),
        ("visualization_health",         "Visualization",        "visualization_healthy"),
        ("institutional_search_health",  "Institutional Search", "search_operational"),
    ]
    print(f"\n  Component Health:")
    for key, label, ok_field in sections:
        sub    = report.get(key, {})
        ok     = sub.get(ok_field, False)
        symbol = "+" if ok else "!"
        status = "OK" if ok else "DEGRADED"
        print(f"    [{symbol}] {label:30s}  {status}")
        if verbose and not ok:
            err = sub.get("error", "")
            if err:
                print(f"          {err}")

    bundles = report.get("available_bundles", [])
    print(f"\n  Available Bundles : {', '.join(bundles)}")
    snap_types = report.get("available_snapshot_types", [])
    print(f"  Snapshot Types   : {', '.join(snap_types)}")

    recs = report.get("recommendations", [])
    print(f"\n  Recommendations ({len(recs)}):")
    for rec in recs:
        pri   = rec.get("priority", "")
        rtype = rec.get("type", "")
        summ  = rec.get("summary", "")
        auto  = rec.get("auto_authorized", False)
        print(f"    [{pri}] {rtype}")
        if verbose:
            print(f"           {summ}")
        print(f"           auto_authorized={auto}")

    if verbose:
        audit = report.get("audit_entry", {})
        print(f"\n  Audit Entry      : {audit.get('entry_id', '')}")
        print(f"  Human Approval   : {audit.get('human_approval_required', True)}")

    print(f"{'='*66}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open PHOENIX institutional download center governance report."
    )
    parser.add_argument("--json",  action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--simulate-snapshots", type=int, default=0, metavar="N",
        help="Include N simulated snapshots in the assessment.",
    )
    args = parser.parse_args()

    snapshots = []
    if args.simulate_snapshots > 0:
        types = sorted(SNAPSHOT_TYPES)
        for i in range(args.simulate_snapshots):
            s = create_snapshot_record(
                snapshot_type=types[i % len(types)],
                app_version=f"1.{i // len(types)}.0",
                trade_count=i * 50,
                triggered_by="CLI",
            )
            snapshots.append(s)

    report = compute_download_center_governance(snapshots=snapshots or None)

    if args.as_json:
        print(json.dumps(report, indent=2, default=str))
        return

    _print_report(report, verbose=args.verbose)
    tier = report.get("download_center_health_tier", "CRITICAL")
    sys.exit(0 if tier in ("HEALTHY", "ADEQUATE") else 1)


if __name__ == "__main__":
    main()

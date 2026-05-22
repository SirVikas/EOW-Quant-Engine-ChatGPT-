"""
FTD-UDCA CLI: Search Institutional Archive.

Searches the PHOENIX report registry, bundle taxonomy, and snapshot ledger.
Supports free-text query and structured filters.

Usage:
    python tools/search_archive.py reports [--query Q] [--family F] [--tier T]
                                            [--bundle B] [--no-deps] [--json]
    python tools/search_archive.py bundles [--query Q] [--min-count N]
                                            [--contains-report R] [--json]
    python tools/search_archive.py index   [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.institutional_search import (
    search_reports, search_bundles, build_search_index, get_search_health,
)


def _print_reports(result: dict, verbose: bool) -> None:
    count = result.get("result_count", 0)
    print(f"\n  Report Search Results — {count} found")
    if result.get("filters_applied"):
        print(f"  Filters: {result['filters_applied']}")
    print()
    for r in result.get("results", []):
        prio = r.get("archive_priority", "")
        fam  = r.get("report_family", "")
        tier = r.get("export_tier", "")
        print(f"  {r['report_id']:35s}  [{fam:20s}]  {tier}  {prio}")
        if verbose:
            print(f"    {r.get('description', '')}")
            if r.get("dependencies"):
                print(f"    deps: {', '.join(r['dependencies'])}")
    print()


def _print_bundles(result: dict) -> None:
    count = result.get("result_count", 0)
    print(f"\n  Bundle Search Results — {count} found\n")
    for b in result.get("results", []):
        print(f"  {b['bundle_type']:20s}  {b['report_count']} reports")
        print(f"    {', '.join(b['report_ids'])}")
    print()


def _print_index(index: dict) -> None:
    print(f"\n  Search Index Summary")
    print(f"  Total reports    : {index['total_reports']}")
    print(f"  Bundle types     : {', '.join(index['all_bundle_types'])}")
    print(f"  Report families  : {', '.join(index['all_families'])}")
    print(f"  Export tiers     : {', '.join(index['all_tiers'])}")
    print(f"  Priority levels  : {', '.join(index['all_priorities'])}")
    print(f"  Snapshot types   : {', '.join(index['all_snapshot_types'])}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search PHOENIX institutional archive."
    )
    sub = parser.add_subparsers(dest="mode", help="Search target")

    # reports subcommand
    rp = sub.add_parser("reports", help="Search the report registry.")
    rp.add_argument("--query",   "-q", default=None)
    rp.add_argument("--family",  "-f", default=None)
    rp.add_argument("--tier",    "-t", default=None)
    rp.add_argument("--bundle",  "-b", default=None)
    rp.add_argument("--priority", "-p", default=None)
    rp.add_argument("--no-deps", action="store_true",
                    help="Only primitives (no dependencies).")
    rp.add_argument("--json", action="store_true", dest="as_json")
    rp.add_argument("--verbose", action="store_true")

    # bundles subcommand
    bp = sub.add_parser("bundles", help="Search bundle taxonomy.")
    bp.add_argument("--query",           "-q", default=None)
    bp.add_argument("--min-count",       "-n", type=int, default=None)
    bp.add_argument("--contains-report", "-r", default=None)
    bp.add_argument("--json", action="store_true", dest="as_json")

    # index subcommand
    ip = sub.add_parser("index", help="Print full search index summary.")
    ip.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args()

    if args.mode == "reports":
        has_deps = False if args.no_deps else None
        result = search_reports(
            query=args.query, family=args.family, tier=args.tier,
            bundle_type=args.bundle, priority=args.priority,
            has_dependencies=has_deps,
        )
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_reports(result, verbose=args.verbose)

    elif args.mode == "bundles":
        result = search_bundles(
            query=args.query,
            min_report_count=args.min_count,
            contains_report=args.contains_report,
        )
        if args.as_json:
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_bundles(result)

    elif args.mode == "index":
        index = build_search_index()
        if args.as_json:
            print(json.dumps(index, indent=2, default=str))
        else:
            _print_index(index)

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()

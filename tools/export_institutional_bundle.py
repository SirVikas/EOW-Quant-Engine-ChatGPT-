"""
FTD-UEI CLI: Export Institutional Bundle Descriptor.

Composes a PHOENIX institutional export bundle descriptor and prints it.
This is a data descriptor — not a file export. Actual live report data
is injected at the HTTP layer.

Usage:
    python tools/export_institutional_bundle.py [--bundle BUNDLE_TYPE]
                                                [--app-version VERSION]
                                                [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.export_composer import compose_bundle, get_composer_health
from core.report_taxonomy import BUNDLE_MEMBERSHIP


def _print_summary(bundle: dict, verbose: bool) -> None:
    bt      = bundle.get("bundle_type", "UNKNOWN")
    eid     = bundle.get("export_id", "")
    count   = bundle.get("report_count", 0)
    ts      = bundle.get("generation_ts", 0)
    order   = bundle.get("export_order", [])
    meta    = bundle.get("metadata", {})
    r_hash  = meta.get("reconstruction_hash", "")[:16]
    m_hash  = meta.get("manifest_hash", "")[:16]
    error   = bundle.get("error", "")

    print(f"\n{'='*60}")
    print(f"  PHOENIX Institutional Export Bundle Descriptor")
    print(f"{'='*60}")
    if error:
        print(f"  ERROR: {error}")
        return

    print(f"  Bundle Type     : {bt}")
    print(f"  Export ID       : {eid}")
    print(f"  Report Count    : {count}")
    print(f"  Generation (ms) : {ts}")
    print(f"  Recon Hash      : {r_hash}...")
    print(f"  Manifest Hash   : {m_hash}...")
    print(f"  Auto-authorized : {bundle.get('auto_authorized', False)}")

    if verbose:
        print(f"\n  Export Order ({len(order)} reports):")
        for i, r in enumerate(order, 1):
            print(f"    {i:2d}. {r}")

        manifest = bundle.get("manifest", {})
        topo = manifest.get("bundle_topology", {})
        primitives = topo.get("primitives", [])
        if primitives:
            print(f"\n  Primitive reports (no dependencies): {', '.join(primitives)}")

    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compose a PHOENIX institutional export bundle descriptor."
    )
    parser.add_argument(
        "--bundle", default="EXECUTIVE",
        help=f"Bundle type. Available: {', '.join(sorted(BUNDLE_MEMBERSHIP))}",
    )
    parser.add_argument("--app-version", default="1.0")
    parser.add_argument("--doctrine-version", default="1.0")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--health", action="store_true",
                        help="Show composer health across all bundles instead.")
    args = parser.parse_args()

    if args.health:
        health = get_composer_health(args.app_version, args.doctrine_version)
        if args.as_json:
            print(json.dumps(health, indent=2, default=str))
        else:
            status = "HEALTHY" if health.get("composer_healthy") else "DEGRADED"
            print(f"\nBundle Composer Health: {status}")
            print(f"  Bundles composable : {health.get('bundle_count', 0)}")
            print(f"  Succeeded          : {health.get('succeeded_bundles', [])}")
            failed = health.get("failed_bundles", [])
            if failed:
                print(f"  Failed             : {failed}")
            print()
        return

    bundle_type = args.bundle.upper()
    if bundle_type not in BUNDLE_MEMBERSHIP:
        print(
            f"ERROR: unknown bundle type '{bundle_type}'. "
            f"Available: {', '.join(sorted(BUNDLE_MEMBERSHIP))}",
            file=sys.stderr,
        )
        sys.exit(1)

    bundle = compose_bundle(
        bundle_type,
        app_version=args.app_version,
        doctrine_version=args.doctrine_version,
    )

    if args.as_json:
        print(json.dumps(bundle, indent=2, default=str))
    else:
        _print_summary(bundle, verbose=args.verbose)


if __name__ == "__main__":
    main()

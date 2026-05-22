"""
FTD-UEI CLI: Verify Archive Integrity.

Composes a bundle (or all bundles) and verifies their integrity
— reconstruction hash, manifest hash, metadata compliance,
and constitutional invariants.

Usage:
    python tools/verify_archive_integrity.py [--bundle BUNDLE_TYPE | --all]
                                             [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.export_composer import compose_bundle, compose_all_bundles
from core.archive_integrity import (
    verify_bundle_integrity, assess_archive_health, detect_corruption,
)
from core.report_taxonomy import BUNDLE_MEMBERSHIP


def _print_bundle_result(result: dict, corruption: list, verbose: bool) -> None:
    bt     = result.get("bundle_type", "UNKNOWN")
    valid  = result.get("valid", False)
    issues = result.get("issues", [])
    status = "PASS" if valid else "FAIL"
    marker = "✓" if valid else "✗"

    print(f"  [{marker}] {bt:20s}  {status}", end="")
    if corruption:
        print(f"  CORRUPTION DETECTED ({len(corruption)} signal(s))", end="")
    print()

    if verbose or not valid:
        for issue in issues:
            print(f"        issue: {issue}")
        for sig in corruption:
            print(f"        corruption: {sig}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify PHOENIX archive bundle integrity."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--bundle", default="EXECUTIVE",
        help=f"Bundle type. Available: {', '.join(sorted(BUNDLE_MEMBERSHIP))}",
    )
    group.add_argument("--all", action="store_true", dest="all_bundles",
                       help="Verify all canonical bundles.")
    parser.add_argument("--app-version", default="1.0")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.all_bundles:
        bundles_map = compose_all_bundles(app_version=args.app_version)
        bundles     = list(bundles_map.values())
        health      = assess_archive_health(bundles)

        if args.as_json:
            results = {
                bt: {
                    "integrity": verify_bundle_integrity(b),
                    "corruption": detect_corruption(b),
                }
                for bt, b in bundles_map.items()
            }
            print(json.dumps({"archive_health": health, "bundle_results": results},
                             indent=2, default=str))
            return

        print(f"\n{'='*60}")
        print(f"  PHOENIX Archive Integrity — All Bundles")
        print(f"{'='*60}")
        for bt, b in bundles_map.items():
            result     = verify_bundle_integrity(b)
            corruption = detect_corruption(b)
            _print_bundle_result(result, corruption, args.verbose)

        total   = health.get("total_bundles", 0)
        healthy = health.get("healthy_bundles", 0)
        failed  = health.get("failed_bundles", [])
        arch_ok = health.get("archive_healthy", False)
        status  = "HEALTHY" if arch_ok else "DEGRADED"

        print(f"{'='*60}")
        print(f"  Archive Health : {status}  ({healthy}/{total} bundles clean)")
        if failed:
            print(f"  Failed bundles : {', '.join(failed)}")
        if health.get("corruption_detected"):
            print(f"  CORRUPTION detected in: {health.get('corrupted_bundles', [])}")
        print(f"{'='*60}\n")
        sys.exit(0 if arch_ok else 1)

    # Single bundle
    bundle_type = args.bundle.upper()
    if bundle_type not in BUNDLE_MEMBERSHIP:
        print(
            f"ERROR: unknown bundle type '{bundle_type}'. "
            f"Available: {', '.join(sorted(BUNDLE_MEMBERSHIP))}",
            file=sys.stderr,
        )
        sys.exit(1)

    bundle     = compose_bundle(bundle_type, app_version=args.app_version)
    result     = verify_bundle_integrity(bundle)
    corruption = detect_corruption(bundle)

    if args.as_json:
        print(json.dumps({"integrity": result, "corruption": corruption},
                         indent=2, default=str))
        return

    print(f"\n{'='*60}")
    print(f"  PHOENIX Archive Integrity — {bundle_type}")
    print(f"{'='*60}")
    _print_bundle_result(result, corruption, verbose=True)
    print(f"{'='*60}\n")
    sys.exit(0 if result["valid"] and not corruption else 1)


if __name__ == "__main__":
    main()

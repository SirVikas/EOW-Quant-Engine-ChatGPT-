"""
FTD-UEI CLI: Analyze Export Ecosystem Governance.

Runs the full constitutional export infrastructure governance assessment
and prints a human-readable report. Covers bundle composer health,
manifest generation, reconstruction hashing, archive integrity,
snapshot continuity, export ordering, and metadata compliance.

Usage:
    python tools/analyze_export_ecosystem.py [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.download_center import compute_export_infrastructure_governance
from core.snapshot_manager import create_snapshot_record


def _print_report(report: dict, verbose: bool) -> None:
    score  = report.get("infrastructure_health_score", 0.0)
    tier   = report.get("infrastructure_health_tier", "UNKNOWN")
    error  = report.get("error", "")

    print(f"\n{'='*64}")
    print(f"  PHOENIX Export Ecosystem Governance Assessment")
    print(f"{'='*64}")

    if error:
        print(f"  ERROR: {error}")
        print(f"{'='*64}\n")
        return

    print(f"  Health Score    : {score:.1f} / 100")
    print(f"  Health Tier     : {tier}")

    sections = [
        ("bundle_composer_health",     "Bundle Composer",        "composer_healthy"),
        ("manifest_generation_health", "Manifest Generation",    "manifest_generation_healthy"),
        ("hash_infrastructure_health", "Reconstruction Hashing", "hashing_operational"),
        ("archive_integrity_health",   "Archive Integrity",      "integrity_checks_operational"),
        ("export_ordering_health",     "Export Ordering",        "topological_sort_valid"),
    ]

    print(f"\n  Component Health:")
    for key, label, ok_field in sections:
        sub    = report.get(key, {})
        ok     = sub.get(ok_field, False)
        symbol = "✓" if ok else "✗"
        status = "OK" if ok else "DEGRADED"
        print(f"    [{symbol}] {label:30s}  {status}")
        if verbose and not ok:
            err = sub.get("error", sub.get("issues", []))
            print(f"          detail: {err}")

    snap = report.get("snapshot_health", {})
    snap_count = snap.get("total_snapshots", 0)
    print(f"\n  Snapshot Health : {snap_count} snapshots assessed")

    meta = report.get("export_metadata_compliance", {})
    fcount = meta.get("required_field_count", 0)
    print(f"  Metadata Schema : {fcount} required fields defined")

    bundles = report.get("available_bundles", [])
    print(f"  Available Bundles: {', '.join(bundles)}")

    recs = report.get("recommendations", [])
    print(f"\n  Recommendations ({len(recs)}):")
    for rec in recs:
        pri  = rec.get("priority", "")
        rtype = rec.get("type", "")
        summ = rec.get("summary", "")
        auto = rec.get("auto_authorized", False)
        print(f"    [{pri}] {rtype}")
        print(f"           {summ}")
        print(f"           auto_authorized={auto}")

    if verbose:
        audit = report.get("audit_entry", {})
        print(f"\n  Audit Entry     : {audit.get('entry_id', '')}")
        print(f"  Human Approval  : {audit.get('human_approval_required', True)}")

    principles = report.get("export_hard_principles", {})
    violations = [k for k, v in principles.items() if not v and "autonomous" not in k.lower() and "silent" not in k.lower() and "self_auth" not in k.lower()]
    if violations:
        print(f"\n  CONSTITUTIONAL VIOLATIONS: {violations}")

    print(f"{'='*64}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze PHOENIX export ecosystem governance."
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--with-snapshots", type=int, default=0, metavar="N",
        help="Include N simulated snapshots in the assessment.",
    )
    args = parser.parse_args()

    snapshots = []
    if args.with_snapshots > 0:
        from core.snapshot_manager import SNAPSHOT_TYPES
        types = sorted(SNAPSHOT_TYPES)
        for i in range(args.with_snapshots):
            s = create_snapshot_record(
                snapshot_type=types[i % len(types)],
                app_version=f"1.{i // len(types)}.0",
                trade_count=i * 50,
                triggered_by="CLI",
            )
            snapshots.append(s)

    report = compute_export_infrastructure_governance(snapshots=snapshots)

    if args.as_json:
        print(json.dumps(report, indent=2, default=str))
        return

    _print_report(report, verbose=args.verbose)
    tier = report.get("infrastructure_health_tier", "CRITICAL")
    sys.exit(0 if tier in ("HEALTHY", "ADEQUATE") else 1)


if __name__ == "__main__":
    main()

"""
FTD-IREL CLI: Generate Institutional Governance Report.

Generates a constitutional governance report covering the GOVERNANCE,
CONTINUITY, and HUMAN_ALIGNMENT report families.

Usage:
    python tools/generate_governance_report.py [--format FORMAT] [--out FILE]
    python tools/generate_governance_report.py --health
    python tools/generate_governance_report.py --downloads [--json]

Formats: html, markdown
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.export_presentation import generate_governance_html, generate_research_markdown
from core.download_experience import (
    list_available_downloads, get_download_experience_health,
    orchestrate_download,
)


def _print_health(health: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  IREL Download Experience Health")
    print(f"{'='*60}")
    print(f"  Operational           : {health.get('download_experience_operational', False)}")
    print(f"  Orchestrate OK        : {health.get('orchestrate_ok', False)}")
    print(f"  Metadata OK           : {health.get('metadata_ok', False)}")
    print(f"  Manifest OK           : {health.get('manifest_ok', False)}")
    print(f"  Available downloads OK: {health.get('available_downloads_ok', False)}")
    print(f"  Experience healthy    : {health.get('download_experience_healthy', False)}")
    print(f"  Registered reports    : {health.get('registered_report_count', 0)}")
    print(f"  Modes                 : {', '.join(health.get('supported_modes', []))}")
    print(f"  Formats               : {', '.join(health.get('supported_formats', []))}")
    print(f"{'='*60}\n")


def _print_downloads(avail: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  Available Institutional Downloads")
    print(f"{'='*60}")
    print(f"  Bundles ({avail.get('bundle_count', 0)}):")
    for b in avail.get("bundles", []):
        print(f"    {b['bundle_name']:20s}  {b['report_count']:3d} reports  "
              f"{b.get('description', '')}")
    print(f"\n  Families ({avail.get('family_count', 0)}):")
    for f in avail.get("families", []):
        print(f"    {f['family']:24s}  {f['report_count']:3d} reports")
    print(f"\n  Formats : {', '.join(avail.get('formats', []))}")
    print(f"  Modes   : {', '.join(avail.get('modes', []))}")
    print(f"  auto_authorized = {avail.get('auto_authorized', False)}")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PHOENIX constitutional governance report."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--health", action="store_true",
                       help="Show download experience health and exit.")
    group.add_argument("--downloads", action="store_true",
                       help="List all available download targets and exit.")
    parser.add_argument("--format", default="html",
                        choices=["html", "markdown"],
                        help="Output format (default: html).")
    parser.add_argument("--version", default="1.27.0", metavar="VER",
                        help="App version string (default: 1.27.0).")
    parser.add_argument("--out", metavar="FILE",
                        help="Write output to FILE instead of stdout.")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Output download list as JSON (with --downloads).")
    args = parser.parse_args()

    if args.health:
        health = get_download_experience_health()
        _print_health(health)
        sys.exit(0 if health.get("download_experience_healthy") else 1)

    if args.downloads:
        avail = list_available_downloads(args.version)
        if args.as_json:
            print(json.dumps(avail, indent=2, default=str))
        else:
            _print_downloads(avail)
        sys.exit(0)

    # Generate governance report
    bundle_data: dict = {}
    if args.format == "html":
        output = generate_governance_html(bundle_data, app_version=args.version)
    else:
        # Markdown: use research markdown (governance families are included)
        output = generate_research_markdown(bundle_data, app_version=args.version)

    # Also emit a governance download plan (informational only, not executed)
    plan = orchestrate_download(
        "governance_export", "", args.format, args.version
    )
    plan_info = (
        f"<!-- Governance download plan: {plan.get('plan_id', '')} "
        f"| reports={plan.get('report_count', 0)} "
        f"| auto_authorized=False -->"
        if args.format == "html"
        else f"\n_Download plan: {plan.get('plan_id', '')} | auto_authorized=False_\n"
    )
    output = output + ("\n" if not output.endswith("\n") else "") + plan_info

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Governance report ({args.format}) written to: {args.out}")
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()

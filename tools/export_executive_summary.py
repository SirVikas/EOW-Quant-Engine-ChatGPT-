"""
FTD-IREL CLI: Export Executive Summary.

Generates an institutional executive summary in the chosen format.
Outputs to stdout or a file.

Usage:
    python tools/export_executive_summary.py [--format FORMAT] [--out FILE]
    python tools/export_executive_summary.py --health

Formats: html, markdown, governance_html, archive_html
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.export_presentation import (
    generate_executive_html,
    generate_research_markdown,
    generate_governance_html,
    generate_archive_page,
    get_presentation_health,
)

_FORMATS = ["html", "markdown", "governance_html", "archive_html"]


def _print_health(health: dict) -> None:
    print(f"\n{'='*56}")
    print(f"  IREL Presentation Health")
    print(f"{'='*56}")
    print(f"  Operational           : {health.get('presentation_operational', False)}")
    print(f"  Executive HTML OK     : {health.get('executive_html_ok', False)}")
    print(f"  Research Markdown OK  : {health.get('research_markdown_ok', False)}")
    print(f"  Governance HTML OK    : {health.get('governance_html_ok', False)}")
    print(f"  Archive Page OK       : {health.get('archive_page_ok', False)}")
    print(f"  Presentation healthy  : {health.get('presentation_healthy', False)}")
    print(f"  Formats               : {', '.join(health.get('supported_formats', []))}")
    print(f"{'='*56}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export PHOENIX executive summary in institutional format."
    )
    parser.add_argument("--health", action="store_true",
                        help="Show presentation layer health and exit.")
    parser.add_argument("--format", default="html",
                        choices=_FORMATS,
                        help="Output format (default: html).")
    parser.add_argument("--version", default="1.27.0", metavar="VER",
                        help="App version string (default: 1.27.0).")
    parser.add_argument("--out", metavar="FILE",
                        help="Write output to FILE instead of stdout.")
    args = parser.parse_args()

    if args.health:
        health = get_presentation_health()
        _print_health(health)
        sys.exit(0 if health.get("presentation_healthy") else 1)

    # Generate the requested format with empty bundle_data
    # (when run standalone, actual data would be injected via API)
    bundle_data: dict = {}

    if args.format == "html":
        output = generate_executive_html(bundle_data, app_version=args.version)
    elif args.format == "markdown":
        output = generate_research_markdown(bundle_data, app_version=args.version)
    elif args.format == "governance_html":
        output = generate_governance_html(bundle_data, app_version=args.version)
    elif args.format == "archive_html":
        output = generate_archive_page(bundle_data, app_version=args.version)
    else:
        print(f"ERROR: unknown format '{args.format}'", file=sys.stderr)
        sys.exit(1)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Exported '{args.format}' to: {args.out}")
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()

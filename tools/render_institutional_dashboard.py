"""
FTD-IREL CLI: Render Institutional Dashboard.

Renders the full registry-driven institutional dashboard in the chosen mode.
Outputs to stdout or a file.

Usage:
    python tools/render_institutional_dashboard.py [--mode MODE] [--out FILE]
    python tools/render_institutional_dashboard.py --health
    python tools/render_institutional_dashboard.py --tabs

Modes: html, executive_html, governance_html, research_html, archive_html,
       json, markdown
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.institutional_report_renderer import render_report_bundle, get_renderer_health, RENDER_MODES
from core.dashboard_orchestrator import build_tab_manifest, get_orchestrator_health


def _print_tabs(manifest: dict) -> None:
    print(f"\n{'='*64}")
    print(f"  Institutional Dashboard — Tab Manifest")
    print(f"{'='*64}")
    print(f"  Tab count             : {manifest.get('tab_count', 0)}")
    print(f"  Total mapped reports  : {manifest.get('total_mapped_reports', 0)}")
    print(f"  Registry reports      : {manifest.get('registry_report_count', 0)}")
    print(f"  Manifest complete     : {manifest.get('manifest_complete', False)}")
    print()
    for tab in manifest.get("tabs", []):
        print(f"  [{tab['icon']}] {tab['label']:18s}  "
              f"reports={tab['report_count']:2d}  id={tab['tab_id']}")
    print(f"{'='*64}\n")


def _print_health(health: dict) -> None:
    print(f"\n{'='*56}")
    print(f"  IREL Renderer Health")
    print(f"{'='*56}")
    print(f"  Operational           : {health.get('renderer_operational', False)}")
    print(f"  Registered reports    : {health.get('registered_report_count', 0)}")
    print(f"  HTML render OK        : {health.get('html_render_ok', False)}")
    print(f"  JSON render OK        : {health.get('json_render_ok', False)}")
    print(f"  Markdown render OK    : {health.get('markdown_render_ok', False)}")
    print(f"  Renderer healthy      : {health.get('renderer_healthy', False)}")
    print(f"  Supported modes       : {', '.join(health.get('supported_modes', []))}")
    print(f"{'='*56}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the PHOENIX institutional dashboard."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--health", action="store_true",
                       help="Show renderer health status and exit.")
    group.add_argument("--tabs", action="store_true",
                       help="Show institutional tab manifest and exit.")
    parser.add_argument("--mode", default="json",
                        choices=sorted(RENDER_MODES),
                        help="Render mode (default: json).")
    parser.add_argument("--out", metavar="FILE",
                        help="Write output to FILE instead of stdout.")
    args = parser.parse_args()

    if args.health:
        rh = get_renderer_health()
        oh = get_orchestrator_health()
        _print_health(rh)
        print(f"  Orchestrator healthy  : {oh.get('orchestrator_healthy', False)}")
        print(f"  Tab count             : {oh.get('tab_count', 0)}")
        print(f"  Manifest complete     : {oh.get('manifest_complete', False)}\n")
        sys.exit(0 if rh.get("renderer_healthy") and oh.get("orchestrator_healthy") else 1)

    if args.tabs:
        manifest = build_tab_manifest()
        _print_tabs(manifest)
        sys.exit(0 if manifest.get("manifest_complete") else 1)

    result = render_report_bundle({}, mode=args.mode, app_version="1.27.0")

    if args.mode == "json":
        output = json.dumps(result, indent=2, default=str)
    else:
        output = result if isinstance(result, str) else json.dumps(result, indent=2, default=str)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Rendered '{args.mode}' to: {args.out}")
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()

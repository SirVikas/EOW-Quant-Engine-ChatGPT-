"""
FTD-IREL: Institutional Report Renderer.

Registry-driven dynamic rendering engine for PHOENIX institutional reports.
Auto-discovers all registered reports, groups by family, orders topologically,
and renders to HTML/JSON/Markdown without hardcoded section references.

Supported modes: html, executive_html, governance_html, research_html,
                 archive_html, json, markdown

Constitutional requirement: render_constitutional_banner() must always be called
and its output included in every rendered report.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Callable, Dict, List, Optional, Union

from core.report_registry import (
    REPORT_REGISTRY,
    TIER_CORE, TIER_GOVERNANCE,
    FAMILY_GOVERNANCE, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT,
    KNOWN_FAMILIES,
)
from core.report_dependency_graph import topological_sort
from core.timeline_visualization import build_evolution_timeline

# ── Supported render modes ────────────────────────────────────────────────────
RENDER_MODES: frozenset = frozenset({
    "html",
    "executive_html",
    "governance_html",
    "research_html",
    "archive_html",
    "json",
    "markdown",
})

# ── Inline CSS palette — matches dashboard aesthetic ─────────────────────────
_CSS = """
<style>
  :root {
    --c-green:  #276749; --c-blue:  #2B6CB0; --c-red:    #9B2C2C;
    --c-amber:  #92400E; --c-teal:  #234E52; --c-purple: #553C9A;
    --c-gray:   #4A5568; --c-mint:  #1D4044; --c-sky:    #1A365D;
    --c-bg:     #F7FAFC; --c-card:  #FFFFFF; --c-border: #E2E8F0;
    --c-text:   #1A202C;
  }
  body { font-family: 'DM Sans', system-ui, sans-serif; background: var(--c-bg);
         color: var(--c-text); margin: 0; padding: 0; }
  .irel-wrapper { max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }
  .irel-banner  { background: #1A202C; color: #F7FAFC; padding: 1.25rem 1.5rem;
                  border-radius: 8px; margin-bottom: 1.5rem; }
  .irel-banner h1 { margin: 0 0 .4rem; font-size: 1.2rem; }
  .irel-banner p  { margin: .15rem 0; font-size: .875rem; opacity: .85; }
  .irel-family    { margin-bottom: 2rem; }
  .irel-family h2 { font-size: 1rem; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .06em; border-bottom: 2px solid var(--c-border);
                    padding-bottom: .4rem; margin-bottom: .8rem; }
  .irel-section   { background: var(--c-card); border: 1px solid var(--c-border);
                    border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: .6rem; }
  .irel-section h3 { margin: 0 0 .3rem; font-size: .95rem; }
  .irel-section .desc { font-size: .82rem; color: var(--c-gray); margin: .2rem 0; }
  .irel-section .pending { font-size: .8rem; color: #A0AEC0; font-style: italic; }
  .badge { display: inline-block; border-radius: 4px; padding: .15rem .5rem;
           font-size: .75rem; font-weight: 600; color: #fff; }
  .bg-green  { background: var(--c-green);  }
  .bg-blue   { background: var(--c-blue);   }
  .bg-red    { background: var(--c-red);    }
  .bg-amber  { background: var(--c-amber);  }
  .bg-purple { background: var(--c-purple); }
  .bg-teal   { background: var(--c-teal);   }
  .bg-gray   { background: var(--c-gray);   }
  .kv-row    { display: flex; gap: .5rem; font-size: .82rem; margin: .15rem 0; }
  .kv-row .k { font-weight: 600; min-width: 6rem; }
  .download-section { margin-top: 2rem; padding: 1rem 1.25rem;
                      background: #EBF8FF; border-radius: 6px;
                      border: 1px solid #BEE3F8; }
</style>
"""

_FAMILY_BG: Dict[str, str] = {
    "ECONOMIC":        "bg-green",
    "COGNITIVE":       "bg-blue",
    "GOVERNANCE":      "bg-purple",
    "EPISTEMIC":       "bg-teal",
    "CONTINUITY":      "bg-amber",
    "HUMAN_ALIGNMENT": "bg-teal",
    "REPLAY":          "bg-blue",
    "FORENSICS":       "bg-gray",
}


# ── Public API ────────────────────────────────────────────────────────────────

def render_constitutional_banner() -> dict:
    """
    Constitutional governance notice — must be included in every rendered report.
    auto_authorized is always False; human authority is always True.
    """
    return {
        "component_type":   "constitutional_banner",
        "title":            "PHOENIX Constitutional Governance Notice",
        "principles": [
            "All institutional reports are research instruments — not trading instructions.",
            "Human authority is required for all governance and deployment decisions.",
            "No report output is autonomously authorized to modify engine behaviour.",
            "Export and dissemination requires explicit human approval.",
            "Lineage and reconstruction records are immutable once generated.",
            "Report registry governance remains permanently under human constitutional authority.",
        ],
        "auto_authorized": False,
        "human_authority": True,
    }


def render_report_section(report_id: str, report_data: dict) -> dict:
    """
    Build structured rendering metadata for a single report.
    Derives health_indicator from score fields when present.
    """
    try:
        meta = REPORT_REGISTRY.get(report_id, {})
        has_data = bool(report_data)
        data_keys = sorted(report_data.keys()) if has_data else []

        # Derive health indicator from known score fields (best-effort)
        score = None
        for field in ("score", "health_score", "infrastructure_health_score",
                      "irel_health_score", "download_center_health_score"):
            if field in report_data:
                try:
                    score = float(report_data[field])
                    break
                except (TypeError, ValueError):
                    pass

        if score is None:
            health_indicator = "UNKNOWN"
        elif score >= 80:
            health_indicator = "HEALTHY"
        elif score >= 60:
            health_indicator = "ADEQUATE"
        elif score >= 40:
            health_indicator = "VULNERABLE"
        else:
            health_indicator = "CRITICAL"

        return {
            "report_id":          report_id,
            "name":               meta.get("name", report_id),
            "family":             meta.get("report_family", ""),
            "tier":               meta.get("export_tier", ""),
            "priority":           meta.get("archive_priority", ""),
            "endpoint":           meta.get("endpoint", ""),
            "bundle_key":         meta.get("bundle_key", ""),
            "description":        meta.get("description", ""),
            "constitutional_scope": meta.get("constitutional_scope", ""),
            "has_data":           has_data,
            "data_keys":          data_keys,
            "health_indicator":   health_indicator,
            "component_count":    len(data_keys),
        }
    except Exception as exc:
        return {
            "report_id":      report_id,
            "has_data":       False,
            "data_keys":      [],
            "health_indicator": "UNKNOWN",
            "component_count": 0,
            "error":          str(exc),
        }


def render_lineage_timeline(snapshots: list) -> dict:
    """Wraps build_evolution_timeline with rendering metadata."""
    try:
        evo = build_evolution_timeline(snapshots or [])
        return {
            "component_type":    "lineage_timeline",
            "timeline_data":     evo,
            "snapshot_count":    len(snapshots or []),
            "render_mode":       "EVOLUTION_TIMELINE",
            "auto_authorized":   False,
        }
    except Exception as exc:
        return {
            "component_type":  "lineage_timeline",
            "timeline_data":   {},
            "snapshot_count":  0,
            "render_mode":     "EVOLUTION_TIMELINE",
            "auto_authorized": False,
            "error":           str(exc),
        }


def render_download_center(available_bundles: Optional[List[str]] = None) -> dict:
    """
    Download center component descriptor.
    Lists available bundles and export formats.
    auto_authorized is always False per constitutional requirement.
    """
    from core.report_taxonomy import BUNDLE_MEMBERSHIP
    bundles = available_bundles if available_bundles is not None else sorted(BUNDLE_MEMBERSHIP.keys())

    _bundle_descriptions = {
        "EXECUTIVE":      "High-level institutional summary — 7 core reports",
        "RESEARCH":       "Full research suite — 11 deep-analysis reports",
        "GOVERNANCE":     "Constitutional governance package — 8 reports",
        "EPISTEMIC":      "Scientific evidence package — 3 reports",
        "CONTINUITY":     "Continuity & lineage package — 5 reports",
        "MASTER_ARCHIVE": "Complete institutional archive — all 25 reports",
    }
    from core.report_taxonomy import BUNDLE_MEMBERSHIP as _BM
    bundle_list = [
        {
            "bundle_type":  b,
            "report_count": len(_BM.get(b, set())),
            "description":  _bundle_descriptions.get(b, b),
        }
        for b in bundles
    ]
    return {
        "component_type":  "download_center",
        "bundles":         bundle_list,
        "formats":         ["html", "json", "markdown", "zip", "pdf_ready_html"],
        "auto_authorized": False,
    }


def render_report_bundle(
    bundle_data: dict,
    mode: str = "html",
    app_version: str = "1.0",
) -> Union[str, dict]:
    """
    Registry-driven bundle renderer.

    For json mode: returns a dict with sections list, metadata, and constitutional banner.
    For html/executive_html/governance_html/research_html/archive_html: returns HTML string.
    For markdown mode: returns a markdown string.

    If mode is not in RENDER_MODES, falls back to 'html'.
    Never raises — returns an error indicator on failure.
    """
    try:
        effective_mode = mode if mode in RENDER_MODES else "html"

        # Define which reports to include per mode
        if effective_mode == "executive_html":
            def _filter(meta: dict) -> bool:
                return meta.get("export_tier") in (TIER_CORE, TIER_GOVERNANCE)
            title = f"PHOENIX Executive Report — v{app_version}"
        elif effective_mode == "governance_html":
            def _filter(meta: dict) -> bool:
                return meta.get("report_family") in (
                    FAMILY_GOVERNANCE, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT
                )
            title = f"PHOENIX Governance Report — v{app_version}"
        elif effective_mode == "archive_html":
            def _filter(meta: dict) -> bool:
                return True
            title = f"PHOENIX Archive Report — v{app_version}"
        elif effective_mode in ("html", "research_html"):
            def _filter(meta: dict) -> bool:
                return True
            title = f"PHOENIX Institutional Report — v{app_version}"
        else:
            def _filter(meta: dict) -> bool:  # json, markdown
                return True
            title = f"PHOENIX Institutional Report — v{app_version}"

        if effective_mode == "json":
            sections = []
            topo = topological_sort()
            for report_id in topo:
                meta = REPORT_REGISTRY.get(report_id, {})
                if not _filter(meta):
                    continue
                bk = meta.get("bundle_key", report_id.lower())
                data = bundle_data.get(bk, {})
                sections.append(render_report_section(report_id, data))
            return {
                "render_mode":          effective_mode,
                "app_version":          app_version,
                "title":                title,
                "sections":             sections,
                "section_count":        len(sections),
                "constitutional_banner": render_constitutional_banner(),
                "generated_at_ms":      int(_time.time() * 1000),
                "auto_authorized":      False,
            }

        if effective_mode == "markdown":
            return _render_markdown_report(bundle_data)

        # All HTML modes
        return _render_html_report(bundle_data, title, _filter,
                                   include_download=(effective_mode in ("html", "archive_html")))

    except Exception as exc:
        if mode == "json":
            return {
                "render_mode":  mode,
                "error":        str(exc),
                "sections":     [],
                "constitutional_banner": render_constitutional_banner(),
                "auto_authorized": False,
            }
        return f"<!-- render error: {exc} -->"


# ── Private helpers ───────────────────────────────────────────────────────────

def _render_html_report(
    bundle_data: dict,
    title: str,
    report_filter_fn: Callable,
    include_download: bool = False,
) -> str:
    """
    Build a full self-contained HTML string.
    Groups sections by family, renders constitutional banner header,
    and optionally appends the download center block.
    """
    try:
        banner = render_constitutional_banner()
        topo   = topological_sort()

        # Group reports by family in topo order
        family_sections: Dict[str, List[dict]] = {}
        for report_id in topo:
            meta = REPORT_REGISTRY.get(report_id, {})
            if not report_filter_fn(meta):
                continue
            family = meta.get("report_family", "OTHER")
            bk     = meta.get("bundle_key", report_id.lower())
            data   = bundle_data.get(bk, {})
            sec    = render_report_section(report_id, data)
            family_sections.setdefault(family, []).append(sec)

        # Build HTML
        ts_str = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
        lines: List[str] = [
            "<!DOCTYPE html><html lang='en'><head>",
            f"<meta charset='UTF-8'><title>{title}</title>",
            _CSS,
            "</head><body><div class='irel-wrapper'>",
            # Constitutional banner
            "<div class='irel-banner'>",
            f"<h1>{banner['title']}</h1>",
        ]
        for p in banner["principles"]:
            lines.append(f"<p>&#x2022; {p}</p>")
        lines.append(f"<p style='margin-top:.6rem;font-size:.75rem;opacity:.6'>"
                     f"Generated: {ts_str} | human_authority=True | auto_authorized=False</p>")
        lines.append("</div>")  # end banner

        # Family sections
        for family in sorted(family_sections.keys()):
            sections = family_sections[family]
            bg = _FAMILY_BG.get(family, "bg-gray")
            lines.append("<div class='irel-family'>")
            lines.append(f"<h2><span class='badge {bg}'>{family}</span></h2>")
            for sec in sections:
                lines.append("<div class='irel-section'>")
                h_badge_bg = {
                    "HEALTHY": "bg-green", "ADEQUATE": "bg-blue",
                    "VULNERABLE": "bg-amber", "CRITICAL": "bg-red",
                }.get(sec["health_indicator"], "bg-gray")
                lines.append(
                    f"<h3>{sec.get('name', sec['report_id'])} "
                    f"<span class='badge {h_badge_bg}' style='font-size:.7rem'>"
                    f"{sec['health_indicator']}</span></h3>"
                )
                lines.append(f"<p class='desc'>{sec.get('description', '')}</p>")
                lines.append(
                    f"<div class='kv-row'><span class='k'>Tier:</span>{sec.get('tier','')}"
                    f"&nbsp; <span class='k'>Priority:</span>{sec.get('priority','')}"
                    f"&nbsp; <span class='k'>Scope:</span>{sec.get('constitutional_scope','')}</div>"
                )
                if sec["has_data"]:
                    lines.append(
                        f"<div class='kv-row'><span class='k'>Fields:</span>"
                        f"{sec['component_count']} data keys present</div>"
                    )
                else:
                    lines.append("<p class='pending'>&#x23F3; Data pending — endpoint not yet called.</p>")
                lines.append("</div>")  # end section
            lines.append("</div>")  # end family

        if include_download:
            dc = render_download_center()
            lines.append("<div class='download-section'>")
            lines.append("<h2 style='margin:0 0 .6rem;font-size:.95rem'>Download Center</h2>")
            for b in dc["bundles"]:
                lines.append(
                    f"<div class='kv-row'><span class='k'>{b['bundle_type']}</span>"
                    f"{b['description']} ({b['report_count']} reports)</div>"
                )
            lines.append(
                "<p style='font-size:.75rem;margin-top:.6rem;color:#4A5568'>"
                "Formats: " + ", ".join(dc["formats"]) + " | auto_authorized=False</p>"
            )
            lines.append("</div>")

        lines.append("</div></body></html>")
        return "\n".join(lines)

    except Exception as exc:
        return f"<!DOCTYPE html><html><body><p>Render error: {exc}</p></body></html>"


def _render_markdown_report(bundle_data: dict) -> str:
    """Generate a full markdown research report from bundle_data."""
    try:
        topo    = topological_sort()
        ts_str  = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
        lines: List[str] = [
            "# PHOENIX Institutional Report",
            "",
            f"_Generated: {ts_str}_",
            "",
            "## Constitutional Notice",
            "",
            "> All outputs are research instruments only. "
            "Human authority required for all governance decisions. "
            "auto_authorized=False.",
            "",
        ]

        # Group by family
        family_sections: Dict[str, List[dict]] = {}
        for report_id in topo:
            meta   = REPORT_REGISTRY.get(report_id, {})
            family = meta.get("report_family", "OTHER")
            bk     = meta.get("bundle_key", report_id.lower())
            data   = bundle_data.get(bk, {})
            sec    = render_report_section(report_id, data)
            family_sections.setdefault(family, []).append(sec)

        for family in sorted(family_sections.keys()):
            lines.append(f"## {family}")
            lines.append("")
            for sec in family_sections[family]:
                lines.append(f"### {sec.get('name', sec['report_id'])}")
                lines.append("")
                lines.append(f"**ID:** `{sec['report_id']}` | "
                             f"**Tier:** {sec.get('tier','')} | "
                             f"**Priority:** {sec.get('priority','')} | "
                             f"**Health:** {sec['health_indicator']}")
                lines.append("")
                lines.append(f"_{sec.get('description', '')}_")
                lines.append("")
                if sec["has_data"]:
                    lines.append(f"Data present — {sec['component_count']} fields.")
                else:
                    lines.append("_Data pending — endpoint not yet called._")
                lines.append("")

        return "\n".join(lines)

    except Exception as exc:
        return f"# PHOENIX Institutional Report\n\n_Render error: {exc}_\n"


# ── Health check ──────────────────────────────────────────────────────────────

def get_renderer_health() -> dict:
    """
    Spot-checks render_report_bundle with an empty dict in html mode.
    Returns health summary — never raises.
    """
    try:
        result   = render_report_bundle({}, mode="html", app_version="1.0")
        html_ok  = isinstance(result, str) and len(result) > 100
        json_res = render_report_bundle({}, mode="json", app_version="1.0")
        json_ok  = isinstance(json_res, dict) and "sections" in json_res
        md_res   = render_report_bundle({}, mode="markdown", app_version="1.0")
        md_ok    = isinstance(md_res, str) and len(md_res) > 20
        renderer_healthy = html_ok and json_ok and md_ok
        return {
            "renderer_operational":   True,
            "supported_modes":        sorted(RENDER_MODES),
            "registered_report_count": len(REPORT_REGISTRY),
            "html_render_ok":         html_ok,
            "json_render_ok":         json_ok,
            "markdown_render_ok":     md_ok,
            "renderer_healthy":       renderer_healthy,
        }
    except Exception as exc:
        return {
            "renderer_operational":   False,
            "supported_modes":        sorted(RENDER_MODES),
            "registered_report_count": len(REPORT_REGISTRY),
            "renderer_healthy":       False,
            "error":                  str(exc),
        }

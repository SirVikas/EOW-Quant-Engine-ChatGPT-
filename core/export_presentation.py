"""
FTD-IREL: Advanced Export Presentation Layer.

Generates formatted institutional outputs: executive HTML, research markdown,
governance HTML, and institutional archive pages.

All outputs are self-contained strings (no file I/O).
Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Dict, List

from core.report_registry import (
    REPORT_REGISTRY,
    FAMILY_GOVERNANCE, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT,
)
from core.report_dependency_graph import topological_sort
from core.report_taxonomy import BUNDLE_MEMBERSHIP

# ── Shared CSS snippet (compact — executive view) ─────────────────────────────
_BASE_CSS = """<style>
  body{font-family:'DM Sans',system-ui,sans-serif;background:#F7FAFC;
       color:#1A202C;margin:0;padding:0}
  .wrap{max-width:960px;margin:0 auto;padding:1.5rem}
  .hdr{background:#1A202C;color:#F7FAFC;padding:1rem 1.25rem;border-radius:6px;
       margin-bottom:1.25rem}
  .hdr h1{margin:0;font-size:1.1rem}
  .hdr p{margin:.2rem 0;font-size:.8rem;opacity:.8}
  .card{background:#fff;border:1px solid #E2E8F0;border-radius:6px;
        padding:.85rem 1rem;margin-bottom:.5rem}
  .card h3{margin:0 0 .25rem;font-size:.9rem}
  .card .desc{font-size:.8rem;color:#718096;margin:.1rem 0}
  .badge{display:inline-block;border-radius:3px;padding:.1rem .45rem;
         font-size:.72rem;font-weight:600;color:#fff}
  .bg-g{background:#276749}.bg-b{background:#2B6CB0}
  .bg-r{background:#9B2C2C}.bg-a{background:#92400E}
  .bg-p{background:#553C9A}.bg-t{background:#234E52}
  .bg-grey{background:#4A5568}
  .kv{font-size:.78rem;margin:.1rem 0;display:flex;gap:.4rem}
  .kv .k{font-weight:600;min-width:5.5rem}
  .pending{font-size:.77rem;color:#A0AEC0;font-style:italic}
  .notice{background:#EBF8FF;border:1px solid #BEE3F8;border-radius:6px;
          padding:.75rem 1rem;margin-bottom:1rem;font-size:.8rem}
  table{border-collapse:collapse;width:100%;font-size:.8rem;margin:.5rem 0}
  th,td{border:1px solid #E2E8F0;padding:.35rem .6rem;text-align:left}
  th{background:#EDF2F7;font-weight:600}
  h2{font-size:.95rem;font-weight:700;text-transform:uppercase;
     letter-spacing:.05em;border-bottom:2px solid #E2E8F0;
     padding-bottom:.3rem;margin:.9rem 0 .6rem}
</style>"""

_GOV_FAMILIES = {FAMILY_GOVERNANCE, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT}

_FAMILY_BG: Dict[str, str] = {
    "ECONOMIC": "bg-g", "COGNITIVE": "bg-b", "GOVERNANCE": "bg-p",
    "EPISTEMIC": "bg-t", "CONTINUITY": "bg-a", "HUMAN_ALIGNMENT": "bg-t",
    "REPLAY": "bg-b", "FORENSICS": "bg-grey",
}

_HARD_PRINCIPLES = [
    ("human_authority_over_reporting",        True),
    ("registry_driven_rendering_enforced",    True),
    ("constitutional_banner_mandatory",        True),
    ("export_approval_required",              True),
    ("lineage_rendering_immutable",           True),
    ("autonomous_reporting_governance",       False),
    ("sovereign_visual_interpretation",       False),
    ("autonomous_dashboard_rewriting",        False),
]


def _ts_str() -> str:
    return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())


def _health_badge(score) -> str:
    """Return a colored badge string for an optional numeric score."""
    try:
        s = float(score)
        if s >= 80:
            return "<span class='badge bg-g'>HEALTHY</span>"
        elif s >= 60:
            return "<span class='badge bg-b'>ADEQUATE</span>"
        elif s >= 40:
            return "<span class='badge bg-a'>VULNERABLE</span>"
        else:
            return "<span class='badge bg-r'>CRITICAL</span>"
    except (TypeError, ValueError):
        return "<span class='badge bg-grey'>UNKNOWN</span>"


def generate_executive_html(
    bundle_data: dict,
    app_version: str = "1.0",
    generated_at: str = "",
) -> str:
    """
    Compact executive HTML — constitutional notice, KPI summary,
    governance status, economic ground truth, top recommendations.
    Falls back gracefully to 'data pending' for missing sections.
    """
    try:
        ts  = generated_at or _ts_str()
        summary  = bundle_data.get("summary", {})
        sov      = bundle_data.get("sovereign_readiness", {})
        egt      = bundle_data.get("economic_ground_truth", {})
        recs_src = bundle_data.get("recommendations", [])

        lines: List[str] = [
            "<!DOCTYPE html><html lang='en'><head>",
            "<meta charset='UTF-8'><title>PHOENIX Executive Report</title>",
            _BASE_CSS,
            "</head><body><div class='wrap'>",
            "<div class='hdr'>",
            "<h1>PHOENIX Executive Institutional Report</h1>",
            f"<p>Version: {app_version} &nbsp;|&nbsp; Generated: {ts}</p>",
            "<p>Constitutional notice: research instrumentation only — "
            "human authority required for all decisions. auto_authorized=False.</p>",
            "</div>",
        ]

        # KPI summary
        lines.append("<h2>Session KPIs</h2>")
        if summary:
            kpi_fields = [
                ("total_pnl",    "Total PnL"),
                ("win_rate",     "Win Rate"),
                ("trade_count",  "Trades"),
                ("sharpe_ratio", "Sharpe"),
                ("max_drawdown", "Max DD"),
            ]
            lines.append("<div style='display:flex;gap:.6rem;flex-wrap:wrap'>")
            for fk, label in kpi_fields:
                val = summary.get(fk, "—")
                lines.append(
                    f"<div class='card' style='min-width:130px'>"
                    f"<div style='font-size:.72rem;color:#718096'>{label}</div>"
                    f"<div style='font-size:1.1rem;font-weight:700'>{val}</div>"
                    f"</div>"
                )
            lines.append("</div>")
        else:
            lines.append("<p class='pending'>Session summary data pending.</p>")

        # Governance status
        lines.append("<h2>Governance Readiness</h2>")
        if sov:
            score = sov.get("readiness_score", sov.get("score", None))
            tier  = sov.get("readiness_tier", sov.get("health_tier", "UNKNOWN"))
            lines.append(
                f"<div class='card'><div class='kv'><span class='k'>Tier:</span>"
                f"<span class='badge bg-p'>{tier}</span></div>"
            )
            if score is not None:
                lines.append(f"<div class='kv'><span class='k'>Score:</span>{score}</div>")
            gates = sov.get("readiness_gates", sov.get("gates", {}))
            if gates:
                lines.append("<table><tr><th>Gate</th><th>Status</th></tr>")
                for gate, status in list(gates.items())[:8]:
                    ok = "✓" if status else "✗"
                    lines.append(f"<tr><td>{gate}</td><td>{ok}</td></tr>")
                lines.append("</table>")
            lines.append("</div>")
        else:
            lines.append("<p class='pending'>Governance readiness data pending.</p>")

        # Economic ground truth
        lines.append("<h2>Economic Ground Truth</h2>")
        if egt:
            egt_fields = [
                ("net_pnl",    "Net PnL"),
                ("gross_pnl",  "Gross PnL"),
                ("total_fees", "Total Fees"),
                ("sharpe",     "Sharpe"),
            ]
            lines.append("<div class='card'>")
            for fk, label in egt_fields:
                val = egt.get(fk, "—")
                lines.append(
                    f"<div class='kv'><span class='k'>{label}:</span>{val}</div>"
                )
            lines.append("</div>")
        else:
            lines.append("<p class='pending'>Economic ground truth data pending.</p>")

        # Recommendations
        lines.append("<h2>Recommendations</h2>")
        if recs_src and isinstance(recs_src, list):
            for rec in recs_src[:5]:
                pri  = str(rec.get("priority", "LOW")).upper()
                bg   = {"HIGH": "bg-r", "MEDIUM": "bg-a", "LOW": "bg-b"}.get(pri, "bg-grey")
                lines.append(
                    f"<div class='card'><span class='badge {bg}'>{pri}</span> "
                    f"{rec.get('summary', rec.get('type', ''))}"
                    f" <span style='font-size:.72rem;color:#718096'>"
                    f"auto_authorized=False</span></div>"
                )
        else:
            lines.append("<p class='pending'>No recommendations data available.</p>")

        lines.append("</div></body></html>")
        return "\n".join(lines)

    except Exception as exc:
        return (
            f"<!DOCTYPE html><html><body>"
            f"<p>Executive HTML generation error: {exc}</p>"
            f"</body></html>"
        )


def generate_research_markdown(
    bundle_data: dict,
    app_version: str = "1.0",
) -> str:
    """
    Full markdown research report. Header, constitutional notice, all 25 reports
    grouped by family in topological order.
    """
    try:
        topo   = topological_sort()
        ts_str = _ts_str()
        lines: List[str] = [
            "# PHOENIX Research Report",
            "",
            f"**Version:** {app_version}  ",
            f"**Generated:** {ts_str}  ",
            f"**Reports:** {len(REPORT_REGISTRY)}  ",
            "",
            "## Constitutional Notice",
            "",
            "> Research instrumentation only. Human authority required for all "
            "governance and deployment decisions. All recommendations are "
            "auto_authorized=False. Export requires explicit human approval.",
            "",
        ]

        # Group by family
        by_family: Dict[str, List[str]] = {}
        for report_id in topo:
            meta   = REPORT_REGISTRY.get(report_id, {})
            family = meta.get("report_family", "OTHER")
            by_family.setdefault(family, []).append(report_id)

        for family in sorted(by_family.keys()):
            lines.append(f"## {family}")
            lines.append("")
            for report_id in by_family[family]:
                meta = REPORT_REGISTRY.get(report_id, {})
                bk   = meta.get("bundle_key", report_id.lower())
                data = bundle_data.get(bk, {})
                name = meta.get("name", report_id)
                tier = meta.get("export_tier", "")
                pri  = meta.get("archive_priority", "")
                desc = meta.get("description", "")

                lines.append(f"### {name} (`{report_id}`)")
                lines.append("")
                lines.append(f"**Tier:** {tier} | **Priority:** {pri} | "
                             f"**Scope:** {meta.get('constitutional_scope','')}")
                lines.append("")
                lines.append(f"_{desc}_")
                lines.append("")

                if data:
                    data_keys = sorted(data.keys())[:8]
                    lines.append("| Field | Value |")
                    lines.append("|-------|-------|")
                    for k in data_keys:
                        v = str(data[k])[:80]
                        lines.append(f"| {k} | {v} |")
                    if len(data) > 8:
                        lines.append(f"| ... | ({len(data) - 8} more fields) |")
                    lines.append("")
                else:
                    lines.append("_Data pending — endpoint not yet called._")
                    lines.append("")

        return "\n".join(lines)

    except Exception as exc:
        return f"# PHOENIX Research Report\n\n_Error: {exc}_\n"


def generate_governance_html(
    bundle_data: dict,
    app_version: str = "1.0",
) -> str:
    """
    Governance-focused HTML — only GOVERNANCE + CONTINUITY + HUMAN_ALIGNMENT.
    Shows constitutional hard principles table and governance readiness gates.
    """
    try:
        topo   = topological_sort()
        ts_str = _ts_str()
        lines: List[str] = [
            "<!DOCTYPE html><html lang='en'><head>",
            "<meta charset='UTF-8'><title>PHOENIX Governance Report</title>",
            _BASE_CSS,
            "</head><body><div class='wrap'>",
            "<div class='hdr'>",
            "<h1>PHOENIX Constitutional Governance Report</h1>",
            f"<p>Version: {app_version} &nbsp;|&nbsp; Generated: {ts_str}</p>",
            "<p>Constitutional governance layer — "
            "human authority required. auto_authorized=False.</p>",
            "</div>",
        ]

        # Hard principles table
        lines.append("<h2>Constitutional Hard Principles</h2>")
        lines.append("<table><tr><th>Principle</th><th>Value</th></tr>")
        for principle, val in _HARD_PRINCIPLES:
            tick = "✓ TRUE" if val else "✗ FALSE"
            bg   = "color:#276749" if val else "color:#9B2C2C"
            lines.append(
                f"<tr><td>{principle}</td>"
                f"<td style='{bg};font-weight:600'>{tick}</td></tr>"
            )
        lines.append("</table>")

        # Governance-family sections
        lines.append("<h2>Governance Reports</h2>")
        for report_id in topo:
            meta   = REPORT_REGISTRY.get(report_id, {})
            family = meta.get("report_family", "")
            if family not in _GOV_FAMILIES:
                continue
            bk   = meta.get("bundle_key", report_id.lower())
            data = bundle_data.get(bk, {})
            name = meta.get("name", report_id)
            desc = meta.get("description", "")
            fg   = _FAMILY_BG.get(family, "bg-grey")

            lines.append("<div class='card'>")
            lines.append(
                f"<h3>{name} <span class='badge {fg}'>{family}</span></h3>"
            )
            lines.append(f"<p class='desc'>{desc}</p>")

            if data:
                score = data.get("readiness_score", data.get("score",
                        data.get("health_score", None)))
                if score is not None:
                    lines.append(
                        f"<div class='kv'><span class='k'>Score:</span>"
                        f"{score} {_health_badge(score)}</div>"
                    )
                # Show gates if present
                gates = data.get("readiness_gates", data.get("gates", {}))
                if gates and isinstance(gates, dict):
                    lines.append("<table><tr><th>Gate</th><th>Status</th></tr>")
                    for gate, status in list(gates.items())[:10]:
                        ok = "✓" if status else "✗"
                        lines.append(f"<tr><td>{gate}</td><td>{ok}</td></tr>")
                    lines.append("</table>")
            else:
                lines.append("<p class='pending'>Data pending.</p>")
            lines.append("</div>")

        lines.append("</div></body></html>")
        return "\n".join(lines)

    except Exception as exc:
        return (
            f"<!DOCTYPE html><html><body>"
            f"<p>Governance HTML generation error: {exc}</p>"
            f"</body></html>"
        )


def generate_archive_page(
    bundle_data: dict,
    app_version: str = "1.0",
) -> str:
    """
    Archive manifest HTML — available bundles, snapshot health,
    export infrastructure health, reconstruction readiness.
    """
    try:
        ts_str = _ts_str()
        lines: List[str] = [
            "<!DOCTYPE html><html lang='en'><head>",
            "<meta charset='UTF-8'><title>PHOENIX Archive Page</title>",
            _BASE_CSS,
            "</head><body><div class='wrap'>",
            "<div class='hdr'>",
            "<h1>PHOENIX Institutional Archive</h1>",
            f"<p>Version: {app_version} &nbsp;|&nbsp; Generated: {ts_str}</p>",
            "<p>Immutable institutional archive — lineage-anchored, "
            "reconstruction-safe. auto_authorized=False.</p>",
            "</div>",
        ]

        # Available bundles
        lines.append("<h2>Available Bundles</h2>")
        lines.append("<table><tr><th>Bundle</th><th>Reports</th><th>Status</th></tr>")
        for bundle_name, members in sorted(BUNDLE_MEMBERSHIP.items()):
            count  = len(members)
            status = "✓ Registered"
            lines.append(
                f"<tr><td>{bundle_name}</td><td>{count}</td>"
                f"<td style='color:#276749'>{status}</td></tr>"
            )
        lines.append("</table>")

        # Snapshot health (from bundle_data if snapshot-related keys present)
        lines.append("<h2>Archive Health Indicators</h2>")
        health_keys = [
            ("archive_browser_health",      "Archive Browser"),
            ("replay_explorer_health",      "Replay Explorer"),
            ("export_preview_health",       "Export Preview"),
            ("visualization_health",        "Visualization"),
            ("institutional_search_health", "Institutional Search"),
        ]
        lines.append("<div class='card'>")
        found_any = False
        for bk, label in health_keys:
            h = bundle_data.get(bk, {})
            if h:
                found_any = True
                healthy_key = [k for k in h.keys() if k.endswith("_healthy")]
                is_healthy  = h.get(healthy_key[0], False) if healthy_key else False
                ind = "✓ Healthy" if is_healthy else "⚠ Degraded"
                col = "color:#276749" if is_healthy else "color:#9B2C2C"
                lines.append(
                    f"<div class='kv'><span class='k'>{label}:</span>"
                    f"<span style='{col}'>{ind}</span></div>"
                )
        if not found_any:
            lines.append("<p class='pending'>Archive health data pending.</p>")
        lines.append("</div>")

        # Export formats
        lines.append("<h2>Export Infrastructure</h2>")
        lines.append("<div class='card'>")
        lines.append(
            "<div class='kv'><span class='k'>Formats:</span>"
            "html, json, markdown, zip, pdf_ready_html</div>"
        )
        lines.append(
            "<div class='kv'><span class='k'>Modes:</span>"
            "single_report, report_family, bundle, full_archive, "
            "replay_snapshot, governance_export</div>"
        )
        lines.append(
            "<div class='kv'><span class='k'>Auth:</span>"
            "<span style='color:#9B2C2C'>auto_authorized=False — "
            "human approval required</span></div>"
        )
        lines.append("</div>")

        lines.append("</div></body></html>")
        return "\n".join(lines)

    except Exception as exc:
        return (
            f"<!DOCTYPE html><html><body>"
            f"<p>Archive page generation error: {exc}</p>"
            f"</body></html>"
        )


# ── Health check ──────────────────────────────────────────────────────────────

def get_presentation_health() -> dict:
    """
    Spot-checks generate_executive_html with an empty dict.
    Returns health summary — never raises.
    """
    try:
        html = generate_executive_html({})
        html_ok = isinstance(html, str) and len(html) > 100

        md = generate_research_markdown({})
        md_ok = isinstance(md, str) and len(md) > 50

        gov = generate_governance_html({})
        gov_ok = isinstance(gov, str) and len(gov) > 100

        arch = generate_archive_page({})
        arch_ok = isinstance(arch, str) and len(arch) > 100

        presentation_healthy = html_ok and md_ok and gov_ok and arch_ok
        return {
            "presentation_operational": True,
            "supported_formats":        ["html", "markdown", "governance_html", "archive_html"],
            "executive_html_ok":        html_ok,
            "research_markdown_ok":     md_ok,
            "governance_html_ok":       gov_ok,
            "archive_page_ok":          arch_ok,
            "presentation_healthy":     presentation_healthy,
        }
    except Exception as exc:
        return {
            "presentation_operational": False,
            "supported_formats":        ["html", "markdown", "governance_html", "archive_html"],
            "presentation_healthy":     False,
            "error":                    str(exc),
        }

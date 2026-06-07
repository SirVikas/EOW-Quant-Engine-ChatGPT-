"""
FTD-NEXUS-DASHBOARD-001 — Verifier
PHOENIX NEXUS Dashboard Identity & Visibility Layer
"""
import re
from pathlib import Path

DASHBOARD = Path(__file__).parents[2] / "dashboard.html"


def _html() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


# ── Test 1: NEXUS name visible ────────────────────────────────────────────────

def test_nexus_name_in_topbar():
    html = _html()
    assert "PHOENIX NEXUS" in html, "PHOENIX NEXUS identity missing from dashboard"


def test_nexus_topbar_badge_element():
    html = _html()
    assert "nexus-topbar-badge" in html, "nexus-topbar-badge element missing from topbar"


# ── Test 2: NEXUS version visible ─────────────────────────────────────────────

def test_nexus_version_element_present():
    html = _html()
    assert "nexus-version-topbar" in html, "nexus-version-topbar element missing"
    assert "nexus-card-version" in html, "nexus-card-version element missing"


def test_nexus_version_fallback_value():
    html = _html()
    assert "v1.0.0" in html, "Initial NEXUS version v1.0.0 not present in HTML"


# ── Test 3: Layer rendering works ─────────────────────────────────────────────

def test_nexus_layer_grid_element():
    html = _html()
    assert "nexus-layer-grid" in html, "nexus-layer-grid element missing"


def test_nexus_health_grid_element():
    html = _html()
    assert "nexus-health-grid" in html, "nexus-health-grid element missing"


def test_render_nexus_card_function():
    html = _html()
    assert "renderNexusCard" in html, "renderNexusCard JS function missing"


# ── Test 4: Dynamic rendering from API response ───────────────────────────────

def test_dynamic_active_layers_rendering():
    html = _html()
    # Must iterate d.active_layers, not hardcode layer names in render path
    assert "d.active_layers" in html, "active_layers iteration missing — layers must be rendered dynamically"
    assert "d.pending_layers" in html, "pending_layers iteration missing — future layers must render dynamically"


def test_no_hardcoded_layer_names_in_renderer():
    html = _html()
    # The render functions must not hardcode individual layer names like 'IMRAF', 'DIAL', etc.
    # Extract only the renderNexusCard / renderNexusHealthGrid JS blocks
    render_block_start = html.find("function renderNexusCard(d)")
    render_block_end   = html.find("function renderNexusRoadmap(d)")
    assert render_block_start != -1, "renderNexusCard function not found"
    render_block = html[render_block_start:render_block_end]
    for hardcoded in ("'IMRAF'", "'DIAL'", "'AEOS'", "'EMA'", "'EGI'"):
        assert hardcoded not in render_block, (
            f"Layer name {hardcoded} is hardcoded in render function — must be dynamic"
        )


# ── Test 5: Roadmap displayed ─────────────────────────────────────────────────

def test_roadmap_chain_a_element():
    html = _html()
    assert "nexus-chain-a" in html, "nexus-chain-a roadmap element missing"


def test_roadmap_chain_b_element():
    html = _html()
    assert "nexus-chain-b" in html, "nexus-chain-b roadmap element missing"


def test_roadmap_kge_hke_aeg_labels():
    html = _html()
    assert "KGE" in html, "KGE roadmap step missing from dashboard"
    assert "HKE" in html, "HKE roadmap step missing from dashboard"
    assert "AEG" in html, "AEG roadmap step missing from dashboard"


def test_roadmap_blocked_reason_displayed():
    html = _html()
    assert "BLOCKED" in html, "BLOCKED state label missing from roadmap panel"
    assert "Requires" in html, "Roadmap blocked-reason text missing"


# ── Test 6: Diagnostics panel opens ──────────────────────────────────────────

def test_diagnostics_card_element():
    html = _html()
    assert "nexus-diagnostics-card" in html, "nexus-diagnostics-card element missing"
    assert "nexus-diagnostics-body" in html, "nexus-diagnostics-body element missing"


def test_toggle_nexus_diagnostics_function():
    html = _html()
    assert "toggleNexusDiagnostics" in html, "toggleNexusDiagnostics JS function missing"


def test_open_nexus_diagnostics_from_topbar():
    html = _html()
    assert "openNexusDiagnostics" in html, "openNexusDiagnostics function missing"
    assert 'onclick="openNexusDiagnostics()"' in html, "topbar badge does not call openNexusDiagnostics"


def test_diagnostics_shows_adr_reference():
    html = _html()
    assert "ADR-NEXUS-001" in html, "ADR-NEXUS-001 reference missing from diagnostics"


# ── Test 7: Health indicator displayed ───────────────────────────────────────

def test_health_summary_element():
    html = _html()
    assert "nexus-health-summary" in html, "nexus-health-summary element missing"


def test_health_dot_element():
    html = _html()
    assert "nexus-health-dot" in html, "nexus-health-dot topbar indicator missing"


def test_health_derived_from_api():
    html = _html()
    # Health % must be computed from active_layers count, not hardcoded
    assert "healthPct" in html, "healthPct variable missing — health must be computed from API data"
    assert "activeCount" in html, "activeCount variable missing"


# ── Test 8: Future layer auto-render validated ────────────────────────────────

def test_pending_layers_rendered_dynamically():
    html = _html()
    assert "nexus-pending-layers" in html, "nexus-pending-layers container missing"
    # pending_layers from API drives rendering, not hardcoded KGE/HKE/AEG
    pending_render_start = html.find("nexus-pending-layers")
    pending_render_block = html[pending_render_start:pending_render_start + 2000]
    assert "pending_layers" in pending_render_block or "pendingLayers" in pending_render_block, (
        "Pending layers container does not use API data — must render from d.pending_layers"
    )


def test_nexus_tab_wired_in_switchtab():
    html = _html()
    assert "'nexus'" in html, "nexus tab not registered in switchTab list"
    assert "loadNexusData" in html, "loadNexusData not called from switchTab"


def test_nexus_tab_button_present():
    html = _html()
    assert "tab-btn-nexus" in html, "NEXUS tab button missing from nav"
    assert "switchTab('nexus')" in html, "switchTab('nexus') call missing"


# ── Boot validation ───────────────────────────────────────────────────────────

def test_boot_fetches_nexus_api():
    html = _html()
    # /api/nexus must be fetched on DOMContentLoaded (boot)
    boot_block_start = html.find("DOMContentLoaded")
    boot_block_end   = html.find("// ── MASTER-001")
    assert boot_block_start != -1, "DOMContentLoaded boot block not found"
    boot_block = html[boot_block_start:boot_block_end]
    assert "/api/nexus" in boot_block, "/api/nexus not fetched at boot — topbar identity requires boot-time fetch"


def test_boot_populates_topbar_identity():
    html = _html()
    assert "renderNexusTopbar" in html, "renderNexusTopbar not called at boot"


def test_component8_nexus_always_visible():
    html = _html()
    # The topbar badge must be in the permanent topbar structure, not inside a tab panel
    topbar_start = html.find('<div class="topbar">')
    topbar_end   = html.find('</div>', topbar_start + 500)
    # Extend to capture the full topbar block
    topbar_block = html[topbar_start:topbar_start + 2000]
    assert "nexus-topbar-badge" in topbar_block, (
        "PHOENIX NEXUS badge must be in the topbar (always visible) — COMPONENT-8 requires permanent visibility"
    )

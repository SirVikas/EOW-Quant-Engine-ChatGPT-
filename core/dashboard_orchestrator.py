"""
FTD-IREL: Institutional Dashboard Orchestrator.

Registry-driven dashboard structure builder and governance entry point.
Maps report families to institutional tabs, builds tab manifests,
and computes the composite IREL health score.

IREL health scoring:
  renderer(25) + orchestrator(25) + presentation(20) + download(15) + timeline(15) = 100

Constitutional guarantee: auto_authorized is always False on all outputs.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

from core.report_registry import (
    REPORT_REGISTRY,
    KNOWN_FAMILIES,
    FAMILY_ECONOMIC, FAMILY_COGNITIVE, FAMILY_GOVERNANCE,
    FAMILY_EPISTEMIC, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT,
    FAMILY_REPLAY, FAMILY_FORENSICS,
    TIER_CORE, TIER_GOVERNANCE,
    PRIORITY_CRITICAL, PRIORITY_HIGH,
)

# ── Family → tab mapping ──────────────────────────────────────────────────────
FAMILY_TO_TAB: Dict[str, str] = {
    FAMILY_ECONOMIC:        "executive",
    FAMILY_COGNITIVE:       "cognition",
    FAMILY_GOVERNANCE:      "governance",
    FAMILY_EPISTEMIC:       "epistemic",
    FAMILY_CONTINUITY:      "continuity",
    FAMILY_HUMAN_ALIGNMENT: "continuity",
    FAMILY_REPLAY:          "research_lab",
    FAMILY_FORENSICS:       "research_lab",
}

# ── Tab descriptors ───────────────────────────────────────────────────────────
TAB_METADATA: Dict[str, Dict] = {
    "executive": {
        "tab_id":      "executive",
        "label":       "Executive",
        "icon":        "🏛",
        "description": "High-level economic truth and trading summary",
        "families":    [FAMILY_ECONOMIC],
        "order":       1,
    },
    "cognition": {
        "tab_id":      "cognition",
        "label":       "Cognition",
        "icon":        "🧠",
        "description": "Cognitive and learning intelligence reports",
        "families":    [FAMILY_COGNITIVE],
        "order":       2,
    },
    "governance": {
        "tab_id":      "governance",
        "label":       "Governance",
        "icon":        "⚖",
        "description": "Constitutional governance and adaptive doctrine reports",
        "families":    [FAMILY_GOVERNANCE],
        "order":       3,
    },
    "epistemic": {
        "tab_id":      "epistemic",
        "label":       "Epistemic",
        "icon":        "🔬",
        "description": "Scientific evidence and epistemic integrity reports",
        "families":    [FAMILY_EPISTEMIC],
        "order":       4,
    },
    "continuity": {
        "tab_id":      "continuity",
        "label":       "Continuity",
        "icon":        "🔗",
        "description": "Continuity, lineage, and human alignment reports",
        "families":    [FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT],
        "order":       5,
    },
    "archive": {
        "tab_id":      "archive",
        "label":       "Archive",
        "icon":        "📦",
        "description": "Snapshot archive browser and lineage explorer",
        "families":    [],
        "order":       6,
    },
    "export_center": {
        "tab_id":      "export_center",
        "label":       "Export",
        "icon":        "⬇",
        "description": "Institutional export and download center",
        "families":    [],
        "order":       7,
    },
    "research_lab": {
        "tab_id":      "research_lab",
        "label":       "Research Lab",
        "icon":        "🧪",
        "description": "Replay, forensics, and research-grade analysis",
        "families":    [FAMILY_REPLAY, FAMILY_FORENSICS],
        "order":       8,
    },
}

# ── Constitutional hard principles ────────────────────────────────────────────
IREL_HARD_PRINCIPLES: Dict[str, bool] = {
    "autonomous_report_modification":       False,
    "auto_authorized_recommendations":      False,
    "headless_export_without_approval":     False,
    "dashboard_driven_order_placement":     False,
    "registry_mutation_at_runtime":         False,
    "tab_removal_without_human_approval":   False,
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_report_to_tab_mapping() -> Dict[str, str]:
    """
    Returns a mapping of report_id → tab_id derived from FAMILY_TO_TAB.
    Reports whose family has no mapping fall back to 'executive'.
    """
    result: Dict[str, str] = {}
    for report_id, meta in REPORT_REGISTRY.items():
        family = meta.get("report_family", "")
        result[report_id] = FAMILY_TO_TAB.get(family, "executive")
    return result


def build_tab_manifest() -> dict:
    """
    Build the full institutional tab manifest.

    For each tab, collects the list of report_ids assigned to it (in
    registry order), along with report counts and tab metadata.
    Returns a manifest suitable for the dashboard JS to auto-discover tabs.
    """
    try:
        report_to_tab = get_report_to_tab_mapping()

        # Group report_ids by tab
        tab_reports: Dict[str, List[str]] = {tid: [] for tid in TAB_METADATA}
        for report_id, tab_id in report_to_tab.items():
            if tab_id in tab_reports:
                tab_reports[tab_id].append(report_id)

        tabs_list = []
        for tab_id, tmeta in sorted(TAB_METADATA.items(), key=lambda kv: kv[1]["order"]):
            rids = sorted(tab_reports.get(tab_id, []))
            tabs_list.append({
                "tab_id":       tab_id,
                "label":        tmeta["label"],
                "icon":         tmeta["icon"],
                "description":  tmeta["description"],
                "order":        tmeta["order"],
                "families":     tmeta["families"],
                "report_ids":   rids,
                "report_count": len(rids),
            })

        total_reports = sum(t["report_count"] for t in tabs_list)
        return {
            "tabs":                  tabs_list,
            "tab_count":             len(tabs_list),
            "total_mapped_reports":  total_reports,
            "registry_report_count": len(REPORT_REGISTRY),
            "manifest_complete":     total_reports == len(REPORT_REGISTRY),
            "auto_authorized":       False,
        }
    except Exception as exc:
        return {
            "tabs":                  [],
            "tab_count":             0,
            "total_mapped_reports":  0,
            "registry_report_count": len(REPORT_REGISTRY),
            "manifest_complete":     False,
            "auto_authorized":       False,
            "error":                 str(exc),
        }


def build_dashboard_structure(bundle_data: Optional[dict] = None) -> dict:
    """
    Build the full dashboard structure, combining tab manifest with
    per-report data availability from bundle_data.

    Returns a dict suitable for serialization to the frontend.
    """
    try:
        bd    = bundle_data or {}
        tmfst = build_tab_manifest()
        r2t   = get_report_to_tab_mapping()

        report_statuses: List[dict] = []
        populated = 0
        critical_missing = []

        for report_id, meta in REPORT_REGISTRY.items():
            bk        = meta.get("bundle_key", report_id.lower())
            has_data  = bool(bd.get(bk))
            priority  = meta.get("archive_priority", "")
            tab_id    = r2t.get(report_id, "executive")

            if has_data:
                populated += 1
            elif priority in (PRIORITY_CRITICAL, PRIORITY_HIGH):
                critical_missing.append(report_id)

            report_statuses.append({
                "report_id":  report_id,
                "name":       meta.get("name", report_id),
                "tab_id":     tab_id,
                "bundle_key": bk,
                "has_data":   has_data,
                "priority":   priority,
                "family":     meta.get("report_family", ""),
            })

        total = len(REPORT_REGISTRY)
        coverage_pct = round(populated / total * 100.0, 1) if total else 0.0

        return {
            "tab_manifest":       tmfst,
            "report_statuses":    report_statuses,
            "total_reports":      total,
            "populated_reports":  populated,
            "coverage_pct":       coverage_pct,
            "critical_missing":   critical_missing,
            "auto_authorized":    False,
        }
    except Exception as exc:
        return {
            "tab_manifest":     {},
            "report_statuses":  [],
            "total_reports":    len(REPORT_REGISTRY),
            "populated_reports": 0,
            "coverage_pct":     0.0,
            "critical_missing": [],
            "auto_authorized":  False,
            "error":            str(exc),
        }


def get_orchestrator_health() -> dict:
    """
    Self-check: build_tab_manifest and build_dashboard_structure with empty data.
    Returns health summary without raising.
    """
    try:
        tmfst  = build_tab_manifest()
        struct = build_dashboard_structure({})
        tmfst_ok  = isinstance(tmfst, dict) and tmfst.get("tab_count", 0) >= 8
        struct_ok = isinstance(struct, dict) and struct.get("total_reports", 0) == len(REPORT_REGISTRY)
        orch_healthy = tmfst_ok and struct_ok
        return {
            "orchestrator_operational":   True,
            "tab_count":                  tmfst.get("tab_count", 0),
            "registry_report_count":      len(REPORT_REGISTRY),
            "manifest_complete":          tmfst.get("manifest_complete", False),
            "tab_manifest_ok":            tmfst_ok,
            "dashboard_structure_ok":     struct_ok,
            "orchestrator_healthy":       orch_healthy,
        }
    except Exception as exc:
        return {
            "orchestrator_operational":   False,
            "tab_count":                  0,
            "registry_report_count":      len(REPORT_REGISTRY),
            "orchestrator_healthy":       False,
            "error":                      str(exc),
        }


def compute_institutional_reporting_experience(
    bundle_data: Optional[dict] = None,
    snapshots: Optional[list] = None,
) -> dict:
    """
    Master IREL governance entry point.

    Computes composite IREL health score (0-100):
      renderer(25) + orchestrator(25) + presentation(20) + download(15) + timeline(15)

    Emits a constitutional audit entry with prefix IREL-{ts}-{hash[:16]}.
    auto_authorized is always False.
    """
    try:
        from core.institutional_report_renderer import get_renderer_health
        from core.export_presentation import get_presentation_health
        from core.download_experience import get_download_experience_health
        from core.timeline_visualization import get_timeline_health

        bd    = bundle_data or {}
        snaps = list(snapshots or [])

        renderer_h     = get_renderer_health()
        orchestrator_h = get_orchestrator_health()
        presentation_h = get_presentation_health()
        download_h     = get_download_experience_health()
        timeline_h     = get_timeline_health(snaps)

        # Score components (0/max based on healthy flag)
        r_score   = 25 if renderer_h.get("renderer_healthy")       else 0
        o_score   = 25 if orchestrator_h.get("orchestrator_healthy") else 0
        p_score   = 20 if presentation_h.get("presentation_healthy") else 0
        d_score   = 15 if download_h.get("download_experience_healthy") else 0
        t_score   = 15 if timeline_h.get("timeline_healthy")         else 0

        irel_score = r_score + o_score + p_score + d_score + t_score

        if irel_score >= 80:
            tier = "HEALTHY"
        elif irel_score >= 60:
            tier = "ADEQUATE"
        elif irel_score >= 40:
            tier = "VULNERABLE"
        else:
            tier = "CRITICAL"

        structure = build_dashboard_structure(bd)
        tmfst     = build_tab_manifest()

        ts_ms = int(_time.time() * 1000)
        audit_payload = {
            "irel_health_score": irel_score,
            "tier":              tier,
            "ts_ms":             ts_ms,
        }
        audit_hash = hashlib.sha256(
            str(audit_payload).encode("utf-8")
        ).hexdigest()
        audit_id = f"IREL-{ts_ms}-{audit_hash[:16]}"

        return {
            "irel_health_score":          irel_score,
            "irel_health_tier":           tier,
            "scoring_breakdown": {
                "renderer":      {"weight": 25, "score": r_score},
                "orchestrator":  {"weight": 25, "score": o_score},
                "presentation":  {"weight": 20, "score": p_score},
                "download":      {"weight": 15, "score": d_score},
                "timeline":      {"weight": 15, "score": t_score},
            },
            "tab_manifest":               tmfst,
            "dashboard_structure":        structure,
            "renderer_health":            renderer_h,
            "orchestrator_health":        orchestrator_h,
            "presentation_health":        presentation_h,
            "download_health":            download_h,
            "timeline_health":            timeline_h,
            "irel_hard_principles":       IREL_HARD_PRINCIPLES,
            "audit_id":                   audit_id,
            "generated_at_ms":            ts_ms,
            "auto_authorized":            False,
            "human_authority":            True,
        }
    except Exception as exc:
        ts_ms = int(_time.time() * 1000)
        return {
            "irel_health_score":  0,
            "irel_health_tier":   "CRITICAL",
            "irel_hard_principles": IREL_HARD_PRINCIPLES,
            "auto_authorized":    False,
            "human_authority":    True,
            "generated_at_ms":    ts_ms,
            "error":              str(exc),
        }

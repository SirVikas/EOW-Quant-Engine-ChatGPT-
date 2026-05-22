"""
FTD-UDCA: Unified Institutional Download Center Governance.

Orchestrates PHOENIX's archive experience layer and produces a constitutional
download center governance assessment.

Capabilities assessed:
  - Archive browser operability
  - Replay explorer health
  - Export preview integrity
  - Archive visualization health
  - Institutional search operability
  - Lineage navigation accessibility
  - Download center accessibility

Constitutional guarantee:
  All recommendations have auto_authorized=False.
  Archive experience governance remains permanently under human authority.

Pure analytics — no I/O, no live engine imports, fail-open.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

from core.archive_browser import get_browser_health
from core.replay_explorer import get_replay_health
from core.export_preview import get_preview_health
from core.archive_visualization import get_visualization_health
from core.institutional_search import get_search_health
from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP
from core.snapshot_manager import SNAPSHOT_TYPES

# ── Hard constitutional download center principles ────────────────────────────
DOWNLOAD_CENTER_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_archive_experience":  True,
    "explicit_export_approval_required":        True,
    "immutable_lineage_navigation_guaranteed":  True,
    "all_archive_access_human_controlled":      True,
    "replay_continuity_preserved":              True,
    "search_index_integrity_enforced":          True,
    "autonomous_archive_mutation":              False,
    "self_authorized_snapshot_deletion":        False,
    "autonomous_lineage_rewriting":             False,
    "silent_manifest_alteration":              False,
    "undocumented_export_generation":           False,
}


def _generate_download_recommendations(
    browser_h: dict,
    replay_h:  dict,
    preview_h: dict,
    viz_h:     dict,
    search_h:  dict,
) -> List[dict]:
    recs: List[dict] = []

    if not browser_h.get("browser_healthy"):
        recs.append({
            "priority":        "HIGH",
            "type":            "ARCHIVE_BROWSER_DEGRADED",
            "summary":         "Archive browser health degraded — snapshot navigation unavailable.",
            "action_required": "HUMAN_REVIEW_ARCHIVE_BROWSER",
            "auto_authorized": False,
        })

    if not replay_h.get("replay_healthy"):
        recs.append({
            "priority":        "HIGH",
            "type":            "REPLAY_EXPLORER_DEGRADED",
            "summary":         "Replay explorer health degraded — lineage replay unavailable.",
            "action_required": "HUMAN_REVIEW_REPLAY_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not preview_h.get("preview_healthy"):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "EXPORT_PREVIEW_DEGRADED",
            "summary":         "Export preview degraded — preview-before-download unavailable.",
            "action_required": "HUMAN_REVIEW_PREVIEW_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not viz_h.get("visualization_healthy"):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "VISUALIZATION_DEGRADED",
            "summary":         "Archive visualization degraded — graph rendering unavailable.",
            "action_required": "HUMAN_REVIEW_VISUALIZATION_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not search_h.get("search_operational"):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "INSTITUTIONAL_SEARCH_DEGRADED",
            "summary":         "Institutional search degraded — archive discoverability impaired.",
            "action_required": "HUMAN_REVIEW_SEARCH_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":        "LOW",
            "type":            "DOWNLOAD_CENTER_HEALTHY",
            "summary":         (
                "All download center components operational — archive browser, replay explorer, "
                "export preview, visualization, and institutional search healthy."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Public entry point ────────────────────────────────────────────────────────

def compute_download_center_governance(
    snapshots: Optional[List[dict]] = None,
) -> dict:
    """
    Produce a constitutional download center governance assessment.

    Args:
        snapshots: Optional list of snapshot records from the session ledger.

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        snap_list = list(snapshots or [])
        browser_h = get_browser_health(snap_list)
        replay_h  = get_replay_health(snap_list)
        preview_h = get_preview_health()
        viz_h     = get_visualization_health()
        search_h  = get_search_health()
        recs      = _generate_download_recommendations(
            browser_h, replay_h, preview_h, viz_h, search_h
        )

        # Health score (0–100)
        score = 0.0
        if browser_h.get("browser_healthy"):       score += 25.0
        if replay_h.get("replay_healthy"):         score += 25.0
        if preview_h.get("preview_healthy"):       score += 20.0
        if viz_h.get("visualization_healthy"):     score += 15.0
        if search_h.get("search_operational"):     score += 15.0

        if   score >= 80.0: health_tier = "HEALTHY"
        elif score >= 60.0: health_tier = "ADEQUATE"
        elif score >= 40.0: health_tier = "VULNERABLE"
        else:               health_tier = "CRITICAL"

        ts      = int(_time.time() * 1000)
        payload = f"UDCA|{ts}|{score}|{len(REPORT_REGISTRY)}"
        fp      = hashlib.sha256(payload.encode()).hexdigest()

        return {
            "scope_note": (
                "FTD-UDCA constitutional unified download center & archive experience "
                "governance — research instrumentation only. Assesses whether PHOENIX's "
                "institutional archive is operationally accessible, navigable, replayable, "
                "and constitutionally auditable. "
                "All archive experience governance remains permanently subordinate to human authority."
            ),
            "download_center_health_score": round(score, 2),
            "download_center_health_tier":  health_tier,
            "archive_browser_health":       browser_h,
            "replay_explorer_health":       replay_h,
            "export_preview_health":        preview_h,
            "visualization_health":         viz_h,
            "institutional_search_health":  search_h,
            "available_bundles":            sorted(BUNDLE_MEMBERSHIP.keys()),
            "available_snapshot_types":     sorted(SNAPSHOT_TYPES),
            "total_reports":                len(REPORT_REGISTRY),
            "snapshots_assessed":           len(snap_list),
            "recommendations":              recs,
            "download_hard_principles":     DOWNLOAD_CENTER_HARD_PRINCIPLES,
            "audit_entry": {
                "entry_id":                     f"UDCA-{ts}-{fp[:16]}",
                "timestamp_ms":                 ts,
                "entry_type":                   "DOWNLOAD_CENTER_ASSESSMENT",
                "download_center_health_score": round(score, 2),
                "health_tier":                  health_tier,
                "snapshots_assessed":           len(snap_list),
                "human_approval_required":      True,
                "auto_authorized":              False,
                "immutable":                    True,
            },
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "scope_note":  "FTD-UDCA research instrumentation — analysis error.",
            "error":       "analysis failed",
            "download_hard_principles": DOWNLOAD_CENTER_HARD_PRINCIPLES,
            "audit_entry": {
                "entry_id":        f"UDCA-{ts}-error",
                "timestamp_ms":    ts,
                "entry_type":      "DOWNLOAD_CENTER_ASSESSMENT",
                "auto_authorized": False,
                "immutable":       True,
            },
        }

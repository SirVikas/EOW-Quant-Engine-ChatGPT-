"""
FTD-IREL: Download Experience Layer.

Orchestrates multi-format institutional download workflows.
Builds download metadata, generates download manifests, and lists
available downloads across all registered bundle types.

Constitutional requirement: auto_authorized=False on all outputs.
All download actions require explicit human approval — no headless export.

DOWNLOAD_MODES: single_report, report_family, bundle, full_archive,
                replay_snapshot, governance_export

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP, get_reports_in_bundle

# ── Supported modes and formats ───────────────────────────────────────────────
DOWNLOAD_MODES: frozenset = frozenset({
    "single_report",
    "report_family",
    "bundle",
    "full_archive",
    "replay_snapshot",
    "governance_export",
})

EXPORT_FORMATS: frozenset = frozenset({
    "html",
    "json",
    "markdown",
    "zip",
    "pdf_ready_html",
})

# ── Bundle descriptions ────────────────────────────────────────────────────────
_BUNDLE_DESCRIPTIONS: Dict[str, str] = {
    "EXECUTIVE":      "High-level institutional summary — CORE + GOVERNANCE tier reports",
    "RESEARCH":       "Full research suite — all RESEARCH tier reports",
    "GOVERNANCE":     "Constitutional governance package — GOVERNANCE family reports",
    "EPISTEMIC":      "Scientific evidence package — EPISTEMIC family reports",
    "CONTINUITY":     "Continuity & lineage package — CONTINUITY + HUMAN_ALIGNMENT reports",
    "MASTER_ARCHIVE": "Complete institutional archive — all 25 registered reports",
}

# ── Format descriptions ────────────────────────────────────────────────────────
_FORMAT_DESCRIPTIONS: Dict[str, str] = {
    "html":           "Self-contained HTML with embedded CSS — suitable for browser viewing",
    "json":           "Machine-readable JSON — suitable for programmatic consumption",
    "markdown":       "Portable markdown — suitable for documentation systems",
    "zip":            "Compressed archive bundle — all formats packaged together",
    "pdf_ready_html": "Print-optimized HTML — suitable for PDF conversion via browser",
}


# ── Public API ────────────────────────────────────────────────────────────────

def orchestrate_download(
    mode: str,
    target: str = "",
    format: str = "json",
    app_version: str = "1.0",
    snapshots: Optional[list] = None,
) -> dict:
    """
    Plan a download operation.

    Returns a download plan dict — does NOT perform any I/O.
    All download plans carry auto_authorized=False; execution requires
    explicit human approval.

    mode:   one of DOWNLOAD_MODES; unknown modes default to 'bundle'
    target: report_id for single_report, family name for report_family,
            bundle type for bundle/full_archive, snapshot_id for replay_snapshot
    format: one of EXPORT_FORMATS; unknown formats default to 'json'
    """
    try:
        effective_mode   = mode if mode in DOWNLOAD_MODES else "bundle"
        effective_format = format if format in EXPORT_FORMATS else "json"

        ts_ms      = int(_time.time() * 1000)
        report_ids: List[str] = []

        if effective_mode == "single_report":
            if target in REPORT_REGISTRY:
                report_ids = [target]
            else:
                report_ids = []
            description = f"Single report download: {target}"

        elif effective_mode == "report_family":
            report_ids = [
                r for r, m in REPORT_REGISTRY.items()
                if m.get("report_family", "") == target.upper()
            ]
            description = f"Family download: {target.upper()}"

        elif effective_mode in ("bundle", "full_archive"):
            bundle_name = target.upper() if target else "MASTER_ARCHIVE"
            members = get_reports_in_bundle(bundle_name)
            report_ids = sorted(members) if members else sorted(REPORT_REGISTRY.keys())
            description = _BUNDLE_DESCRIPTIONS.get(bundle_name, f"Bundle: {bundle_name}")

        elif effective_mode == "replay_snapshot":
            report_ids = sorted(REPORT_REGISTRY.keys())
            description = f"Replay snapshot export: {target}"

        elif effective_mode == "governance_export":
            gov_families = {"GOVERNANCE", "CONTINUITY", "HUMAN_ALIGNMENT"}
            report_ids = [
                r for r, m in REPORT_REGISTRY.items()
                if m.get("report_family", "") in gov_families
            ]
            description = "Constitutional governance export"

        else:
            report_ids = []
            description = "Unknown download mode"

        plan_hash = hashlib.sha256(
            f"{effective_mode}:{target}:{effective_format}:{ts_ms}".encode()
        ).hexdigest()
        plan_id = f"DL-{ts_ms}-{plan_hash[:12]}"

        return {
            "plan_id":        plan_id,
            "mode":           effective_mode,
            "format":         effective_format,
            "target":         target,
            "description":    description,
            "report_ids":     report_ids,
            "report_count":   len(report_ids),
            "app_version":    app_version,
            "planned_at_ms":  ts_ms,
            "auto_authorized": False,
            "requires_human_approval": True,
        }
    except Exception as exc:
        return {
            "plan_id":        "",
            "mode":           mode,
            "format":         format,
            "report_ids":     [],
            "report_count":   0,
            "auto_authorized": False,
            "requires_human_approval": True,
            "error":          str(exc),
        }


def build_download_metadata(
    report_ids: List[str],
    format: str = "json",
    app_version: str = "1.0",
) -> dict:
    """
    Build metadata for a set of report_ids.

    Returns per-report metadata (name, family, tier, priority, endpoint)
    alongside aggregate statistics. Does not perform downloads.
    """
    try:
        effective_format = format if format in EXPORT_FORMATS else "json"
        report_meta: List[dict] = []
        families: Dict[str, int] = {}
        tiers: Dict[str, int]    = {}

        for r in report_ids:
            meta = REPORT_REGISTRY.get(r, {})
            if not meta:
                continue
            family = meta.get("report_family", "")
            tier   = meta.get("export_tier", "")
            families[family] = families.get(family, 0) + 1
            tiers[tier]      = tiers.get(tier, 0) + 1
            report_meta.append({
                "report_id":   r,
                "name":        meta.get("name", r),
                "family":      family,
                "tier":        tier,
                "priority":    meta.get("archive_priority", ""),
                "endpoint":    meta.get("endpoint", ""),
                "bundle_key":  meta.get("bundle_key", ""),
            })

        return {
            "report_count":  len(report_meta),
            "report_meta":   report_meta,
            "families":      families,
            "tiers":         tiers,
            "format":        effective_format,
            "app_version":   app_version,
            "auto_authorized": False,
        }
    except Exception as exc:
        return {
            "report_count":  0,
            "report_meta":   [],
            "auto_authorized": False,
            "error":         str(exc),
        }


def generate_download_manifest(
    report_ids: List[str],
    format: str = "json",
    mode: str = "bundle",
    app_version: str = "1.0",
) -> dict:
    """
    Generate an immutable download manifest for a planned download.

    The manifest_hash covers all manifest fields except manifest_id
    and manifest_hash itself. Manifests are immutable once created.
    """
    try:
        effective_format = format if format in EXPORT_FORMATS else "json"
        effective_mode   = mode if mode in DOWNLOAD_MODES else "bundle"
        ts_ms = int(_time.time() * 1000)

        manifest_body = {
            "mode":           effective_mode,
            "format":         effective_format,
            "report_ids":     sorted(report_ids),
            "report_count":   len(report_ids),
            "app_version":    app_version,
            "generated_at_ms": ts_ms,
            "auto_authorized": False,
            "immutable":      True,
            "requires_human_approval": True,
        }

        body_hash = hashlib.sha256(
            str(sorted(manifest_body.items())).encode("utf-8")
        ).hexdigest()
        manifest_id = f"DLM-{effective_mode.upper()}-{ts_ms}-{body_hash[:12]}"

        return {
            "manifest_id":   manifest_id,
            "manifest_hash": body_hash,
            **manifest_body,
        }
    except Exception as exc:
        return {
            "manifest_id":   "",
            "manifest_hash": "",
            "auto_authorized": False,
            "immutable":     True,
            "error":         str(exc),
        }


def list_available_downloads(app_version: str = "1.0") -> dict:
    """
    Enumerate all available download targets across all modes.

    Returns:
      - bundles: one entry per BUNDLE_MEMBERSHIP key
      - families: one entry per known report family
      - single_reports: one entry per registered report
      - formats: list of available export formats
      - modes: list of download modes
    """
    try:
        bundles_list: List[dict] = []
        for bundle_name, members in sorted(BUNDLE_MEMBERSHIP.items()):
            bundles_list.append({
                "bundle_name":  bundle_name,
                "report_count": len(members),
                "description":  _BUNDLE_DESCRIPTIONS.get(bundle_name, ""),
            })

        families_seen: Dict[str, int] = {}
        for meta in REPORT_REGISTRY.values():
            fam = meta.get("report_family", "")
            if fam:
                families_seen[fam] = families_seen.get(fam, 0) + 1

        families_list = [
            {"family": f, "report_count": c}
            for f, c in sorted(families_seen.items())
        ]

        single_reports_list = [
            {
                "report_id": r,
                "name":      m.get("name", r),
                "family":    m.get("report_family", ""),
                "tier":      m.get("export_tier", ""),
            }
            for r, m in sorted(REPORT_REGISTRY.items())
        ]

        return {
            "bundles":         bundles_list,
            "bundle_count":    len(bundles_list),
            "families":        families_list,
            "family_count":    len(families_list),
            "single_reports":  single_reports_list,
            "report_count":    len(single_reports_list),
            "formats":         sorted(EXPORT_FORMATS),
            "modes":           sorted(DOWNLOAD_MODES),
            "app_version":     app_version,
            "auto_authorized": False,
        }
    except Exception as exc:
        return {
            "bundles":         [],
            "families":        [],
            "single_reports":  [],
            "formats":         sorted(EXPORT_FORMATS),
            "modes":           sorted(DOWNLOAD_MODES),
            "auto_authorized": False,
            "error":           str(exc),
        }


def get_download_experience_health() -> dict:
    """
    Spot-check orchestrate_download, build_download_metadata,
    generate_download_manifest, and list_available_downloads.
    Returns health summary without raising.
    """
    try:
        plan = orchestrate_download("bundle", "EXECUTIVE", "json", "1.0")
        plan_ok = isinstance(plan, dict) and "plan_id" in plan and not plan.get("error")

        meta = build_download_metadata(["SUMMARY", "ECOLOGY"], "json", "1.0")
        meta_ok = isinstance(meta, dict) and meta.get("report_count", 0) >= 2

        mfst = generate_download_manifest(["SUMMARY"], "json", "single_report", "1.0")
        mfst_ok = (
            isinstance(mfst, dict)
            and bool(mfst.get("manifest_id"))
            and bool(mfst.get("manifest_hash"))
            and not mfst.get("error")
        )

        avail = list_available_downloads("1.0")
        avail_ok = isinstance(avail, dict) and avail.get("report_count", 0) == len(REPORT_REGISTRY)

        download_experience_healthy = plan_ok and meta_ok and mfst_ok and avail_ok
        return {
            "download_experience_operational":  True,
            "supported_modes":                  sorted(DOWNLOAD_MODES),
            "supported_formats":                sorted(EXPORT_FORMATS),
            "registered_report_count":          len(REPORT_REGISTRY),
            "orchestrate_ok":                   plan_ok,
            "metadata_ok":                      meta_ok,
            "manifest_ok":                      mfst_ok,
            "available_downloads_ok":           avail_ok,
            "download_experience_healthy":      download_experience_healthy,
        }
    except Exception as exc:
        return {
            "download_experience_operational": False,
            "supported_modes":                 sorted(DOWNLOAD_MODES),
            "supported_formats":               sorted(EXPORT_FORMATS),
            "download_experience_healthy":     False,
            "error":                           str(exc),
        }

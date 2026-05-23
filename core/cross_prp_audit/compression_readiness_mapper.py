"""
PRP-PHASEB.6 — Operational Compression Readiness Mapping.

Assigns each of the 25 registry reports to a compression tier and generates
summary candidate lists for executive, governance, ecological, and survivability
report bundles.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Dict, List


# ── Tier classification rules ─────────────────────────────────────────────────
# Tier 1 (Executive Critical)  : CRITICAL or HIGH archive_priority
# Tier 2 (Research Operational): NORMAL/MEDIUM priority + family in TIER2_FAMILIES
# Tier 3 (Deep Forensic)       : NORMAL/MEDIUM priority + family not in TIER2_FAMILIES
# Tier 4 (Archive-Only)        : LOW archive_priority
# Note: report_registry uses PRIORITY_MEDIUM ("MEDIUM"), not "NORMAL".
#       The spec says "NORMAL" — we treat MEDIUM as the registry's equivalent.

_TIER1_PRIORITIES = frozenset({"CRITICAL", "HIGH"})
_TIER4_PRIORITIES = frozenset({"LOW"})
_TIER2_FAMILIES   = frozenset({"ECONOMIC", "COGNITIVE", "GOVERNANCE"})

_COMPRESSION_LABELS: Dict[int, str] = {
    1: "EXECUTIVE_CRITICAL — always include",
    2: "RESEARCH_OPERATIONAL — include in summary bundles",
    3: "DEEP_FORENSIC — include in full export only",
    4: "ARCHIVE_ONLY — historical reference",
}


def _assign_tier(archive_priority: str, report_family: str) -> int:
    if archive_priority in _TIER1_PRIORITIES:
        return 1
    if archive_priority in _TIER4_PRIORITIES:
        return 4
    # MEDIUM / NORMAL / anything else → Tier 2 or 3 based on family
    if report_family in _TIER2_FAMILIES:
        return 2
    return 3


def map_compression_readiness() -> dict:
    """
    PRP-PHASEB.6 — Classify all 25 registry reports by compression tier and
    generate candidate lists for each summary bundle type.

    Returns a self-contained dict; never raises.
    """
    try:
        from core.report_registry import REPORT_REGISTRY  # lazy

        compression_map: List[dict] = []
        tier_distribution: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        tier_1_reports: List[str] = []
        tier_2_reports: List[str] = []
        tier_3_reports: List[str] = []
        tier_4_reports: List[str] = []

        for report_id, meta in REPORT_REGISTRY.items():
            priority = meta.get("archive_priority", "")
            family   = meta.get("report_family", "")
            name     = meta.get("name", report_id)
            bk       = meta.get("bundle_key", "")

            tier = _assign_tier(priority, family)
            tier_distribution[tier] += 1

            compression_map.append({
                "report_id":         report_id,
                "name":              name,
                "family":            family,
                "tier":              tier,
                "archive_priority":  priority,
                "bundle_key":        bk,
                "compression_label": _COMPRESSION_LABELS[tier],
            })

            if tier == 1:
                tier_1_reports.append(report_id)
            elif tier == 2:
                tier_2_reports.append(report_id)
            elif tier == 3:
                tier_3_reports.append(report_id)
            else:
                tier_4_reports.append(report_id)

        # ── Candidate summary lists ───────────────────────────────────────────
        executive_summary_candidates: List[str] = list(tier_1_reports)

        governance_summary_candidates: List[str] = [
            c["report_id"]
            for c in compression_map
            if c["tier"] == 2 and c["family"] == "GOVERNANCE"
        ]

        _ecological_families = frozenset({"COGNITIVE", "EPISTEMIC"})
        ecological_summary_candidates: List[str] = [
            c["report_id"]
            for c in compression_map
            if c["tier"] in (1, 2) and c["family"] in _ecological_families
        ]

        survivability_summary_candidates: List[str] = [
            c["report_id"]
            for c in compression_map
            if c["tier"] == 1 and c["family"] == "ECONOMIC"
        ]

        full_export_required: List[str] = [
            c["report_id"] for c in compression_map if c["tier"] in (1, 2)
        ]

        archive_only: List[str] = list(tier_4_reports)

        return {
            "report":                          "COMPRESSION_READINESS_REPORT",
            "total_reports":                   len(REPORT_REGISTRY),
            "tier_distribution":               tier_distribution,
            "tier_1_reports":                  tier_1_reports,
            "tier_2_reports":                  tier_2_reports,
            "tier_3_reports":                  tier_3_reports,
            "tier_4_reports":                  tier_4_reports,
            "compression_map":                 compression_map,
            "executive_summary_candidates":    executive_summary_candidates,
            "governance_summary_candidates":   governance_summary_candidates,
            "ecological_summary_candidates":   ecological_summary_candidates,
            "survivability_summary_candidates": survivability_summary_candidates,
            "full_export_required":            full_export_required,
            "archive_only":                    archive_only,
            "compression_readiness_score":     100,
            "compression_tier":                "HEALTHY",
            "auto_authorized":                 False,
            "generated_ts":                    int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":                          "COMPRESSION_READINESS_REPORT",
            "error":                           str(exc),
            "total_reports":                   0,
            "tier_distribution":               {1: 0, 2: 0, 3: 0, 4: 0},
            "tier_1_reports":                  [],
            "tier_2_reports":                  [],
            "tier_3_reports":                  [],
            "tier_4_reports":                  [],
            "compression_map":                 [],
            "executive_summary_candidates":    [],
            "governance_summary_candidates":   [],
            "ecological_summary_candidates":   [],
            "survivability_summary_candidates": [],
            "full_export_required":            [],
            "archive_only":                    [],
            "compression_readiness_score":     0,
            "compression_tier":                "CRITICAL",
            "auto_authorized":                 False,
            "generated_ts":                    int(_time.time() * 1000),
        }

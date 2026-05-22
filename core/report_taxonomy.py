"""
FTD-RTAG: Report Taxonomy — canonical classification, querying, and bundle governance.

Provides query functions over the report registry: by family, tier, bundle,
priority, and overlap. Also defines the canonical export bundle membership.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations
from typing import Dict, List, Set

from core.report_registry import (
    REPORT_REGISTRY,
    KNOWN_FAMILIES, KNOWN_TIERS, KNOWN_PRIORITIES,
    PRIORITY_CRITICAL, PRIORITY_HIGH,
    FAMILY_ECONOMIC, FAMILY_COGNITIVE, FAMILY_GOVERNANCE,
    FAMILY_EPISTEMIC, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT,
    FAMILY_REPLAY, FAMILY_FORENSICS,
)

# ── Bundle identifiers ────────────────────────────────────────────────────────
BUNDLE_EXECUTIVE      = "EXECUTIVE"
BUNDLE_RESEARCH       = "RESEARCH"
BUNDLE_GOVERNANCE     = "GOVERNANCE"
BUNDLE_EPISTEMIC      = "EPISTEMIC"
BUNDLE_CONTINUITY     = "CONTINUITY"
BUNDLE_MASTER_ARCHIVE = "MASTER_ARCHIVE"

KNOWN_BUNDLES: frozenset = frozenset({
    BUNDLE_EXECUTIVE, BUNDLE_RESEARCH, BUNDLE_GOVERNANCE,
    BUNDLE_EPISTEMIC, BUNDLE_CONTINUITY, BUNDLE_MASTER_ARCHIVE,
})

# ── Canonical bundle membership ───────────────────────────────────────────────
# MASTER_ARCHIVE includes every registered report.
BUNDLE_MEMBERSHIP: Dict[str, Set[str]] = {
    BUNDLE_EXECUTIVE: {
        "SUMMARY", "ECOLOGY", "RL_LEARNING", "ECONOMIC_GROUND_TRUTH",
        "SESSION_ATTRIBUTION", "EXPLORATION_DIAGNOSTICS", "GRVL",
    },
    BUNDLE_RESEARCH: {
        "PATTERNS", "NEGATIVE_MEMORY", "TOPOLOGY", "COGNITION",
        "ALPHA_DISCOVERY", "EXPLORATION_DIAGNOSTICS",
        "EXPLORATION_ECONOMIC_ATTRIBUTION", "TIMEFRAME_SURVIVABILITY",
        "REGIME_CARTOGRAPHY", "MEMORY_PRESSURE", "COUNTERFACTUAL_LAB",
    },
    BUNDLE_GOVERNANCE: {
        "SOVEREIGN_READINESS", "GAGS", "GADD", "GRVL", "GMPD",
        "CKPD", "LHEO", "HMAO",
    },
    BUNDLE_EPISTEMIC: {
        "EIOD", "EXPLORATION_DIAGNOSTICS", "EXPLORATION_ECONOMIC_ATTRIBUTION",
    },
    BUNDLE_CONTINUITY: {
        "CKPD", "LHEO", "HMAO", "COGNITION", "MEMORY_PRESSURE",
    },
    BUNDLE_MASTER_ARCHIVE: set(REPORT_REGISTRY.keys()),
}


# ── Family query functions ────────────────────────────────────────────────────

def get_reports_by_family(family: str) -> List[dict]:
    """All registry entries whose report_family equals family."""
    return [r for r in REPORT_REGISTRY.values() if r.get("report_family") == family]


def get_family_ids(family: str) -> List[str]:
    """Report IDs in a given family, sorted."""
    return sorted(r["report_id"] for r in get_reports_by_family(family))


# ── Tier query functions ──────────────────────────────────────────────────────

def get_reports_by_tier(tier: str) -> List[dict]:
    """All registry entries whose export_tier equals tier."""
    return [r for r in REPORT_REGISTRY.values() if r.get("export_tier") == tier]


def get_tier_ids(tier: str) -> List[str]:
    """Report IDs in a given tier, sorted."""
    return sorted(r["report_id"] for r in get_reports_by_tier(tier))


# ── Priority query functions ──────────────────────────────────────────────────

def get_reports_by_priority(priority: str) -> List[str]:
    return sorted(
        r_id for r_id, spec in REPORT_REGISTRY.items()
        if spec.get("archive_priority") == priority
    )


# ── Bundle query functions ────────────────────────────────────────────────────

def get_reports_in_bundle(bundle: str) -> List[str]:
    """Sorted list of report IDs in a bundle."""
    return sorted(BUNDLE_MEMBERSHIP.get(bundle, set()))


def get_bundles_for_report(report_id: str) -> List[str]:
    """Which bundles include this report (including MASTER_ARCHIVE)."""
    return sorted(b for b, members in BUNDLE_MEMBERSHIP.items() if report_id in members)


# ── Orphan detection ──────────────────────────────────────────────────────────

def get_orphaned_reports() -> List[str]:
    """
    Reports not assigned to any non-MASTER_ARCHIVE bundle.
    Orphaned reports risk archival invisibility.
    """
    non_master_coverage: Set[str] = set()
    for bundle, members in BUNDLE_MEMBERSHIP.items():
        if bundle != BUNDLE_MASTER_ARCHIVE:
            non_master_coverage |= members
    return sorted(r_id for r_id in REPORT_REGISTRY if r_id not in non_master_coverage)


# ── All-families / all-tiers ──────────────────────────────────────────────────

def get_all_families() -> List[str]:
    """Distinct families present in the registry, sorted."""
    return sorted({r.get("report_family", "") for r in REPORT_REGISTRY.values()})


def get_all_tiers() -> List[str]:
    """Distinct export tiers present in the registry, sorted."""
    return sorted({r.get("export_tier", "") for r in REPORT_REGISTRY.values()})


# ── Coverage summary ──────────────────────────────────────────────────────────

def get_coverage_summary() -> dict:
    return {
        "total_reports":       len(REPORT_REGISTRY),
        "families_represented": get_all_families(),
        "family_count":        len(get_all_families()),
        "tiers_represented":   get_all_tiers(),
        "tier_count":          len(get_all_tiers()),
        "family_breakdown": {
            fam: len(get_reports_by_family(fam))
            for fam in sorted(KNOWN_FAMILIES)
        },
        "tier_breakdown": {
            tier: len(get_reports_by_tier(tier))
            for tier in sorted(KNOWN_TIERS)
        },
        "bundle_breakdown": {
            bundle: len(members)
            for bundle, members in BUNDLE_MEMBERSHIP.items()
        },
        "orphaned_reports":    get_orphaned_reports(),
        "orphaned_count":      len(get_orphaned_reports()),
        "critical_priority":   get_reports_by_priority(PRIORITY_CRITICAL),
        "high_priority":       get_reports_by_priority(PRIORITY_HIGH),
    }

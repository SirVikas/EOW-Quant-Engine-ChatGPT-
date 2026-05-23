"""
PRP-PHASEB.2 — Cross-Report Propagation Audit.

Verifies that every registry report propagates correctly into the dashboard
tab manifest and that every lio_report_bundle key is accounted for (either
as a registry bundle_key or as an expected extended-governance key).

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import List, Set


# ── All 29 keys returned by lio_report_bundle() ──────────────────────────────
KNOWN_BUNDLE_KEYS: frozenset = frozenset({
    "summary",
    "patterns",
    "negative_memory",
    "ecology",
    "rl",
    "topology",
    "cognition",
    "sovereign_readiness",
    "alpha_discovery",
    "session_attribution",
    "exploration_diagnostics",
    "exploration_economic_attribution",
    "economic_ground_truth",
    "timeframe_survivability",
    "regime_survivability_cartography",
    "memory_pressure_dynamics",
    "counterfactual_interventions",
    "adaptive_governance_simulator",
    "governed_adaptive_doctrine",
    "reality_verification",
    "guarded_micro_pilot",
    "long_horizon_evolution",
    "constitutional_recovery_observatory",
    "epistemic_integrity_observatory",
    "human_meaning_alignment",
    # ── 4 extended-governance keys (not in REPORT_REGISTRY) ──────────────────
    "report_ecosystem_governance",
    "export_infrastructure_governance",
    "download_center_governance",
    "institutional_reporting_experience",
})

# ── The 4 extra bundle keys that extend beyond the 25-report registry ─────────
EXTENDED_GOVERNANCE_KEYS: frozenset = frozenset({
    "report_ecosystem_governance",
    "export_infrastructure_governance",
    "download_center_governance",
    "institutional_reporting_experience",
})


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "WEAK"
    return "CRITICAL"


def audit_report_propagation() -> dict:
    """
    PRP-PHASEB.2 — Verify that registry reports propagate into the dashboard
    and that bundle keys are fully accounted for.

    Returns a self-contained audit dict; never raises.
    """
    try:
        from core.report_registry import REPORT_REGISTRY       # lazy
        from core.dashboard_orchestrator import build_tab_manifest  # lazy

        # ── Collect registry facts ────────────────────────────────────────────
        registry_bundle_keys: Set[str] = {
            meta.get("bundle_key", "")
            for meta in REPORT_REGISTRY.values()
            if meta.get("bundle_key")
        }
        registry_report_ids: Set[str] = set(REPORT_REGISTRY.keys())

        # ── Dashboard facts ───────────────────────────────────────────────────
        manifest = build_tab_manifest()
        dashboard_report_ids: Set[str] = set()
        for tab in manifest.get("tabs", []):
            for rid in tab.get("report_ids", []):
                dashboard_report_ids.add(rid)

        # ── Coverage computations ─────────────────────────────────────────────
        # registry bundle_keys vs KNOWN_BUNDLE_KEYS (the 29 known keys)
        registry_keys_in_known = registry_bundle_keys & KNOWN_BUNDLE_KEYS
        registry_to_bundle_coverage: float = (
            round(len(registry_keys_in_known) / len(registry_bundle_keys) * 100, 1)
            if registry_bundle_keys else 0.0
        )

        # registry report_ids vs dashboard report_ids
        ids_in_dashboard = registry_report_ids & dashboard_report_ids
        registry_to_dashboard_coverage: float = (
            round(len(ids_in_dashboard) / len(registry_report_ids) * 100, 1)
            if registry_report_ids else 0.0
        )

        # ── Ghost reports: in registry but NOT visible in dashboard ───────────
        ghost_reports: List[str] = sorted(registry_report_ids - dashboard_report_ids)

        # ── Orphan bundle keys: in KNOWN_BUNDLE_KEYS but not registry or EG ──
        # (These would indicate a bundle key was added to lio_report_bundle
        #  without a corresponding registry entry and without being classified
        #  as extended governance — a true wiring gap.)
        orphan_bundle_keys: List[str] = sorted(
            KNOWN_BUNDLE_KEYS - registry_bundle_keys - EXTENDED_GOVERNANCE_KEYS
        )

        # ── Extended governance classification ────────────────────────────────
        extended_governance_count: int = len(EXTENDED_GOVERNANCE_KEYS)

        # ── Scoring ───────────────────────────────────────────────────────────
        propagation_score: int = 100
        for _ in ghost_reports:
            propagation_score -= 20
        for _ in orphan_bundle_keys:
            propagation_score -= 10
        propagation_score = max(0, propagation_score)

        return {
            "report":                        "REPORT_PROPAGATION_AUDIT",
            "registry_count":                len(registry_report_ids),
            "bundle_count":                  len(KNOWN_BUNDLE_KEYS),
            "dashboard_count":               len(dashboard_report_ids),
            "registry_bundle_key_count":     len(registry_bundle_keys),
            "registry_to_bundle_coverage":   registry_to_bundle_coverage,
            "registry_to_dashboard_coverage": registry_to_dashboard_coverage,
            "ghost_reports":                 ghost_reports,
            "orphan_bundle_keys":            orphan_bundle_keys,
            "extended_governance_count":     extended_governance_count,
            "extended_governance_keys":      sorted(EXTENDED_GOVERNANCE_KEYS),
            "propagation_score":             propagation_score,
            "propagation_tier":              _score_tier(propagation_score),
            "auto_authorized":               False,
            "generated_ts":                  int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":                        "REPORT_PROPAGATION_AUDIT",
            "error":                         str(exc),
            "registry_count":                0,
            "bundle_count":                  len(KNOWN_BUNDLE_KEYS),
            "dashboard_count":               0,
            "registry_bundle_key_count":     0,
            "registry_to_bundle_coverage":   0.0,
            "registry_to_dashboard_coverage": 0.0,
            "ghost_reports":                 [],
            "orphan_bundle_keys":            [],
            "extended_governance_count":     len(EXTENDED_GOVERNANCE_KEYS),
            "extended_governance_keys":      sorted(EXTENDED_GOVERNANCE_KEYS),
            "propagation_score":             0,
            "propagation_tier":              "CRITICAL",
            "auto_authorized":               False,
            "generated_ts":                  int(_time.time() * 1000),
        }

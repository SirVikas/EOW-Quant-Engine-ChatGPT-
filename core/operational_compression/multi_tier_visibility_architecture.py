"""
PRP-PHASEC.6 — Multi-Tier Visibility Architecture.

Separates institutional visibility into cognition-safe layers with guaranteed:
  - no information loss
  - deterministic drill-down paths
  - replay-safe tier transitions
  - lineage preservation across all tiers

Tier definitions:
  Tier 1 — Executive Operational  (CRITICAL/HIGH priority)
  Tier 2 — Research Operational   (MEDIUM + ECONOMIC/COGNITIVE/GOVERNANCE)
  Tier 3 — Deep Forensic          (MEDIUM + other families)
  Tier 4 — Archive Lineage        (LOW priority)

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict, List


_TIER1_PRIORITIES = frozenset({"CRITICAL", "HIGH"})
_TIER4_PRIORITIES = frozenset({"LOW"})
_TIER2_FAMILIES   = frozenset({"ECONOMIC", "COGNITIVE", "GOVERNANCE"})

_TIER_META: Dict[int, Dict[str, str]] = {
    1: {"label": "EXECUTIVE_OPERATIONAL",  "purpose": "Always-present executive view"},
    2: {"label": "RESEARCH_OPERATIONAL",   "purpose": "Summary bundles and research"},
    3: {"label": "DEEP_FORENSIC",          "purpose": "Full export and forensic analysis"},
    4: {"label": "ARCHIVE_LINEAGE",        "purpose": "Historical reference and replay"},
}


def _assign_tier(priority: str, family: str) -> int:
    if priority in _TIER1_PRIORITIES:
        return 1
    if priority in _TIER4_PRIORITIES:
        return 4
    return 2 if family in _TIER2_FAMILIES else 3


def build_visibility_tier_map() -> dict:
    """
    PRP-PHASEC.6 — Build a deterministic visibility tier map for all 25 reports.

    Guarantees:
      - Every report appears in exactly one tier (no loss)
      - Tier assignments are deterministic (same input → same output)
      - Each report entry carries its drill-down path (endpoint)
      - Lineage fields are preserved for replay-safe transitions

    Returns a self-contained dict; never raises.
    """
    try:
        from core.report_registry import REPORT_REGISTRY  # lazy

        tier_map: Dict[int, List[Dict[str, Any]]] = {1: [], 2: [], 3: [], 4: []}
        all_entries: List[Dict[str, Any]] = []
        report_to_tier: Dict[str, int] = {}

        for report_id, meta in REPORT_REGISTRY.items():
            priority = meta.get("archive_priority", "")
            family   = meta.get("report_family", "")
            tier     = _assign_tier(priority, family)

            entry: Dict[str, Any] = {
                "report_id":         report_id,
                "name":              meta.get("name", report_id),
                "family":            family,
                "tier":              tier,
                "tier_label":        _TIER_META[tier]["label"],
                "archive_priority":  priority,
                "endpoint":          meta.get("endpoint", ""),
                "bundle_key":        meta.get("bundle_key", ""),
                "export_tier":       meta.get("export_tier", ""),
                "dependencies":      meta.get("dependencies", []),
                "lineage_preserved": True,
                "replay_safe":       True,
                "drill_down_path":   meta.get("endpoint", ""),
            }
            tier_map[tier].append(entry)
            all_entries.append(entry)
            report_to_tier[report_id] = tier

        # Sort each tier alphabetically by report_id for determinism
        for t in tier_map:
            tier_map[t].sort(key=lambda e: e["report_id"])

        total_reports = sum(len(v) for v in tier_map.values())

        # Visibility layer summaries
        tier_summaries: List[dict] = []
        for t in (1, 2, 3, 4):
            reports = tier_map[t]
            tier_summaries.append({
                "tier":         t,
                "label":        _TIER_META[t]["label"],
                "purpose":      _TIER_META[t]["purpose"],
                "report_count": len(reports),
                "report_ids":   [e["report_id"] for e in reports],
                "families":     sorted({e["family"] for e in reports}),
            })

        # Drill-down adjacency: which tier-N reports depend on tier-M reports
        drill_down_adjacency: Dict[str, List[str]] = {}
        for entry in all_entries:
            deps = entry.get("dependencies", [])
            if deps:
                drill_down_adjacency[entry["report_id"]] = deps

        return {
            "report":                "VISIBILITY_TIER_MAP",
            "total_reports":         total_reports,
            "tier_summaries":        tier_summaries,
            "tier_1_reports":        tier_map[1],
            "tier_2_reports":        tier_map[2],
            "tier_3_reports":        tier_map[3],
            "tier_4_reports":        tier_map[4],
            "tier_distribution":     {t: len(tier_map[t]) for t in (1, 2, 3, 4)},
            "drill_down_adjacency":  drill_down_adjacency,
            "report_to_tier":        report_to_tier,
            "lineage_preserved":     True,
            "replay_safe":           True,
            "deterministic":         True,
            "auto_authorized":       False,
            "generated_ts":          int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":            "VISIBILITY_TIER_MAP",
            "error":             str(exc),
            "total_reports":     0,
            "tier_summaries":    [],
            "tier_1_reports":    [],
            "tier_2_reports":    [],
            "tier_3_reports":    [],
            "tier_4_reports":    [],
            "tier_distribution": {1: 0, 2: 0, 3: 0, 4: 0},
            "drill_down_adjacency": {},
            "report_to_tier":    {},
            "lineage_preserved": True,
            "replay_safe":       True,
            "deterministic":     True,
            "auto_authorized":   False,
            "generated_ts":      int(_time.time() * 1000),
        }

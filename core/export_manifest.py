"""
FTD-UEI: Archive Manifest Infrastructure.

Every PHOENIX export bundle gets a manifest describing its content,
dependency topology, export order, and reconstruction fingerprint.

The manifest is the forensic index of an export: future systems
(human or AI) can use it to understand, replay, or reconstruct
what was exported and why.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import json
import time as _time
from typing import Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_dependency_graph import topological_sort, get_dependencies
from core.reconstruction_hashing import dict_hash


def generate_manifest(
    bundle_type: str,
    report_ids: List[str],
    metadata: dict,
    generation_ts: Optional[int] = None,
) -> dict:
    """
    Generate a canonical archive manifest for a bundle.

    The manifest_hash covers the bundle_type, sorted report_ids,
    export_order, and generation_ts so that any tampering changes the hash.
    """
    ts = generation_ts or int(_time.time() * 1000)

    # Topological export order filtered to this bundle's reports
    topo       = topological_sort()
    id_set     = set(report_ids)
    exp_order  = [r for r in topo if r in id_set]
    # Any reports not in topo (shouldn't happen) appended at end
    remaining  = sorted(r for r in report_ids if r not in exp_order)
    exp_order += remaining

    # Lineage graph: dependencies within the bundle
    lineage_graph: Dict[str, List[str]] = {
        r_id: [d for d in get_dependencies(r_id) if d in id_set]
        for r_id in report_ids
    }

    # Dependency map (full, including deps outside bundle)
    dependency_map: Dict[str, List[str]] = {
        r_id: get_dependencies(r_id) for r_id in report_ids
    }

    # Bundle topology: primitives vs dependents within the bundle
    primitives  = [r for r in report_ids if not lineage_graph.get(r)]
    dependents  = [r for r in report_ids if lineage_graph.get(r)]

    # Metadata summary (safe subset for manifest)
    meta_summary = {
        k: metadata.get(k)
        for k in ("app_version", "doctrine_version", "lineage_epoch", "export_bundle_type")
    }

    # Build full manifest body (excluding manifest_id and manifest_hash)
    # so verify_manifest_hash can recompute the same hash
    manifest_body = {
        "bundle_type":      bundle_type,
        "generation_ts":    ts,
        "report_count":     len(report_ids),
        "report_ids":       sorted(report_ids),
        "export_order":     exp_order,
        "lineage_graph":    lineage_graph,
        "dependency_map":   dependency_map,
        "bundle_topology":  {
            "primitives":  primitives,
            "dependents":  dependents,
        },
        "metadata_summary": meta_summary,
        "auto_authorized":  False,
        "immutable":        True,
    }
    m_hash = dict_hash(manifest_body)

    return {
        "manifest_id":  f"MNF-{bundle_type}-{ts}-{m_hash[:12]}",
        "manifest_hash": m_hash,
        **manifest_body,
    }


def validate_manifest(manifest: dict) -> tuple[bool, list]:
    """
    Basic structural validation of a manifest dict.
    Returns (is_valid, list_of_issues).
    """
    required = (
        "manifest_id", "manifest_hash", "bundle_type",
        "generation_ts", "report_ids", "export_order",
        "lineage_graph", "dependency_map",
    )
    issues = [f for f in required if f not in manifest]
    if manifest.get("auto_authorized") is True:
        issues.append("auto_authorized must be False")
    return (len(issues) == 0, issues)

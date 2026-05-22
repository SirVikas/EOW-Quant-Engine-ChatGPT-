"""
FTD-UDCA: Tests for the Unified Institutional Download Center & Archive Experience Layer.

Validates:
  - Archive browser (browsing, filtering, timeline, manifest preview)
  - Replay explorer (lineage replay, snapshot comparison, era comparison, timeline)
  - Export preview (bundle preview, manifest preview, dependency chain, size, continuity)
  - Archive visualization (dependency graph, bundle topology, lineage tree, continuity flow,
    export relationship map)
  - Institutional search (report search, snapshot search, bundle search, search index)
  - Download center governance orchestrator (health score, audit entry, recommendations)
  - Constitutional constraints (all auto_authorized=False, hard principles)
  - Production isolation (no side effects, fail-open)
  - Edge cases

Production isolation guarantee: no live trading state is touched.
"""
from __future__ import annotations

import time
import pytest

from core.archive_browser import (
    browse_snapshots, get_archive_timeline,
    get_snapshot_manifest_preview, get_browser_health,
)
from core.replay_explorer import (
    replay_lineage, compare_snapshots, compare_eras,
    get_replay_timeline, get_replay_health,
)
from core.export_preview import (
    preview_bundle, preview_manifest, preview_dependency_chain,
    preview_archive_size, preview_continuity_scope, get_preview_health,
)
from core.archive_visualization import (
    build_dependency_graph, build_bundle_topology, build_lineage_tree,
    build_continuity_flow, build_export_relationship_map, get_visualization_health,
)
from core.institutional_search import (
    build_search_index, search_reports, search_snapshots, search_bundles,
    get_search_health,
)
from core.download_dashboard import (
    compute_download_center_governance, DOWNLOAD_CENTER_HARD_PRINCIPLES,
)
from core.snapshot_manager import create_snapshot_record, SNAPSHOT_TYPES
from core.report_registry import REPORT_REGISTRY, EXPECTED_REPORT_COUNT
from core.report_taxonomy import BUNDLE_MEMBERSHIP


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_snapshots(n: int = 14) -> list:
    types = sorted(SNAPSHOT_TYPES)
    snaps = []
    base  = 1_700_000_000_000
    for i in range(n):
        s = create_snapshot_record(
            snapshot_type=types[i % len(types)],
            app_version=f"1.{i // len(types)}.0",
            trade_count=i * 100,
            label=f"snap-{i}",
            triggered_by="TEST",
            generation_ts=base + i * 3_600_000,
        )
        snaps.append(s)
    return snaps


# ── TestArchiveBrowser ────────────────────────────────────────────────────────

class TestArchiveBrowser:
    def test_browse_no_filters_returns_all(self):
        snaps = _make_snapshots(10)
        result = browse_snapshots(snaps)
        assert result["browse_healthy"] is True
        assert result["total_snapshots"] == 10

    def test_browse_filter_by_type(self):
        snaps = _make_snapshots(14)
        first_type = sorted(SNAPSHOT_TYPES)[0]
        result = browse_snapshots(snaps, filters={"snapshot_type": first_type})
        assert result["browse_healthy"] is True
        for s in result["snapshots"]:
            assert s["snapshot_type"] == first_type

    def test_browse_filter_by_version(self):
        snaps = _make_snapshots(14)
        result = browse_snapshots(snaps, filters={"app_version": "1.0.0"})
        assert result["browse_healthy"] is True
        for s in result["snapshots"]:
            assert s["app_version"] == "1.0.0"

    def test_browse_filter_by_date_range(self):
        snaps = _make_snapshots(10)
        mid_ts = 1_700_000_000_000 + 5 * 3_600_000
        result = browse_snapshots(snaps, filters={"to_ts": mid_ts})
        assert result["browse_healthy"] is True
        for s in result["snapshots"]:
            assert s["timestamp_ms"] <= mid_ts

    def test_browse_filter_by_triggered_by(self):
        snaps = _make_snapshots(5)
        result = browse_snapshots(snaps, filters={"triggered_by": "TEST"})
        assert result["browse_healthy"] is True
        assert result["total_snapshots"] == 5

    def test_browse_pagination(self):
        snaps = _make_snapshots(20)
        page1 = browse_snapshots(snaps, page=1, page_size=5)
        page2 = browse_snapshots(snaps, page=2, page_size=5)
        assert page1["browse_healthy"] is True
        assert len(page1["snapshots"]) == 5
        assert len(page2["snapshots"]) == 5
        assert page1["has_next"] is True
        assert page2["has_prev"] is True
        # Different snapshots on different pages
        ids1 = {s["snapshot_id"] for s in page1["snapshots"]}
        ids2 = {s["snapshot_id"] for s in page2["snapshots"]}
        assert ids1.isdisjoint(ids2)

    def test_browse_empty_snapshots(self):
        result = browse_snapshots([])
        assert result["browse_healthy"] is True
        assert result["total_snapshots"] == 0
        assert result["snapshots"] == []

    def test_browse_result_is_chronological(self):
        snaps = _make_snapshots(10)
        result = browse_snapshots(snaps)
        timestamps = [s["timestamp_ms"] for s in result["snapshots"]]
        assert timestamps == sorted(timestamps)

    def test_get_archive_timeline(self):
        snaps = _make_snapshots(7)
        result = get_archive_timeline(snaps)
        assert result["timeline_healthy"] is True
        assert result["timeline_length"] == 7
        assert len(result["timeline"]) == 7
        for i, entry in enumerate(result["timeline"]):
            assert entry["index"] == i + 1

    def test_get_archive_timeline_empty(self):
        result = get_archive_timeline([])
        assert result["timeline_healthy"] is True
        assert result["timeline_length"] == 0
        assert result["earliest_timestamp"] is None

    def test_get_archive_timeline_has_hash_validity(self):
        snaps = _make_snapshots(3)
        result = get_archive_timeline(snaps)
        for entry in result["timeline"]:
            assert "hash_valid" in entry
            assert entry["hash_valid"] is True

    def test_get_snapshot_manifest_preview(self):
        snap = _make_snapshots(1)[0]
        result = get_snapshot_manifest_preview(snap)
        assert result["preview_healthy"] is True
        assert result["snapshot_id"] == snap["snapshot_id"]
        assert result["hash_valid"] is True
        assert result["auto_authorized"] is False
        assert result["immutable"] is True

    def test_get_browser_health_with_snapshots(self):
        snaps = _make_snapshots(7)
        result = get_browser_health(snaps)
        assert result["browser_healthy"] is True
        assert result["total_snapshots"] == 7

    def test_get_browser_health_empty(self):
        result = get_browser_health([])
        assert result["browser_healthy"] is True
        assert result["total_snapshots"] == 0


# ── TestReplayExplorer ────────────────────────────────────────────────────────

class TestReplayExplorer:
    def test_replay_lineage_known_report(self):
        result = replay_lineage("SUMMARY", [])
        assert result["replay_healthy"] is True
        assert result["report_id"] == "SUMMARY"
        assert "replay_events" in result

    def test_replay_lineage_unknown_report(self):
        result = replay_lineage("NONEXISTENT_REPORT", [])
        assert result["replay_healthy"] is False
        assert "error" in result

    def test_replay_lineage_with_snapshots(self):
        snaps  = _make_snapshots(5)
        result = replay_lineage("SUMMARY", snaps)
        assert result["replay_healthy"] is True
        assert result["replay_event_count"] == 5
        assert len(result["replay_events"]) == 5

    def test_replay_lineage_primitive_has_no_deps(self):
        result = replay_lineage("SUMMARY", [])
        assert result["dependency_count"] == 0
        assert result["dependencies"] == []

    def test_replay_lineage_dependent_has_deps(self):
        # ECOLOGY depends on SUMMARY and others
        result = replay_lineage("ECOLOGY", [])
        assert result["replay_healthy"] is True
        assert result["dependency_count"] > 0

    def test_compare_snapshots_basic(self):
        snaps = _make_snapshots(2)
        result = compare_snapshots(snaps[0], snaps[1])
        assert result["compare_healthy"] is True
        assert "elapsed_ms" in result
        assert "version_changed" in result

    def test_compare_snapshots_chronological_order(self):
        snaps = _make_snapshots(2)
        # Whichever order they're passed, result is deterministic
        r1 = compare_snapshots(snaps[0], snaps[1])
        r2 = compare_snapshots(snaps[1], snaps[0])
        assert r1["snapshot_a_id"] == r2["snapshot_a_id"]
        assert r1["chronological"] is True

    def test_compare_snapshots_version_change_detected(self):
        snaps = _make_snapshots(14)
        # snaps[0] is v1.0.0, snaps[7] is v1.1.0
        result = compare_snapshots(snaps[0], snaps[7])
        assert result["compare_healthy"] is True
        assert result["version_changed"] is True

    def test_compare_eras_empty(self):
        result = compare_eras([], [], "A", "B")
        assert result["compare_healthy"] is True
        assert result["era_a"]["count"] == 0
        assert result["era_b"]["count"] == 0

    def test_compare_eras_with_data(self):
        snaps = _make_snapshots(14)
        result = compare_eras(snaps[:7], snaps[7:], "EARLY", "LATE")
        assert result["compare_healthy"] is True
        assert result["era_a_label"] == "EARLY"
        assert result["era_b_label"] == "LATE"
        assert result["era_a"]["count"] == 7
        assert result["era_b"]["count"] == 7

    def test_get_replay_timeline_empty(self):
        result = get_replay_timeline([])
        assert result["replay_healthy"] is True
        assert result["event_count"] == 0

    def test_get_replay_timeline_with_snapshots(self):
        snaps  = _make_snapshots(7)
        result = get_replay_timeline(snaps)
        assert result["replay_healthy"] is True
        assert result["event_count"] == 7

    def test_get_replay_timeline_version_transitions_detected(self):
        snaps  = _make_snapshots(14)
        result = get_replay_timeline(snaps)
        assert result["replay_healthy"] is True
        assert result["version_transitions"] >= 1

    def test_get_replay_health(self):
        snaps  = _make_snapshots(5)
        result = get_replay_health(snaps)
        assert result["replay_healthy"] is True
        assert result["snapshot_count"] == 5


# ── TestExportPreview ─────────────────────────────────────────────────────────

class TestExportPreview:
    def test_preview_bundle_executive(self):
        result = preview_bundle("EXECUTIVE")
        assert result["preview_healthy"] is True
        assert result["bundle_type"] == "EXECUTIVE"
        assert result["report_count"] > 0
        assert result["auto_authorized"] is False

    def test_preview_bundle_all_canonical_bundles(self):
        for bt in BUNDLE_MEMBERSHIP:
            result = preview_bundle(bt)
            assert result["preview_healthy"] is True, f"{bt} preview failed"
            assert result["report_count"] > 0

    def test_preview_bundle_unknown(self):
        result = preview_bundle("NONEXISTENT_BUNDLE_TYPE")
        assert result["preview_healthy"] is False
        assert "error" in result

    def test_preview_bundle_has_export_order(self):
        result = preview_bundle("EXECUTIVE")
        assert "export_order" in result
        assert len(result["export_order"]) == result["report_count"]

    def test_preview_bundle_has_size_estimates(self):
        result = preview_bundle("EXECUTIVE")
        assert result["estimated_json_bytes"] > 0
        assert result["estimated_json_kb"] > 0

    def test_preview_manifest(self):
        result = preview_manifest("EXECUTIVE")
        assert result["preview_healthy"] is True
        assert result["manifest_id_preview"].startswith("MNF-")
        assert result["manifest_hash_valid"] is True
        assert result["auto_authorized"] is False

    def test_preview_manifest_all_bundles(self):
        for bt in BUNDLE_MEMBERSHIP:
            result = preview_manifest(bt)
            assert result["preview_healthy"] is True, f"{bt} manifest preview failed"

    def test_preview_manifest_unknown_bundle(self):
        result = preview_manifest("UNKNOWN")
        assert result["preview_healthy"] is False

    def test_preview_dependency_chain_primitive(self):
        result = preview_dependency_chain("SUMMARY")
        assert result["preview_healthy"] is True
        assert result["is_primitive"] is True
        assert result["total_dep_count"] == 0
        assert result["direct_dependencies"] == []

    def test_preview_dependency_chain_dependent(self):
        # ECOLOGY has dependencies
        result = preview_dependency_chain("ECOLOGY")
        assert result["preview_healthy"] is True
        assert result["is_primitive"] is False
        assert result["total_dep_count"] > 0

    def test_preview_dependency_chain_unknown(self):
        result = preview_dependency_chain("NO_SUCH_REPORT")
        assert result["preview_healthy"] is False

    def test_preview_dependency_chain_containing_bundles(self):
        result = preview_dependency_chain("SUMMARY")
        assert len(result["containing_bundles"]) > 0
        assert "MASTER_ARCHIVE" in result["containing_bundles"]

    def test_preview_archive_size(self):
        result = preview_archive_size("EXECUTIVE")
        assert result["preview_healthy"] is True
        assert result["report_count"] > 0
        assert result["estimated_json_bytes"] > 0
        assert result["estimated_zip_kb"] < result["estimated_json_kb"]

    def test_preview_archive_size_unknown_bundle(self):
        result = preview_archive_size("UNKNOWN")
        assert result["preview_healthy"] is False

    def test_preview_continuity_scope_empty(self):
        result = preview_continuity_scope([])
        assert result["preview_healthy"] is True
        assert result["snapshot_count"] == 0
        assert result["continuity_scope"] == "EMPTY"

    def test_preview_continuity_scope_single_era(self):
        snaps  = _make_snapshots(7)
        # Force all same version
        for s in snaps:
            s["app_version"] = "1.0.0"
        result = preview_continuity_scope(snaps)
        assert result["preview_healthy"] is True
        assert result["continuity_scope"] == "SINGLE_ERA"

    def test_preview_continuity_scope_multi_era(self):
        snaps = _make_snapshots(14)
        result = preview_continuity_scope(snaps)
        assert result["preview_healthy"] is True
        assert result["continuity_scope"] == "MULTI_ERA"

    def test_get_preview_health(self):
        result = get_preview_health()
        assert result["preview_healthy"] is True
        assert result["preview_operational"] is True


# ── TestArchiveVisualization ──────────────────────────────────────────────────

class TestArchiveVisualization:
    def test_build_dependency_graph_all_reports(self):
        result = build_dependency_graph()
        assert result["graph_healthy"] is True
        assert result["node_count"] == EXPECTED_REPORT_COUNT
        assert result["visualization_type"] == "DEPENDENCY_GRAPH"

    def test_dependency_graph_has_primitives(self):
        result = build_dependency_graph()
        assert len(result["primitives"]) >= 1
        # SUMMARY, ECONOMIC_GROUND_TRUTH, CKPD are primitives
        for p in ("SUMMARY", "ECONOMIC_GROUND_TRUTH", "CKPD"):
            assert p in result["primitives"]

    def test_dependency_graph_no_self_edges(self):
        result = build_dependency_graph()
        for edge in result["edges"]:
            assert edge["source"] != edge["target"]

    def test_dependency_graph_subset(self):
        ids    = ["SUMMARY", "ECOLOGY", "ECONOMIC_GROUND_TRUTH"]
        result = build_dependency_graph(ids)
        assert result["graph_healthy"] is True
        assert result["node_count"] == 3

    def test_dependency_graph_topological_order_length(self):
        result = build_dependency_graph()
        assert len(result["topological_order"]) == EXPECTED_REPORT_COUNT

    def test_build_bundle_topology_executive(self):
        result = build_bundle_topology("EXECUTIVE")
        assert result["graph_healthy"] is True
        assert result["bundle_type"] == "EXECUTIVE"
        assert result["visualization_type"] == "BUNDLE_TOPOLOGY"
        assert "family_groups" in result

    def test_build_bundle_topology_all_bundles(self):
        for bt in BUNDLE_MEMBERSHIP:
            result = build_bundle_topology(bt)
            assert result["graph_healthy"] is True, f"{bt} topology failed"

    def test_build_bundle_topology_unknown_bundle(self):
        result = build_bundle_topology("NONEXISTENT")
        assert result["graph_healthy"] is False

    def test_build_lineage_tree_empty(self):
        result = build_lineage_tree([])
        assert result["graph_healthy"] is True
        assert result["node_count"] == 0
        assert result["edge_count"] == 0

    def test_build_lineage_tree_with_snapshots(self):
        snaps  = _make_snapshots(7)
        result = build_lineage_tree(snaps)
        assert result["graph_healthy"] is True
        assert result["node_count"] == 7
        assert result["edge_count"] == 6  # n-1 temporal edges
        assert result["visualization_type"] == "LINEAGE_TREE"

    def test_lineage_tree_version_transitions_annotated(self):
        snaps  = _make_snapshots(14)
        result = build_lineage_tree(snaps)
        assert result["graph_healthy"] is True
        assert len(result["version_transitions"]) >= 1

    def test_build_continuity_flow(self):
        snaps  = _make_snapshots(7)
        result = build_continuity_flow(snaps)
        assert result["graph_healthy"] is True
        assert result["node_count"] == 7
        assert result["visualization_type"] == "CONTINUITY_FLOW"

    def test_continuity_flow_milestone_detection(self):
        snaps  = _make_snapshots(14)
        result = build_continuity_flow(snaps)
        assert result["graph_healthy"] is True
        assert result["milestone_count"] >= 1

    def test_build_export_relationship_map(self):
        result = build_export_relationship_map()
        assert result["graph_healthy"] is True
        assert result["visualization_type"] == "EXPORT_RELATIONSHIP_MAP"
        # nodes = 6 bundles + 25 reports
        assert result["node_count"] == len(BUNDLE_MEMBERSHIP) + EXPECTED_REPORT_COUNT

    def test_export_relationship_map_overlaps(self):
        result = build_export_relationship_map()
        # MASTER_ARCHIVE overlaps with every other bundle
        overlaps = result["bundle_overlaps"]
        master_overlaps = [o for o in overlaps
                           if "MASTER_ARCHIVE" in (o["bundle_a"], o["bundle_b"])]
        assert len(master_overlaps) == len(BUNDLE_MEMBERSHIP) - 1

    def test_get_visualization_health(self):
        result = get_visualization_health()
        assert result["visualization_healthy"] is True
        assert result["visualization_operational"] is True
        assert result["node_count"] == EXPECTED_REPORT_COUNT


# ── TestInstitutionalSearch ───────────────────────────────────────────────────

class TestInstitutionalSearch:
    def test_build_search_index_structure(self):
        index = build_search_index()
        assert index["total_reports"] == EXPECTED_REPORT_COUNT
        assert len(index["all_bundle_types"]) == len(BUNDLE_MEMBERSHIP)
        assert len(index["all_families"]) > 0
        assert len(index["all_tiers"]) > 0

    def test_build_search_index_all_reports_indexed(self):
        index = build_search_index()
        all_ids = set(index["all_report_ids"])
        assert all_ids == set(REPORT_REGISTRY.keys())

    def test_search_reports_no_filter_returns_all(self):
        result = search_reports()
        assert result["search_healthy"] is True
        assert result["result_count"] == EXPECTED_REPORT_COUNT

    def test_search_reports_by_family(self):
        result = search_reports(family="ECONOMIC")
        assert result["search_healthy"] is True
        for r in result["results"]:
            assert r["report_family"] == "ECONOMIC"

    def test_search_reports_by_query(self):
        result = search_reports(query="SUMMARY")
        assert result["search_healthy"] is True
        ids = [r["report_id"] for r in result["results"]]
        assert "SUMMARY" in ids

    def test_search_reports_by_bundle(self):
        result = search_reports(bundle_type="EXECUTIVE")
        assert result["search_healthy"] is True
        from core.report_taxonomy import get_reports_in_bundle
        expected_ids = set(get_reports_in_bundle("EXECUTIVE"))
        result_ids   = {r["report_id"] for r in result["results"]}
        assert result_ids == expected_ids

    def test_search_reports_no_dependencies_filter(self):
        result = search_reports(has_dependencies=False)
        assert result["search_healthy"] is True
        for r in result["results"]:
            assert r["dependencies"] == []

    def test_search_reports_has_dependencies_filter(self):
        result = search_reports(has_dependencies=True)
        assert result["search_healthy"] is True
        for r in result["results"]:
            assert len(r["dependencies"]) > 0

    def test_search_snapshots_no_filter(self):
        snaps  = _make_snapshots(10)
        result = search_snapshots(snaps)
        assert result["search_healthy"] is True
        assert result["result_count"] == 10

    def test_search_snapshots_by_type(self):
        snaps     = _make_snapshots(14)
        first_type = sorted(SNAPSHOT_TYPES)[0]
        result    = search_snapshots(snaps, snapshot_type=first_type)
        assert result["search_healthy"] is True
        for s in result["results"]:
            assert s["snapshot_type"] == first_type

    def test_search_snapshots_by_version(self):
        snaps  = _make_snapshots(14)
        result = search_snapshots(snaps, app_version="1.0.0")
        assert result["search_healthy"] is True
        for s in result["results"]:
            assert s["app_version"] == "1.0.0"

    def test_search_snapshots_by_triggered_by(self):
        snaps  = _make_snapshots(5)
        result = search_snapshots(snaps, triggered_by="TEST")
        assert result["search_healthy"] is True
        assert result["result_count"] == 5

    def test_search_snapshots_empty_ledger(self):
        result = search_snapshots([])
        assert result["search_healthy"] is True
        assert result["result_count"] == 0

    def test_search_bundles_no_filter(self):
        result = search_bundles()
        assert result["search_healthy"] is True
        assert result["result_count"] == len(BUNDLE_MEMBERSHIP)

    def test_search_bundles_by_name(self):
        result = search_bundles(query="EXECUTIVE")
        assert result["search_healthy"] is True
        assert result["result_count"] == 1
        assert result["results"][0]["bundle_type"] == "EXECUTIVE"

    def test_search_bundles_contains_report(self):
        result = search_bundles(contains_report="SUMMARY")
        assert result["search_healthy"] is True
        for b in result["results"]:
            assert "SUMMARY" in b["report_ids"]

    def test_search_bundles_min_report_count(self):
        result = search_bundles(min_report_count=20)
        assert result["search_healthy"] is True
        for b in result["results"]:
            assert b["report_count"] >= 20

    def test_get_search_health(self):
        result = get_search_health()
        assert result["search_healthy"] is True
        assert result["search_operational"] is True
        assert result["indexed_reports"] == EXPECTED_REPORT_COUNT


# ── TestDownloadCenterGovernance ──────────────────────────────────────────────

class TestDownloadCenterGovernance:
    def test_basic_structure(self):
        result = compute_download_center_governance()
        assert "download_center_health_score" in result
        assert "download_center_health_tier" in result
        assert "recommendations" in result
        assert "audit_entry" in result
        assert "download_hard_principles" in result

    def test_health_score_100_on_clean_system(self):
        result = compute_download_center_governance()
        assert result["download_center_health_score"] == 100.0

    def test_health_tier_healthy(self):
        result = compute_download_center_governance()
        assert result["download_center_health_tier"] == "HEALTHY"

    def test_audit_entry_prefix(self):
        result = compute_download_center_governance()
        assert result["audit_entry"]["entry_id"].startswith("UDCA-")

    def test_audit_entry_auto_authorized_false(self):
        result = compute_download_center_governance()
        assert result["audit_entry"]["auto_authorized"] is False

    def test_audit_entry_immutable(self):
        result = compute_download_center_governance()
        assert result["audit_entry"]["immutable"] is True

    def test_audit_entry_human_approval_required(self):
        result = compute_download_center_governance()
        assert result["audit_entry"]["human_approval_required"] is True

    def test_recommendations_healthy_when_all_ok(self):
        result = compute_download_center_governance()
        recs   = result["recommendations"]
        assert len(recs) == 1
        assert recs[0]["type"] == "DOWNLOAD_CENTER_HEALTHY"

    def test_all_recommendations_auto_authorized_false(self):
        result = compute_download_center_governance()
        for rec in result["recommendations"]:
            assert rec["auto_authorized"] is False

    def test_available_bundles(self):
        result = compute_download_center_governance()
        assert set(result["available_bundles"]) == set(BUNDLE_MEMBERSHIP.keys())

    def test_available_snapshot_types(self):
        result = compute_download_center_governance()
        assert set(result["available_snapshot_types"]) == SNAPSHOT_TYPES

    def test_total_reports(self):
        result = compute_download_center_governance()
        assert result["total_reports"] == EXPECTED_REPORT_COUNT

    def test_with_snapshots(self):
        snaps  = _make_snapshots(5)
        result = compute_download_center_governance(snapshots=snaps)
        assert result["download_center_health_score"] == 100.0
        assert result["snapshots_assessed"] == 5

    def test_never_raises_on_empty(self):
        result = compute_download_center_governance(snapshots=None)
        assert "download_center_health_score" in result

    def test_scope_note_present(self):
        result = compute_download_center_governance()
        assert "FTD-UDCA" in result["scope_note"]

    def test_sub_health_components_present(self):
        result = compute_download_center_governance()
        assert "archive_browser_health" in result
        assert "replay_explorer_health" in result
        assert "export_preview_health" in result
        assert "visualization_health" in result
        assert "institutional_search_health" in result


# ── TestConstitutionalPrinciples ──────────────────────────────────────────────

class TestConstitutionalPrinciples:
    def test_hard_principles_affirmative_values(self):
        affirmative = [
            "human_authority_over_archive_experience",
            "explicit_export_approval_required",
            "immutable_lineage_navigation_guaranteed",
            "all_archive_access_human_controlled",
            "replay_continuity_preserved",
            "search_index_integrity_enforced",
        ]
        for key in affirmative:
            assert DOWNLOAD_CENTER_HARD_PRINCIPLES[key] is True, key

    def test_hard_principles_prohibited_actions_false(self):
        prohibited = [
            "autonomous_archive_mutation",
            "self_authorized_snapshot_deletion",
            "autonomous_lineage_rewriting",
            "silent_manifest_alteration",
            "undocumented_export_generation",
        ]
        for key in prohibited:
            assert DOWNLOAD_CENTER_HARD_PRINCIPLES[key] is False, key

    def test_governance_result_hard_principles_match(self):
        result = compute_download_center_governance()
        assert result["download_hard_principles"] == DOWNLOAD_CENTER_HARD_PRINCIPLES

    def test_preview_bundle_auto_authorized_false(self):
        for bt in BUNDLE_MEMBERSHIP:
            result = preview_bundle(bt)
            assert result.get("auto_authorized") is False, bt

    def test_preview_manifest_auto_authorized_false(self):
        for bt in BUNDLE_MEMBERSHIP:
            result = preview_manifest(bt)
            assert result.get("auto_authorized") is False, bt

    def test_snapshot_manifest_preview_auto_authorized_false(self):
        snap = _make_snapshots(1)[0]
        result = get_snapshot_manifest_preview(snap)
        assert result["auto_authorized"] is False

    def test_snapshot_manifest_preview_immutable(self):
        snap = _make_snapshots(1)[0]
        result = get_snapshot_manifest_preview(snap)
        assert result["immutable"] is True

    def test_recommendations_never_self_authorize(self):
        result = compute_download_center_governance()
        for rec in result["recommendations"]:
            assert rec["auto_authorized"] is False


# ── TestProductionIsolation ───────────────────────────────────────────────────

class TestProductionIsolation:
    def test_compute_does_not_modify_input_snapshots(self):
        snaps    = _make_snapshots(5)
        original = [s.copy() for s in snaps]
        compute_download_center_governance(snapshots=snaps)
        for i, s in enumerate(snaps):
            assert s == original[i]

    def test_search_does_not_modify_input(self):
        snaps    = _make_snapshots(5)
        original = [s.copy() for s in snaps]
        search_snapshots(snaps, snapshot_type="HOURLY")
        for i, s in enumerate(snaps):
            assert s == original[i]

    def test_browse_does_not_modify_input(self):
        snaps    = _make_snapshots(5)
        original = [s.copy() for s in snaps]
        browse_snapshots(snaps)
        for i, s in enumerate(snaps):
            assert s == original[i]

    def test_compute_is_deterministic_structure(self):
        r1 = compute_download_center_governance()
        r2 = compute_download_center_governance()
        assert r1["download_center_health_score"] == r2["download_center_health_score"]
        assert r1["download_center_health_tier"] == r2["download_center_health_tier"]

    def test_fail_open_bad_snapshot_data(self):
        bad_snaps = [{"corrupted": True, "no_timestamp": None}] * 5
        result = compute_download_center_governance(snapshots=bad_snaps)
        assert "download_center_health_score" in result


# ── TestEdgeCases ─────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_browse_all_snapshot_types_filterable(self):
        snaps = _make_snapshots(len(SNAPSHOT_TYPES) * 2)
        for stype in SNAPSHOT_TYPES:
            result = browse_snapshots(snaps, filters={"snapshot_type": stype})
            assert result["browse_healthy"] is True

    def test_compare_snapshots_same_snapshot(self):
        snap   = _make_snapshots(1)[0]
        result = compare_snapshots(snap, snap)
        assert result["compare_healthy"] is True
        assert result["elapsed_ms"] == 0
        assert result["hash_changed"] is False
        assert result["version_changed"] is False

    def test_search_empty_query_returns_all(self):
        result = search_reports(query="")
        assert result["search_healthy"] is True
        # Empty string matches everything (empty string is in everything)
        assert result["result_count"] == EXPECTED_REPORT_COUNT

    def test_replay_lineage_all_registered_reports(self):
        for r_id in REPORT_REGISTRY:
            result = replay_lineage(r_id, [])
            assert result["replay_healthy"] is True, f"Failed for {r_id}"

    def test_dependency_graph_empty_subset(self):
        result = build_dependency_graph([])
        assert result["graph_healthy"] is True
        assert result["node_count"] == 0
        assert result["edge_count"] == 0

    def test_compare_eras_one_empty(self):
        snaps  = _make_snapshots(5)
        result = compare_eras(snaps, [], "POPULATED", "EMPTY")
        assert result["compare_healthy"] is True
        assert result["era_a"]["count"] == 5
        assert result["era_b"]["count"] == 0

    def test_search_nonexistent_bundle_returns_empty(self):
        result = search_bundles(query="NONEXISTENT_BUNDLE_XYZ")
        assert result["search_healthy"] is True
        assert result["result_count"] == 0

    def test_continuity_flow_empty_snapshots(self):
        result = build_continuity_flow([])
        assert result["graph_healthy"] is True
        assert result["node_count"] == 0
        assert result["milestone_count"] == 0

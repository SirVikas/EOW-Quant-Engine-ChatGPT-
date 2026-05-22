"""
Tests for FTD-RTAG — Constitutional Report Taxonomy Alignment
& Institutional Export Governance Layer.

Coverage:
  - core/report_registry.py     — canonical registry completeness & correctness
  - core/report_taxonomy.py     — family/tier/bundle classification queries
  - core/report_dependency_graph.py — cycle detection, dangling refs, topological sort
  - core/export_bundle_manager.py   — bundle compositions, ecosystem governance
  - core/report_metadata_schema.py  — metadata generation and validation
  - compute_report_ecosystem_governance() — structure, health, constitutional invariants
  - Production isolation, fail-open, constitutional principles
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from core.report_registry import (
    REPORT_REGISTRY,
    REGISTRY_REQUIRED_FIELDS,
    KNOWN_FAMILIES,
    KNOWN_TIERS,
    EXPECTED_REPORT_COUNT,
    FAMILY_ECONOMIC, FAMILY_COGNITIVE, FAMILY_GOVERNANCE,
    FAMILY_EPISTEMIC, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT,
    FAMILY_REPLAY, FAMILY_FORENSICS,
    TIER_CORE, TIER_RESEARCH, TIER_GOVERNANCE, TIER_EPISTEMIC,
    TIER_CONTINUITY, TIER_FORENSICS,
    PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
)
from core.report_taxonomy import (
    BUNDLE_MEMBERSHIP,
    BUNDLE_EXECUTIVE, BUNDLE_RESEARCH, BUNDLE_GOVERNANCE,
    BUNDLE_EPISTEMIC, BUNDLE_CONTINUITY, BUNDLE_MASTER_ARCHIVE,
    KNOWN_BUNDLES,
    get_reports_by_family, get_family_ids,
    get_reports_by_tier, get_tier_ids,
    get_reports_by_priority,
    get_reports_in_bundle, get_bundles_for_report,
    get_orphaned_reports, get_all_families, get_all_tiers,
    get_coverage_summary,
)
from core.report_dependency_graph import (
    get_dependencies, get_dependents, get_all_ancestors,
    get_dangling_dependencies, detect_cycles,
    topological_sort, get_overlap_map, get_high_overlap_reports,
    get_primitive_reports, get_dependency_graph_health,
)
from core.export_bundle_manager import (
    REPORTING_HARD_PRINCIPLES,
    get_bundle_composition, get_all_bundle_compositions,
    compute_report_ecosystem_governance,
)
from core.report_metadata_schema import (
    REQUIRED_METADATA_FIELDS, SCHEMA_VERSION,
    generate_metadata, validate_metadata, compliance_score,
)


# ══════════════════════════════════════════════════════════════════════════════
# TestReportRegistry
# ══════════════════════════════════════════════════════════════════════════════

class TestReportRegistry:

    def test_expected_report_count(self):
        assert len(REPORT_REGISTRY) == EXPECTED_REPORT_COUNT

    def test_all_required_fields_present_in_every_entry(self):
        for r_id, spec in REPORT_REGISTRY.items():
            for field in REGISTRY_REQUIRED_FIELDS:
                assert field in spec, f"{r_id}: missing required field '{field}'"

    def test_all_families_are_known(self):
        for r_id, spec in REPORT_REGISTRY.items():
            fam = spec.get("report_family")
            assert fam in KNOWN_FAMILIES, f"{r_id}: unknown family '{fam}'"

    def test_all_tiers_are_known(self):
        for r_id, spec in REPORT_REGISTRY.items():
            tier = spec.get("export_tier")
            assert tier in KNOWN_TIERS, f"{r_id}: unknown tier '{tier}'"

    def test_all_priorities_are_valid(self):
        valid = {PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW}
        for r_id, spec in REPORT_REGISTRY.items():
            prio = spec.get("archive_priority")
            assert prio in valid, f"{r_id}: unknown priority '{prio}'"

    def test_report_id_matches_registry_key(self):
        for r_id, spec in REPORT_REGISTRY.items():
            assert spec["report_id"] == r_id, f"report_id mismatch for key {r_id}"

    def test_all_endpoints_start_with_api(self):
        for r_id, spec in REPORT_REGISTRY.items():
            assert spec["endpoint"].startswith("/api/"), f"{r_id}: bad endpoint"

    def test_all_eight_families_represented(self):
        registered_families = {spec["report_family"] for spec in REPORT_REGISTRY.values()}
        for fam in [
            FAMILY_ECONOMIC, FAMILY_COGNITIVE, FAMILY_GOVERNANCE, FAMILY_EPISTEMIC,
            FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT, FAMILY_REPLAY, FAMILY_FORENSICS,
        ]:
            assert fam in registered_families, f"family '{fam}' not represented"

    def test_ftd_reports_registered(self):
        for ftd_id in ("CKPD", "EIOD", "HMAO"):
            assert ftd_id in REPORT_REGISTRY, f"FTD report {ftd_id} not registered"

    def test_critical_priority_reports_include_ftds(self):
        critical = [r for r, s in REPORT_REGISTRY.items()
                    if s.get("archive_priority") == PRIORITY_CRITICAL]
        for ftd in ("CKPD", "EIOD", "HMAO", "ECONOMIC_GROUND_TRUTH", "GRVL"):
            assert ftd in critical, f"{ftd} should be CRITICAL priority"

    def test_evidence_requirements_is_dict(self):
        for r_id, spec in REPORT_REGISTRY.items():
            assert isinstance(spec.get("evidence_requirements"), dict), \
                f"{r_id}: evidence_requirements must be dict"

    def test_dependencies_is_list(self):
        for r_id, spec in REPORT_REGISTRY.items():
            assert isinstance(spec.get("dependencies"), list), \
                f"{r_id}: dependencies must be list"

    def test_overlapping_reports_is_list(self):
        for r_id, spec in REPORT_REGISTRY.items():
            assert isinstance(spec.get("overlapping_reports"), list), \
                f"{r_id}: overlapping_reports must be list"


# ══════════════════════════════════════════════════════════════════════════════
# TestReportTaxonomy
# ══════════════════════════════════════════════════════════════════════════════

class TestReportTaxonomy:

    def test_get_reports_by_family_economic(self):
        reports = get_reports_by_family(FAMILY_ECONOMIC)
        assert len(reports) >= 5
        assert all(r["report_family"] == FAMILY_ECONOMIC for r in reports)

    def test_get_reports_by_family_epistemic_is_eiod(self):
        ids = get_family_ids(FAMILY_EPISTEMIC)
        assert "EIOD" in ids

    def test_get_reports_by_family_human_alignment_is_hmao(self):
        ids = get_family_ids(FAMILY_HUMAN_ALIGNMENT)
        assert "HMAO" in ids

    def test_get_reports_by_tier_core(self):
        ids = get_tier_ids(TIER_CORE)
        assert len(ids) >= 3
        assert "SUMMARY" in ids
        assert "ECONOMIC_GROUND_TRUTH" in ids

    def test_get_reports_by_tier_continuity(self):
        ids = get_tier_ids(TIER_CONTINUITY)
        assert "CKPD" in ids
        assert "LHEO" in ids

    def test_get_reports_in_bundle_executive(self):
        members = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        assert "SUMMARY" in members
        assert "ECONOMIC_GROUND_TRUTH" in members
        assert "GRVL" in members

    def test_get_reports_in_bundle_governance(self):
        members = get_reports_in_bundle(BUNDLE_GOVERNANCE)
        for r in ("GAGS", "GADD", "GRVL", "GMPD", "CKPD", "LHEO", "HMAO"):
            assert r in members

    def test_master_archive_contains_all_reports(self):
        members = set(get_reports_in_bundle(BUNDLE_MASTER_ARCHIVE))
        assert members == set(REPORT_REGISTRY.keys())

    def test_get_bundles_for_report_ckpd(self):
        bundles = get_bundles_for_report("CKPD")
        assert BUNDLE_GOVERNANCE in bundles
        assert BUNDLE_CONTINUITY in bundles
        assert BUNDLE_MASTER_ARCHIVE in bundles

    def test_no_orphaned_reports(self):
        orphans = get_orphaned_reports()
        assert orphans == [], f"Orphaned reports found: {orphans}"

    def test_all_families_present_in_taxonomy(self):
        fams = get_all_families()
        assert len(fams) == len(KNOWN_FAMILIES)

    def test_all_tiers_present_in_taxonomy(self):
        tiers = get_all_tiers()
        assert len(tiers) == len(KNOWN_TIERS)

    def test_coverage_summary_structure(self):
        cov = get_coverage_summary()
        assert "total_reports" in cov
        assert "family_breakdown" in cov
        assert "tier_breakdown" in cov
        assert "bundle_breakdown" in cov
        assert "orphaned_reports" in cov
        assert cov["total_reports"] == EXPECTED_REPORT_COUNT

    def test_coverage_summary_orphaned_is_empty(self):
        cov = get_coverage_summary()
        assert cov["orphaned_count"] == 0

    def test_known_bundles_all_defined(self):
        for b in KNOWN_BUNDLES:
            assert b in BUNDLE_MEMBERSHIP, f"Bundle {b} not in BUNDLE_MEMBERSHIP"


# ══════════════════════════════════════════════════════════════════════════════
# TestReportDependencyGraph
# ══════════════════════════════════════════════════════════════════════════════

class TestReportDependencyGraph:

    def test_no_cycle_in_registry(self):
        assert detect_cycles() is False

    def test_no_dangling_dependencies(self):
        dangling = get_dangling_dependencies()
        assert dangling == [], f"Dangling dependencies: {dangling}"

    def test_topological_sort_returns_all_reports(self):
        topo = topological_sort()
        assert len(topo) == EXPECTED_REPORT_COUNT
        assert set(topo) == set(REPORT_REGISTRY.keys())

    def test_topological_sort_primitives_first(self):
        topo = topological_sort()
        prims = set(get_primitive_reports())
        # All primitives should appear before their dependents
        for prim in prims:
            prim_idx = topo.index(prim)
            for dep_on_prim in get_dependents(prim):
                if dep_on_prim in topo:
                    assert prim_idx < topo.index(dep_on_prim), \
                        f"{prim} should appear before {dep_on_prim}"

    def test_primitive_reports_have_no_dependencies(self):
        prims = get_primitive_reports()
        for r_id in prims:
            deps = get_dependencies(r_id)
            # deps list may reference other reports not in registry...
            # Actually in our registry, primitives are those with [] deps
            assert REPORT_REGISTRY[r_id].get("dependencies", []) == []

    def test_summary_is_primitive(self):
        assert "SUMMARY" in get_primitive_reports()

    def test_economic_ground_truth_is_primitive(self):
        assert "ECONOMIC_GROUND_TRUTH" in get_primitive_reports()

    def test_ckpd_is_primitive(self):
        assert "CKPD" in get_primitive_reports()

    def test_get_dependents_summary(self):
        # SUMMARY is depended on by many reports
        deps = get_dependents("SUMMARY")
        assert len(deps) >= 4
        assert "PATTERNS" in deps
        assert "ECOLOGY" in deps

    def test_get_all_ancestors_hmao_includes_eiod(self):
        ancestors = get_all_ancestors("HMAO")
        assert "EIOD" in ancestors
        assert "EXPLORATION_DIAGNOSTICS" in ancestors
        assert "SUMMARY" in ancestors

    def test_get_overlap_map_all_reports_present(self):
        ov = get_overlap_map()
        assert set(ov.keys()) == set(REPORT_REGISTRY.keys())

    def test_dependency_graph_health_structure(self):
        h = get_dependency_graph_health()
        assert "cycle_free" in h
        assert "dangling_count" in h
        assert "topological_order" in h
        assert "primitive_reports" in h
        assert "graph_healthy" in h

    def test_dependency_graph_is_healthy(self):
        h = get_dependency_graph_health()
        assert h["cycle_free"] is True
        assert h["dangling_count"] == 0
        assert h["graph_healthy"] is True


# ══════════════════════════════════════════════════════════════════════════════
# TestExportBundleManager
# ══════════════════════════════════════════════════════════════════════════════

class TestExportBundleManager:

    def test_get_bundle_composition_structure(self):
        comp = get_bundle_composition(BUNDLE_EXECUTIVE)
        assert "bundle_name" in comp
        assert "report_count" in comp
        assert "report_ids" in comp
        assert "families" in comp
        assert "tiers" in comp
        assert "critical_count" in comp

    def test_master_archive_composition_has_all_reports(self):
        comp = get_bundle_composition(BUNDLE_MASTER_ARCHIVE)
        assert comp["report_count"] == EXPECTED_REPORT_COUNT

    def test_get_all_bundle_compositions_has_six_bundles(self):
        all_b = get_all_bundle_compositions()
        assert len(all_b) == len(KNOWN_BUNDLES)

    def test_governance_bundle_has_ftd_reports(self):
        comp = get_bundle_composition(BUNDLE_GOVERNANCE)
        for r in ("CKPD", "HMAO", "GAGS", "GADD"):
            assert r in comp["report_ids"]
        # EIOD lives in EPISTEMIC bundle, not GOVERNANCE
        assert "EIOD" not in comp["report_ids"]

    def test_epistemic_bundle_has_eiod(self):
        comp = get_bundle_composition(BUNDLE_EPISTEMIC)
        assert "EIOD" in comp["report_ids"]

    def test_continuity_bundle_has_ckpd_lheo_hmao(self):
        comp = get_bundle_composition(BUNDLE_CONTINUITY)
        for r in ("CKPD", "LHEO", "HMAO"):
            assert r in comp["report_ids"]

    def test_reporting_hard_principles_immutable(self):
        assert REPORTING_HARD_PRINCIPLES["human_authority_over_reporting_governance"] is True
        assert REPORTING_HARD_PRINCIPLES["autonomous_lineage_mutation"] is False
        assert REPORTING_HARD_PRINCIPLES["self_authorized_export"] is False
        assert REPORTING_HARD_PRINCIPLES["autonomous_archive_rewriting"] is False

    def test_reporting_principles_count(self):
        assert len(REPORTING_HARD_PRINCIPLES) >= 10
        true_count  = sum(1 for v in REPORTING_HARD_PRINCIPLES.values() if v is True)
        false_count = sum(1 for v in REPORTING_HARD_PRINCIPLES.values() if v is False)
        assert true_count >= 5
        assert false_count >= 5


# ══════════════════════════════════════════════════════════════════════════════
# TestReportMetadataSchema
# ══════════════════════════════════════════════════════════════════════════════

class TestReportMetadataSchema:

    def test_schema_version_is_string(self):
        assert isinstance(SCHEMA_VERSION, str)
        assert len(SCHEMA_VERSION) > 0

    def test_required_fields_count(self):
        assert len(REQUIRED_METADATA_FIELDS) >= 10

    def test_generate_metadata_returns_all_required_fields(self):
        meta = generate_metadata(
            report_id="EIOD",
            report_family="EPISTEMIC",
            app_version="1.24.0",
            doctrine_version="1.22",
            trade_count=100,
        )
        for field in REQUIRED_METADATA_FIELDS:
            assert field in meta, f"generated metadata missing '{field}'"

    def test_generate_metadata_report_id_correct(self):
        meta = generate_metadata("CKPD", "CONTINUITY", "1.24.0", "1.21", 50)
        assert meta["report_id"] == "CKPD"
        assert meta["report_family"] == "CONTINUITY"

    def test_generate_metadata_reconstruction_hash_is_hex(self):
        meta = generate_metadata("HMAO", "HUMAN_ALIGNMENT", "1.24.0", "1.23", 80)
        h = meta["reconstruction_hash"]
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_generate_metadata_replay_lineage_id_autogenerated(self):
        meta = generate_metadata("SUMMARY", "ECONOMIC", "1.24.0", "1.0", 0)
        assert meta["replay_lineage_id"].startswith("RPL-")

    def test_generate_metadata_custom_bundle_type(self):
        meta = generate_metadata(
            "EIOD", "EPISTEMIC", "1.24.0", "1.22", 100,
            export_bundle_type="EPISTEMIC"
        )
        assert meta["export_bundle_type"] == "EPISTEMIC"

    def test_validate_metadata_valid(self):
        meta = generate_metadata("GRVL", "GOVERNANCE", "1.24.0", "1.0", 0)
        is_valid, missing = validate_metadata(meta)
        assert is_valid is True
        assert missing == []

    def test_validate_metadata_missing_fields(self):
        meta = {"report_id": "X", "report_family": "Y"}
        is_valid, missing = validate_metadata(meta)
        assert is_valid is False
        assert len(missing) > 0
        assert "reconstruction_hash" in missing

    def test_validate_metadata_non_dict_returns_invalid(self):
        is_valid, missing = validate_metadata("not a dict")
        assert is_valid is False
        assert len(missing) == len(REQUIRED_METADATA_FIELDS)

    def test_compliance_score_full_metadata(self):
        meta = generate_metadata("SUMMARY", "ECONOMIC", "1.24.0", "1.0", 0)
        score = compliance_score(meta)
        assert score == 100.0

    def test_compliance_score_empty_dict(self):
        assert compliance_score({}) == 0.0

    def test_compliance_score_partial(self):
        meta = {"report_id": "X", "report_family": "Y"}
        score = compliance_score(meta)
        assert 0.0 < score < 100.0


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeEcosystemGovernance
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeEcosystemGovernance:

    _REQUIRED_KEYS = [
        "scope_note", "total_reports_registered", "ecosystem_health_score",
        "ecosystem_health_tier", "registry_health", "dependency_health",
        "bundle_coverage", "overlap_risk", "metadata_compliance",
        "archive_survivability", "coverage_summary", "bundle_compositions",
        "recommendations", "reporting_hard_principles", "audit_entry",
    ]

    def test_all_required_keys_present(self):
        result = compute_report_ecosystem_governance()
        for k in self._REQUIRED_KEYS:
            assert k in result, f"missing key: {k}"

    def test_scope_note_contains_ftd_rtag(self):
        result = compute_report_ecosystem_governance()
        assert "FTD-RTAG" in result["scope_note"]

    def test_total_reports_matches_registry(self):
        result = compute_report_ecosystem_governance()
        assert result["total_reports_registered"] == EXPECTED_REPORT_COUNT

    def test_ecosystem_health_score_high_for_clean_registry(self):
        result = compute_report_ecosystem_governance()
        # Registry is designed to be clean — should score well
        assert result["ecosystem_health_score"] >= 80.0

    def test_ecosystem_health_tier_healthy(self):
        result = compute_report_ecosystem_governance()
        assert result["ecosystem_health_tier"] in ("HEALTHY", "ADEQUATE")

    def test_registry_health_reports_healthy(self):
        result = compute_report_ecosystem_governance()
        rh = result["registry_health"]
        assert rh["registry_healthy"] is True
        assert rh["violations_count"] == 0

    def test_dependency_health_cycle_free(self):
        result = compute_report_ecosystem_governance()
        dh = result["dependency_health"]
        assert dh["cycle_free"] is True
        assert dh["dangling_count"] == 0
        assert dh["graph_healthy"] is True

    def test_bundle_coverage_no_orphans(self):
        result = compute_report_ecosystem_governance()
        bc = result["bundle_coverage"]
        assert bc["orphaned_count"] == 0
        assert bc["coverage_healthy"] is True

    def test_all_recommendations_not_auto_authorized(self):
        result = compute_report_ecosystem_governance()
        for rec in result["recommendations"]:
            assert rec["auto_authorized"] is False, "Recommendation auto_authorized must be False"

    def test_audit_entry_structure(self):
        result = compute_report_ecosystem_governance()
        ae = result["audit_entry"]
        assert ae["entry_id"].startswith("RTAG-")
        assert ae["auto_authorized"] is False
        assert ae["immutable"] is True
        assert ae["entry_type"] == "GOVERNANCE_ASSESSMENT"

    def test_reporting_hard_principles_present(self):
        result = compute_report_ecosystem_governance()
        hp = result["reporting_hard_principles"]
        assert hp["human_authority_over_reporting_governance"] is True
        assert hp["autonomous_lineage_mutation"] is False

    def test_bundle_compositions_has_all_bundles(self):
        result = compute_report_ecosystem_governance()
        bc = result["bundle_compositions"]
        for bundle in KNOWN_BUNDLES:
            assert bundle in bc, f"bundle_compositions missing {bundle}"

    def test_never_raises(self):
        result = compute_report_ecosystem_governance()
        assert isinstance(result, dict)

    def test_metadata_compliance_schema_defined(self):
        result = compute_report_ecosystem_governance()
        mc = result["metadata_compliance"]
        assert mc["compliance_schema_defined"] is True
        assert mc["required_field_count"] == len(REQUIRED_METADATA_FIELDS)

    def test_archive_survivability_strong(self):
        result = compute_report_ecosystem_governance()
        ar = result["archive_survivability"]
        assert ar["survivability_tier"] in ("STRONG", "ADEQUATE")
        assert ar["high_priority_count"] >= 10


# ══════════════════════════════════════════════════════════════════════════════
# TestConstitutionalPrinciples
# ══════════════════════════════════════════════════════════════════════════════

class TestConstitutionalPrinciples:

    def test_human_authority_true(self):
        assert REPORTING_HARD_PRINCIPLES["human_authority_over_reporting_governance"] is True

    def test_explicit_archive_approval_true(self):
        assert REPORTING_HARD_PRINCIPLES["explicit_archive_approval_required"] is True

    def test_immutable_lineage_true(self):
        assert REPORTING_HARD_PRINCIPLES["immutable_lineage_guaranteed"] is True

    def test_all_exports_human_controlled_true(self):
        assert REPORTING_HARD_PRINCIPLES["all_exports_human_controlled"] is True

    def test_audit_continuity_preserved_true(self):
        assert REPORTING_HARD_PRINCIPLES["audit_continuity_preserved"] is True

    def test_autonomous_lineage_mutation_false(self):
        assert REPORTING_HARD_PRINCIPLES["autonomous_lineage_mutation"] is False

    def test_self_authorized_export_false(self):
        assert REPORTING_HARD_PRINCIPLES["self_authorized_export"] is False

    def test_autonomous_archive_rewriting_false(self):
        assert REPORTING_HARD_PRINCIPLES["autonomous_archive_rewriting"] is False

    def test_undocumented_proliferation_false(self):
        assert REPORTING_HARD_PRINCIPLES["undocumented_report_proliferation"] is False

    def test_autonomous_governance_modification_false(self):
        assert REPORTING_HARD_PRINCIPLES["autonomous_governance_modification"] is False

    def test_principles_in_compute_output(self):
        result = compute_report_ecosystem_governance()
        hp = result["reporting_hard_principles"]
        assert hp == REPORTING_HARD_PRINCIPLES


# ══════════════════════════════════════════════════════════════════════════════
# TestProductionIsolation
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionIsolation:

    def test_registry_has_no_live_engine_imports(self):
        import core.report_registry as mod
        import sys
        for attr in dir(mod):
            assert "pnl_calc" not in attr.lower()
            assert "data_lake" not in attr.lower()

    def test_compute_returns_new_dict_each_call(self):
        r1 = compute_report_ecosystem_governance()
        r2 = compute_report_ecosystem_governance()
        assert r1 is not r2

    def test_compute_is_deterministic_on_keys(self):
        r1 = compute_report_ecosystem_governance()
        r2 = compute_report_ecosystem_governance()
        assert set(r1.keys()) == set(r2.keys())

    def test_fail_open_returns_dict(self):
        # Even if something goes wrong, result is dict
        result = compute_report_ecosystem_governance()
        assert isinstance(result, dict)

    def test_no_side_effects_on_report_registry(self):
        original_keys = set(REPORT_REGISTRY.keys())
        compute_report_ecosystem_governance()
        assert set(REPORT_REGISTRY.keys()) == original_keys


# ══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_get_bundle_composition_unknown_bundle(self):
        comp = get_bundle_composition("NONEXISTENT_BUNDLE")
        assert comp["report_count"] == 0
        assert comp["report_ids"] == []

    def test_get_reports_in_bundle_unknown(self):
        members = get_reports_in_bundle("UNKNOWN")
        assert members == []

    def test_get_bundles_for_unknown_report(self):
        bundles = get_bundles_for_report("NONEXISTENT_REPORT")
        assert bundles == []

    def test_get_dependencies_unknown_report(self):
        deps = get_dependencies("NONEXISTENT")
        assert deps == []

    def test_get_dependents_unknown_report(self):
        deps = get_dependents("NONEXISTENT")
        assert deps == []

    def test_get_reports_by_family_unknown(self):
        reports = get_reports_by_family("UNKNOWN_FAMILY")
        assert reports == []

    def test_get_reports_by_tier_unknown(self):
        reports = get_reports_by_tier("UNKNOWN_TIER")
        assert reports == []

    def test_compliance_score_non_dict(self):
        assert compliance_score(None) == 0.0
        assert compliance_score("str") == 0.0
        assert compliance_score([]) == 0.0

    def test_validate_metadata_none(self):
        is_valid, missing = validate_metadata(None)
        assert is_valid is False

    def test_get_all_ancestors_primitive_is_empty(self):
        ancestors = get_all_ancestors("SUMMARY")
        # SUMMARY has no dependencies → no ancestors
        assert ancestors == set()

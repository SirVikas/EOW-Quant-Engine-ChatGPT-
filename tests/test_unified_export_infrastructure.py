"""
Tests for FTD-UEI — Unified Institutional Export & Download Infrastructure.

Coverage:
  - core/reconstruction_hashing.py  — hash primitives, bundle/manifest verification
  - core/export_manifest.py         — manifest generation and validation
  - core/snapshot_manager.py        — snapshot records, health analysis
  - core/export_composer.py         — bundle composition and ordering
  - core/archive_integrity.py       — integrity verification, corruption detection
  - core/download_center.py         — governance function, hard principles
  - compute_export_infrastructure_governance() — structure, health, constitutional invariants
  - Production isolation, fail-open behavior, constitutional constraints
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from core.reconstruction_hashing import (
    content_hash, dict_hash, bundle_hash, manifest_hash,
    lineage_hash, snapshot_hash, validate_hash, is_valid_sha256,
    verify_bundle_hash, verify_manifest_hash,
)
from core.export_manifest import generate_manifest, validate_manifest
from core.snapshot_manager import (
    SNAPSHOT_TYPES, SNAPSHOT_TYPE_DESCRIPTIONS,
    validate_snapshot_type, create_snapshot_record,
    get_snapshot_health, get_latest_snapshot, get_snapshots_by_type,
)
from core.export_composer import (
    EXPORT_METADATA_REQUIRED_FIELDS,
    compose_bundle, compose_all_bundles, get_composer_health,
)
from core.archive_integrity import (
    verify_bundle_integrity, verify_manifest_integrity,
    detect_corruption, assess_bundle_health, assess_archive_health,
)
from core.download_center import (
    EXPORT_HARD_PRINCIPLES,
    compute_export_infrastructure_governance,
)
from core.report_taxonomy import (
    BUNDLE_EXECUTIVE, BUNDLE_RESEARCH, BUNDLE_GOVERNANCE,
    BUNDLE_EPISTEMIC, BUNDLE_CONTINUITY, BUNDLE_MASTER_ARCHIVE,
    KNOWN_BUNDLES, get_reports_in_bundle,
)
from core.report_registry import REPORT_REGISTRY, EXPECTED_REPORT_COUNT


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_snapshot(i: int = 0, **kw) -> dict:
    base = {"snapshot_type": "MILESTONE", "app_version": "1.25.0",
            "trade_count": 50 + i}
    base.update(kw)
    return create_snapshot_record(**base)


def _make_composed_bundle(bundle_type: str = BUNDLE_EXECUTIVE) -> dict:
    return compose_bundle(bundle_type, app_version="1.25.0", doctrine_version="1.0")


# ══════════════════════════════════════════════════════════════════════════════
# TestReconstructionHashing
# ══════════════════════════════════════════════════════════════════════════════

class TestReconstructionHashing:

    def test_content_hash_returns_64_char_hex(self):
        h = content_hash("hello world")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_content_hash_deterministic(self):
        assert content_hash("test") == content_hash("test")

    def test_dict_hash_deterministic(self):
        d = {"a": 1, "b": 2, "c": [3, 4]}
        assert dict_hash(d) == dict_hash(d)

    def test_dict_hash_different_dicts_differ(self):
        assert dict_hash({"a": 1}) != dict_hash({"a": 2})

    def test_bundle_hash_order_insensitive(self):
        h1 = bundle_hash("EXECUTIVE", ["A", "B", "C"], 1_000_000)
        h2 = bundle_hash("EXECUTIVE", ["C", "B", "A"], 1_000_000)
        assert h1 == h2

    def test_bundle_hash_deterministic(self):
        h1 = bundle_hash("RESEARCH", ["X", "Y"], 999_000)
        h2 = bundle_hash("RESEARCH", ["X", "Y"], 999_000)
        assert h1 == h2

    def test_bundle_hash_different_types_differ(self):
        h1 = bundle_hash("EXECUTIVE", ["A"], 1_000)
        h2 = bundle_hash("RESEARCH", ["A"], 1_000)
        assert h1 != h2

    def test_manifest_hash_is_valid_sha256(self):
        h = manifest_hash({"bundle_type": "TEST", "report_ids": ["A"]})
        assert is_valid_sha256(h)

    def test_lineage_hash_deterministic(self):
        h1 = lineage_hash("EIOD", "1.24.0", 12345)
        h2 = lineage_hash("EIOD", "1.24.0", 12345)
        assert h1 == h2

    def test_validate_hash_correct(self):
        h = content_hash("phoenix")
        assert validate_hash(h, h) is True

    def test_validate_hash_mismatch(self):
        assert validate_hash("abc", "def") is False

    def test_validate_hash_empty(self):
        assert validate_hash("", "abc") is False

    def test_is_valid_sha256_valid(self):
        assert is_valid_sha256("a" * 64) is True

    def test_is_valid_sha256_wrong_length(self):
        assert is_valid_sha256("a" * 32) is False

    def test_is_valid_sha256_non_hex(self):
        assert is_valid_sha256("g" * 64) is False

    def test_verify_bundle_hash_valid_bundle(self):
        bundle = _make_composed_bundle()
        result = verify_bundle_hash(bundle)
        assert result["valid"] is True
        assert result["reason"] == "ok"

    def test_verify_bundle_hash_tampered(self):
        bundle = _make_composed_bundle()
        bundle["metadata"]["reconstruction_hash"] = "a" * 64  # wrong
        result = verify_bundle_hash(bundle)
        assert result["valid"] is False


# ══════════════════════════════════════════════════════════════════════════════
# TestExportManifest
# ══════════════════════════════════════════════════════════════════════════════

class TestExportManifest:

    def _meta(self):
        return {"app_version": "1.25.0", "doctrine_version": "1.0",
                "lineage_epoch": "CURRENT", "export_bundle_type": BUNDLE_EXECUTIVE}

    def test_generate_manifest_required_keys(self):
        ids = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        m = generate_manifest(BUNDLE_EXECUTIVE, ids, self._meta())
        for f in ("manifest_id", "manifest_hash", "bundle_type", "generation_ts",
                  "report_ids", "export_order", "lineage_graph", "dependency_map",
                  "bundle_topology", "auto_authorized", "immutable"):
            assert f in m, f"manifest missing '{f}'"

    def test_manifest_id_starts_with_mnf(self):
        ids = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        m = generate_manifest(BUNDLE_EXECUTIVE, ids, self._meta())
        assert m["manifest_id"].startswith("MNF-")

    def test_manifest_hash_is_valid_sha256(self):
        ids = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        m = generate_manifest(BUNDLE_EXECUTIVE, ids, self._meta())
        assert is_valid_sha256(m["manifest_hash"])

    def test_auto_authorized_false(self):
        ids = get_reports_in_bundle(BUNDLE_GOVERNANCE)
        m = generate_manifest(BUNDLE_GOVERNANCE, ids, self._meta())
        assert m["auto_authorized"] is False

    def test_immutable_true(self):
        ids = get_reports_in_bundle(BUNDLE_CONTINUITY)
        m = generate_manifest(BUNDLE_CONTINUITY, ids, self._meta())
        assert m["immutable"] is True

    def test_export_order_contains_all_report_ids(self):
        ids = get_reports_in_bundle(BUNDLE_RESEARCH)
        m = generate_manifest(BUNDLE_RESEARCH, ids, self._meta())
        assert set(m["export_order"]) == set(ids)

    def test_lineage_graph_keys_are_subset_of_report_ids(self):
        ids = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        m = generate_manifest(BUNDLE_EXECUTIVE, ids, self._meta())
        for r_id in m["lineage_graph"]:
            assert r_id in ids

    def test_bundle_topology_primitives_and_dependents(self):
        ids = get_reports_in_bundle(BUNDLE_MASTER_ARCHIVE)
        m = generate_manifest(BUNDLE_MASTER_ARCHIVE, ids, self._meta())
        topo = m["bundle_topology"]
        assert "primitives" in topo
        assert "dependents" in topo

    def test_validate_manifest_valid(self):
        ids = get_reports_in_bundle(BUNDLE_EPISTEMIC)
        m = generate_manifest(BUNDLE_EPISTEMIC, ids, self._meta())
        is_valid, issues = validate_manifest(m)
        assert is_valid is True
        assert issues == []

    def test_validate_manifest_missing_field(self):
        m = {"manifest_id": "X", "bundle_type": "Y"}
        is_valid, issues = validate_manifest(m)
        assert is_valid is False
        assert len(issues) > 0

    def test_generation_ts_can_be_overridden(self):
        ids = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        ts  = 9_999_000_000_000
        m = generate_manifest(BUNDLE_EXECUTIVE, ids, self._meta(), generation_ts=ts)
        assert m["generation_ts"] == ts


# ══════════════════════════════════════════════════════════════════════════════
# TestSnapshotManager
# ══════════════════════════════════════════════════════════════════════════════

class TestSnapshotManager:

    def test_known_snapshot_types_count(self):
        assert len(SNAPSHOT_TYPES) == 7

    def test_validate_snapshot_type_known(self):
        assert validate_snapshot_type("HOURLY") == "HOURLY"
        assert validate_snapshot_type("CATASTROPHIC_EVENT") == "CATASTROPHIC_EVENT"

    def test_validate_snapshot_type_unknown_returns_milestone(self):
        assert validate_snapshot_type("BANANA") == "MILESTONE"

    def test_create_snapshot_record_required_keys(self):
        snap = create_snapshot_record("HOURLY", "1.25.0", 100)
        for f in ("snapshot_id", "snapshot_type", "timestamp_ms", "app_version",
                  "trade_count", "reconstruction_hash", "auto_authorized", "immutable"):
            assert f in snap, f"missing '{f}'"

    def test_snapshot_id_format(self):
        snap = create_snapshot_record("DAILY", "1.25.0", 50)
        assert snap["snapshot_id"].startswith("SNP-DAIL-")

    def test_auto_authorized_false(self):
        snap = create_snapshot_record("MILESTONE", "1.25.0", 0)
        assert snap["auto_authorized"] is False

    def test_immutable_true(self):
        snap = create_snapshot_record("VERSION_TRANSITION", "1.25.0", 200)
        assert snap["immutable"] is True

    def test_reconstruction_hash_valid(self):
        snap = create_snapshot_record("EPISTEMIC_SHIFT", "1.25.0", 75)
        assert is_valid_sha256(snap["reconstruction_hash"])

    def test_lineage_preserved_true(self):
        snap = create_snapshot_record("GOVERNANCE_TRANSITION", "1.25.0", 30)
        assert snap["lineage_preserved"] is True

    def test_get_snapshot_health_empty(self):
        h = get_snapshot_health([])
        assert h["total_snapshots"] == 0
        assert h["lineage_healthy"] is True

    def test_get_snapshot_health_with_snapshots(self):
        snaps = [_make_snapshot(i) for i in range(3)]
        h = get_snapshot_health(snaps)
        assert h["total_snapshots"] == 3
        assert "MILESTONE" in h["snapshot_by_type"]

    def test_get_latest_snapshot(self):
        snaps = [_make_snapshot(i) for i in range(3)]
        latest = get_latest_snapshot(snaps)
        assert latest == snaps[-1]

    def test_get_latest_snapshot_empty(self):
        assert get_latest_snapshot([]) is None

    def test_get_snapshots_by_type(self):
        snaps = [
            create_snapshot_record("HOURLY", "1.25.0", 10),
            create_snapshot_record("DAILY",  "1.25.0", 20),
            create_snapshot_record("HOURLY", "1.25.0", 30),
        ]
        hourly = get_snapshots_by_type(snaps, "HOURLY")
        assert len(hourly) == 2

    def test_snapshot_type_descriptions_all_defined(self):
        for t in SNAPSHOT_TYPES:
            assert t in SNAPSHOT_TYPE_DESCRIPTIONS, f"no description for {t}"


# ══════════════════════════════════════════════════════════════════════════════
# TestExportComposer
# ══════════════════════════════════════════════════════════════════════════════

class TestExportComposer:

    def test_export_metadata_required_fields_count(self):
        assert len(EXPORT_METADATA_REQUIRED_FIELDS) == 10

    def test_compose_bundle_required_keys(self):
        bundle = _make_composed_bundle(BUNDLE_EXECUTIVE)
        for f in ("export_id", "bundle_type", "generation_ts", "report_count",
                  "report_ids", "export_order", "report_descriptors",
                  "metadata", "manifest", "auto_authorized", "immutable"):
            assert f in bundle, f"missing '{f}'"

    def test_compose_bundle_export_id_format(self):
        bundle = _make_composed_bundle()
        assert bundle["export_id"].startswith("EXP-EXECUTIVE-")

    def test_compose_bundle_auto_authorized_false(self):
        bundle = _make_composed_bundle(BUNDLE_GOVERNANCE)
        assert bundle["auto_authorized"] is False

    def test_compose_bundle_immutable_true(self):
        bundle = _make_composed_bundle(BUNDLE_CONTINUITY)
        assert bundle["immutable"] is True

    def test_compose_bundle_report_count_matches(self):
        bundle = _make_composed_bundle(BUNDLE_EXECUTIVE)
        assert bundle["report_count"] == len(bundle["report_ids"])

    def test_compose_bundle_metadata_has_required_fields(self):
        bundle = _make_composed_bundle()
        meta = bundle["metadata"]
        for f in EXPORT_METADATA_REQUIRED_FIELDS:
            assert f in meta, f"metadata missing '{f}'"

    def test_compose_bundle_reconstruction_hash_valid(self):
        bundle = _make_composed_bundle()
        h = bundle["metadata"]["reconstruction_hash"]
        assert is_valid_sha256(h)

    def test_compose_bundle_export_order_is_subset_of_report_ids(self):
        bundle = _make_composed_bundle(BUNDLE_RESEARCH)
        assert set(bundle["export_order"]).issubset(set(bundle["report_ids"]))

    def test_compose_bundle_manifest_present(self):
        bundle = _make_composed_bundle()
        assert "manifest" in bundle
        assert bundle["manifest"]["bundle_type"] == BUNDLE_EXECUTIVE

    def test_compose_bundle_dependency_version_map(self):
        bundle = _make_composed_bundle(BUNDLE_EPISTEMIC)
        dvm = bundle["metadata"]["dependency_version_map"]
        assert isinstance(dvm, dict)
        assert len(dvm) == bundle["report_count"]

    def test_compose_bundle_unknown_type_returns_error(self):
        bundle = compose_bundle("NONEXISTENT_BUNDLE")
        assert "error" in bundle
        assert bundle["auto_authorized"] is False

    def test_compose_all_bundles_returns_six(self):
        all_b = compose_all_bundles()
        assert len(all_b) == len(KNOWN_BUNDLES)

    def test_compose_all_bundles_no_errors(self):
        all_b = compose_all_bundles("1.25.0")
        for bundle_type, bundle in all_b.items():
            assert "error" not in bundle, f"{bundle_type} composition failed"

    def test_composer_health_healthy(self):
        h = get_composer_health()
        assert h["composer_healthy"] is True
        assert h["bundle_count"] == len(KNOWN_BUNDLES)
        assert h["failed_bundles"] == []

    def test_master_archive_has_all_reports(self):
        bundle = compose_bundle(BUNDLE_MASTER_ARCHIVE, app_version="1.25.0")
        assert bundle["report_count"] == EXPECTED_REPORT_COUNT


# ══════════════════════════════════════════════════════════════════════════════
# TestArchiveIntegrity
# ══════════════════════════════════════════════════════════════════════════════

class TestArchiveIntegrity:

    def test_verify_bundle_integrity_valid_bundle(self):
        bundle = _make_composed_bundle()
        result = verify_bundle_integrity(bundle)
        assert result["valid"] is True
        assert result["issues"] == []

    def test_verify_bundle_integrity_tampered_hash(self):
        bundle = _make_composed_bundle()
        bundle["metadata"]["reconstruction_hash"] = "f" * 64
        result = verify_bundle_integrity(bundle)
        assert result["valid"] is False
        assert result["issue_count"] > 0

    def test_verify_bundle_integrity_missing_manifest(self):
        bundle = _make_composed_bundle()
        del bundle["manifest"]
        result = verify_bundle_integrity(bundle)
        assert result["valid"] is False

    def test_verify_bundle_integrity_auto_authorized_violation(self):
        bundle = _make_composed_bundle()
        bundle["auto_authorized"] = True
        result = verify_bundle_integrity(bundle)
        assert result["valid"] is False

    def test_verify_manifest_integrity_valid(self):
        bundle = _make_composed_bundle()
        result = verify_manifest_integrity(bundle["manifest"])
        assert result["valid"] is True

    def test_verify_manifest_integrity_missing_field(self):
        m = {"manifest_id": "X"}
        result = verify_manifest_integrity(m)
        assert result["valid"] is False
        assert result["issue_count"] > 0

    def test_detect_corruption_clean_bundle(self):
        bundle = _make_composed_bundle()
        signals = detect_corruption(bundle)
        assert signals == []

    def test_detect_corruption_auto_authorized_violation(self):
        bundle = _make_composed_bundle()
        bundle["auto_authorized"] = True
        signals = detect_corruption(bundle)
        assert any("auto_authorized" in s for s in signals)

    def test_assess_bundle_health_healthy(self):
        bundle = _make_composed_bundle()
        h = assess_bundle_health(bundle)
        assert h["healthy"] is True
        assert h["integrity_valid"] is True
        assert h["corruption_signals"] == []

    def test_assess_archive_health_all_healthy(self):
        bundles = [_make_composed_bundle(b) for b in [BUNDLE_EXECUTIVE, BUNDLE_RESEARCH]]
        h = assess_archive_health(bundles)
        assert h["archive_healthy"] is True
        assert h["corruption_detected"] is False

    def test_assess_archive_health_empty(self):
        h = assess_archive_health([])
        assert h["total_bundles"] == 0
        assert h["archive_healthy"] is True


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeExportInfrastructureGovernance
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeExportInfrastructureGovernance:

    _REQUIRED_KEYS = [
        "scope_note", "infrastructure_health_score", "infrastructure_health_tier",
        "bundle_composer_health", "manifest_generation_health",
        "hash_infrastructure_health", "archive_integrity_health",
        "export_ordering_health", "snapshot_health",
        "export_metadata_compliance", "available_bundles",
        "available_snapshot_types", "recommendations",
        "export_hard_principles", "audit_entry",
    ]

    def test_all_required_keys_present(self):
        result = compute_export_infrastructure_governance()
        for k in self._REQUIRED_KEYS:
            assert k in result, f"missing key: {k}"

    def test_scope_note_contains_ftd_uei(self):
        result = compute_export_infrastructure_governance()
        assert "FTD-UEI" in result["scope_note"]

    def test_health_score_is_100_clean_registry(self):
        result = compute_export_infrastructure_governance()
        assert result["infrastructure_health_score"] == 100.0

    def test_health_tier_healthy(self):
        result = compute_export_infrastructure_governance()
        assert result["infrastructure_health_tier"] == "HEALTHY"

    def test_bundle_composer_healthy(self):
        result = compute_export_infrastructure_governance()
        assert result["bundle_composer_health"]["composer_healthy"] is True

    def test_manifest_healthy(self):
        result = compute_export_infrastructure_governance()
        assert result["manifest_generation_health"]["manifest_generation_healthy"] is True

    def test_hash_healthy(self):
        result = compute_export_infrastructure_governance()
        h = result["hash_infrastructure_health"]
        assert h["hashing_operational"] is True
        assert h["deterministic"] is True

    def test_integrity_healthy(self):
        result = compute_export_infrastructure_governance()
        assert result["archive_integrity_health"]["integrity_checks_operational"] is True

    def test_all_recommendations_not_auto_authorized(self):
        result = compute_export_infrastructure_governance()
        for rec in result["recommendations"]:
            assert rec["auto_authorized"] is False

    def test_audit_entry_structure(self):
        result = compute_export_infrastructure_governance()
        ae = result["audit_entry"]
        assert ae["entry_id"].startswith("UEI-")
        assert ae["auto_authorized"] is False
        assert ae["immutable"] is True
        assert ae["entry_type"] == "INFRASTRUCTURE_ASSESSMENT"

    def test_snapshot_health_with_snapshots(self):
        snaps = [_make_snapshot(i) for i in range(3)]
        result = compute_export_infrastructure_governance(snapshots=snaps)
        assert result["snapshot_health"]["total_snapshots"] == 3

    def test_snapshot_health_empty(self):
        result = compute_export_infrastructure_governance(snapshots=[])
        assert result["snapshot_health"]["total_snapshots"] == 0

    def test_available_bundles_has_all_six(self):
        result = compute_export_infrastructure_governance()
        for b in KNOWN_BUNDLES:
            assert b in result["available_bundles"]

    def test_available_snapshot_types_count(self):
        result = compute_export_infrastructure_governance()
        assert len(result["available_snapshot_types"]) == len(SNAPSHOT_TYPES)

    def test_metadata_compliance_defined(self):
        result = compute_export_infrastructure_governance()
        mc = result["export_metadata_compliance"]
        assert mc["compliance_schema_defined"] is True
        assert mc["required_field_count"] == 10

    def test_never_raises(self):
        result = compute_export_infrastructure_governance()
        assert isinstance(result, dict)

    def test_hard_principles_in_result(self):
        result = compute_export_infrastructure_governance()
        hp = result["export_hard_principles"]
        assert hp == EXPORT_HARD_PRINCIPLES


# ══════════════════════════════════════════════════════════════════════════════
# TestConstitutionalPrinciples
# ══════════════════════════════════════════════════════════════════════════════

class TestConstitutionalPrinciples:

    def test_human_authority_over_export_governance_true(self):
        assert EXPORT_HARD_PRINCIPLES["human_authority_over_export_governance"] is True

    def test_explicit_export_approval_required_true(self):
        assert EXPORT_HARD_PRINCIPLES["explicit_export_approval_required"] is True

    def test_immutable_archive_lineage_guaranteed_true(self):
        assert EXPORT_HARD_PRINCIPLES["immutable_archive_lineage_guaranteed"] is True

    def test_reconstruction_continuity_preserved_true(self):
        assert EXPORT_HARD_PRINCIPLES["reconstruction_continuity_preserved"] is True

    def test_manifest_integrity_enforced_true(self):
        assert EXPORT_HARD_PRINCIPLES["manifest_integrity_enforced"] is True

    def test_autonomous_archive_deletion_false(self):
        assert EXPORT_HARD_PRINCIPLES["autonomous_archive_deletion"] is False

    def test_self_authorized_export_false(self):
        assert EXPORT_HARD_PRINCIPLES["self_authorized_export_generation"] is False

    def test_autonomous_lineage_mutation_false(self):
        assert EXPORT_HARD_PRINCIPLES["autonomous_lineage_mutation"] is False

    def test_silent_manifest_alteration_false(self):
        assert EXPORT_HARD_PRINCIPLES["silent_manifest_alteration"] is False

    def test_autonomous_snapshot_governance_false(self):
        assert EXPORT_HARD_PRINCIPLES["autonomous_snapshot_governance"] is False

    def test_at_least_six_true_principles(self):
        assert sum(1 for v in EXPORT_HARD_PRINCIPLES.values() if v is True) >= 6

    def test_at_least_five_false_principles(self):
        assert sum(1 for v in EXPORT_HARD_PRINCIPLES.values() if v is False) >= 5


# ══════════════════════════════════════════════════════════════════════════════
# TestProductionIsolation
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionIsolation:

    def test_no_live_engine_import_in_download_center(self):
        import core.download_center as mod
        # Should not reference pnl_calc or data_lake
        src = open(mod.__file__).read()
        assert "pnl_calc" not in src
        assert "data_lake" not in src

    def test_compute_returns_new_dict_each_call(self):
        r1 = compute_export_infrastructure_governance()
        r2 = compute_export_infrastructure_governance()
        assert r1 is not r2

    def test_snapshots_not_mutated(self):
        snaps = [_make_snapshot(i) for i in range(3)]
        original = list(snaps)
        compute_export_infrastructure_governance(snapshots=snaps)
        assert snaps == original

    def test_fail_open_returns_dict(self):
        result = compute_export_infrastructure_governance(snapshots=None)
        assert isinstance(result, dict)

    def test_no_module_level_mutable_state_in_snapshot_manager(self):
        # snapshot_manager.py should not have a module-level _snapshot_ledger
        import core.snapshot_manager as mod
        src = open(mod.__file__).read()
        assert "_snapshot_ledger: list" not in src


# ══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_compose_bundle_empty_report_ids_via_unknown_type(self):
        bundle = compose_bundle("NONEXISTENT")
        assert "error" in bundle

    def test_verify_bundle_hash_no_metadata(self):
        result = verify_bundle_hash({})
        assert result["valid"] is False

    def test_verify_bundle_hash_no_hash_stored(self):
        bundle = {"metadata": {"bundle_type": "X", "generation_ts": 0}, "report_ids": []}
        result = verify_bundle_hash(bundle)
        assert result["valid"] is False

    def test_generate_manifest_empty_report_ids(self):
        m = generate_manifest("TEST", [], {}, 12345)
        assert isinstance(m, dict)
        assert m["report_count"] == 0

    def test_assess_archive_health_all_tampered(self):
        bundle = _make_composed_bundle()
        bundle["metadata"]["reconstruction_hash"] = "f" * 64
        h = assess_archive_health([bundle])
        assert h["healthy_bundles"] < h["total_bundles"]

    def test_get_snapshot_health_non_list_items(self):
        # Malformed items should not crash
        h = get_snapshot_health([{"snapshot_type": "HOURLY"}, {}, "bad"])
        assert isinstance(h, dict)

    def test_create_snapshot_invalid_type_coerced(self):
        snap = create_snapshot_record("INVALID_TYPE", "1.25.0", 0)
        assert snap["snapshot_type"] == "MILESTONE"

    def test_dict_hash_empty_dict(self):
        h = dict_hash({})
        assert is_valid_sha256(h)

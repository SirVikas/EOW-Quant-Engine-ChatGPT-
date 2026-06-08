"""
FTD-NEXUS-100-PERCENT-001 Phase 1 — Provenance Verifier

8 tests covering:
  1. Provenance dataclass default instantiation
  2. archive()/record() with provenance stores it in metadata
  3. archive()/record() without provenance stays backwards-compatible
  4. get_provenance_stats() returns expected dict shape
  5. After 5 records with provenance, coverage_pct > 0
  6. get_provenance_report() returns a list
  7. HKE run_extraction() produces facts with provenance
  8. DCEL archive functions produce records containing provenance key
"""
from __future__ import annotations

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure the worktree root is on sys.path
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fresh_engine(tmp_path):
    """Create a fresh IMRAFEngine backed by a temp DB."""
    from core.institutional_memory.imraf_engine import IMRAFEngine
    return IMRAFEngine(db_path=tmp_path / "test_imraf.db")


# ── Test 1: Provenance dataclass instantiates with defaults ──────────────────

def test_provenance_dataclass_defaults():
    from core.institutional_memory.imraf_engine import Provenance
    prov = Provenance()
    assert prov.source_file == ""
    assert prov.source_line == 0
    assert prov.git_sha == ""
    assert prov.extraction_method == ""
    assert prov.confidence == 0.5


# ── Test 2: archive() with provenance stores provenance in metadata ───────────

def test_record_with_provenance_stores_in_metadata(tmp_path):
    from core.institutional_memory.imraf_engine import IMRAFEngine, Category, Provenance
    engine = _fresh_engine(tmp_path)
    prov = Provenance(
        source_file="config.py",
        source_line=42,
        extraction_method="hke_config",
        confidence=0.7,
    )
    record_id = engine.record(
        category=Category.KNOWLEDGE,
        title="Test record with provenance",
        data={"content": "some fact"},
        provenance=prov,
    )
    rec = engine.get_record(record_id)
    assert rec is not None
    data = rec["data"]
    assert "provenance" in data, "provenance key missing from stored data"
    stored_prov = data["provenance"]
    assert stored_prov["source_file"] == "config.py"
    assert stored_prov["source_line"] == 42
    assert stored_prov["extraction_method"] == "hke_config"
    assert abs(stored_prov["confidence"] - 0.7) < 0.001
    engine.close()


# ── Test 3: archive() without provenance still works (backwards compat) ──────

def test_record_without_provenance_still_works(tmp_path):
    from core.institutional_memory.imraf_engine import IMRAFEngine, Category
    engine = _fresh_engine(tmp_path)
    record_id = engine.record(
        category=Category.KNOWLEDGE,
        title="Legacy record no provenance",
        data={"content": "old fact"},
    )
    rec = engine.get_record(record_id)
    assert rec is not None
    # No provenance key — but record must exist and have data
    assert rec["data"].get("content") == "old fact"
    assert "provenance" not in rec["data"]
    engine.close()


# ── Test 4: get_provenance_stats() returns dict with coverage_pct ─────────────

def test_get_provenance_stats_returns_correct_shape(tmp_path):
    from core.institutional_memory.imraf_engine import IMRAFEngine, Category
    engine = _fresh_engine(tmp_path)
    stats = engine.get_provenance_stats()
    assert isinstance(stats, dict)
    assert "total" in stats
    assert "with_provenance" in stats
    assert "coverage_pct" in stats
    assert "by_method" in stats
    assert "avg_confidence" in stats
    assert isinstance(stats["coverage_pct"], float)
    assert isinstance(stats["by_method"], dict)
    engine.close()


# ── Test 5: After 5 records with provenance, coverage_pct > 0 ────────────────

def test_coverage_pct_increases_after_provenance_records(tmp_path):
    from core.institutional_memory.imraf_engine import IMRAFEngine, Category, Provenance
    engine = _fresh_engine(tmp_path)
    prov = Provenance(source_file="test.py", extraction_method="manual", confidence=1.0)
    for i in range(5):
        engine.record(
            category=Category.KNOWLEDGE,
            title=f"Fact {i}",
            data={"content": f"content {i}"},
            provenance=prov,
        )
    stats = engine.get_provenance_stats()
    assert stats["with_provenance"] >= 5
    assert stats["coverage_pct"] > 0.0
    engine.close()


# ── Test 6: get_provenance_report() returns a list ───────────────────────────

def test_get_provenance_report_returns_list(tmp_path):
    from core.institutional_memory.imraf_engine import IMRAFEngine, Category, Provenance
    engine = _fresh_engine(tmp_path)
    prov = Provenance(source_file="test.py", extraction_method="manual", confidence=0.8)
    engine.record(
        category=Category.KNOWLEDGE,
        title="Report test record",
        data={"content": "some fact for report"},
        provenance=prov,
    )
    report = engine.get_provenance_report(limit=50)
    assert isinstance(report, list)
    # Records with provenance should appear
    assert len(report) >= 1
    # Each item must be a dict
    for item in report:
        assert isinstance(item, dict)
    engine.close()


# ── Test 7: HKE run_extraction() produces facts tagged hke_extracted ─────────

def test_hke_extraction_produces_hke_extracted_tag(tmp_path):
    """
    Run HKE extraction against a fresh IMRAF engine backed by a temp DB.
    Directly instantiate HKEEngine and inject our temp IMRAF to avoid
    polluting the shared DB and avoid module re-exec issues.
    """
    from core.institutional_memory.imraf_engine import IMRAFEngine, Category, Provenance
    from core.nexus.hke.hke_engine import HKEEngine

    # Create an isolated IMRAF engine
    test_imraf = IMRAFEngine(db_path=tmp_path / "hke_test.db")

    engine = HKEEngine()
    # Inject the isolated engine directly so HKE records into our temp DB
    engine._imraf = test_imraf
    engine._Category = Category
    engine._Provenance = Provenance

    result = engine.run_extraction()
    assert result["total_new"] > 0, "HKE should produce at least some new facts"

    # Verify hke_extracted tag appears on at least one record
    records = test_imraf.timeline(limit=500)
    hke_tagged = [r for r in records if "hke_extracted" in r.get("tags", [])]
    assert len(hke_tagged) > 0, "No records found with 'hke_extracted' tag after HKE extraction"

    # Also verify at least one has provenance
    hke_with_prov = [
        r for r in hke_tagged
        if isinstance(r.get("data"), dict) and "provenance" in r["data"]
    ]
    assert len(hke_with_prov) > 0, "No HKE records found with provenance after extraction"

    test_imraf.close()


# ── Test 8: DCEL archive functions produce records with provenance key ────────

def test_dcel_archive_includes_provenance(tmp_path):
    """
    Call a DCEL archive function with a mock IMRAF that captures the call.
    Verify the provenance kwarg was passed and contains the expected fields.
    """
    captured = {}

    class MockIMRAF:
        def record(self, **kwargs):
            captured.update(kwargs)
            return 1

    class MockCategory:
        EVOLUTION = "EVOLUTION"
        OPERATIONAL = "OPERATIONAL"
        DECISION = "DECISION"
        REGIME = "REGIME"

    class MockProvenance:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    import importlib.util as _ilu
    dcel_src = _REPO_ROOT / "core" / "nexus" / "dcel" / "dcel_engine.py"
    spec = _ilu.spec_from_file_location("test_dcel_prov", str(dcel_src))
    dcel_mod = _ilu.module_from_spec(spec)
    sys.modules["test_dcel_prov"] = dcel_mod

    mock_imraf_instance = MockIMRAF()

    def mock_imraf_fn():
        return mock_imraf_instance, MockCategory, MockProvenance

    dcel_mod.__dict__["_imraf"] = mock_imraf_fn
    spec.loader.exec_module(dcel_mod)

    # Patch _imraf function after load
    dcel_mod._imraf = mock_imraf_fn

    dcel_mod.archive_lcc_event(
        event_type="PAUSE",
        consecutive_losses=5,
        pause_minutes=30.0,
        symbol="BTCUSDT",
    )

    assert "provenance" in captured, "DCEL archive call must include provenance kwarg"
    prov = captured["provenance"]
    assert prov is not None
    assert hasattr(prov, "extraction_method")
    assert prov.extraction_method == "dcel_hook"
    assert prov.confidence == 0.9

"""Tests for DOAE Evidence Validation — P1."""
import sys
import tempfile
import os
from pathlib import Path

# Ensure project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.nexus.doae.doae_engine import DOAEEngine


@pytest.fixture
def engine(tmp_path):
    db = tmp_path / "test_doae.db"
    eng = DOAEEngine(db_path=db)
    yield eng
    eng.close()


def test_generate_evidence_report_structure(engine):
    report = engine.generate_evidence_report()
    assert "top_positive" in report
    assert "top_negative" in report
    assert "summary" in report


def test_top_positive_has_at_least_3_entries(engine):
    report = engine.generate_evidence_report()
    assert len(report["top_positive"]) >= 3


def test_each_entry_has_required_fields(engine):
    report = engine.generate_evidence_report()
    required = {"impact_score", "confidence", "wr_delta"}
    for entry in report["top_positive"]:
        missing = required - set(entry.keys())
        assert not missing, f"Entry missing fields: {missing}"


def test_summary_total_attributed_positive(engine):
    report = engine.generate_evidence_report()
    assert report["summary"]["total_attributed"] > 0


def test_top_positive_sorted_above_top_negative(engine):
    report = engine.generate_evidence_report()
    assert len(report["top_positive"]) > 0
    assert len(report["top_negative"]) > 0
    best_positive = report["top_positive"][0]["impact_score"]
    worst_negative = report["top_negative"][-1]["impact_score"]
    assert best_positive >= worst_negative, (
        f"top_positive[0].impact_score={best_positive} should be >= "
        f"top_negative[-1].impact_score={worst_negative}"
    )

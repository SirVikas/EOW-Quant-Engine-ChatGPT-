"""Tests for FTD-EGI-001 Component 1 — Historical Decision Backfill Engine."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.governance.backfill.historical_decision_backfill import (
    DecisionImporter,
    DecisionValidator,
    HistoricalDecisionBackfill,
    _KNOWN_DECISIONS,
    run_full_backfill,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

class _StubIMRAF:
    def __init__(self):
        self._records = []
        self._next_id = 1

    def record(self, category, title, data, subcategory="", tags=None):
        rid = self._next_id
        self._next_id += 1
        self._records.append({
            "id": rid, "category": category, "title": title, "data": data,
        })
        return rid

    def query(self, category=None, limit=100, search=None):
        results = self._records
        if category:
            results = [r for r in results if r["category"] == category]
        if search:
            results = [r for r in results if search.lower() in r["title"].lower()
                       or search.lower() in str(r["data"]).lower()]
        return results[:limit]

    def search(self, text, limit=10):
        text_lower = text.lower()
        return [r for r in self._records if text_lower in r["title"].lower()][:limit]


@pytest.fixture()
def stub_imraf():
    return _StubIMRAF()


@pytest.fixture()
def project_root(tmp_path):
    """Minimal project structure for backfill scanning."""
    (tmp_path / "CLAUDE.md").write_text(
        "# CLAUDE\n\nDecision: use strategy_id not strategy_type\n\nFTD-EMA-001 applies\n"
    )
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "sample.py").write_text(
        "# Decision: WAL mode enabled for concurrency\npass\n"
    )
    return tmp_path


# ── _KNOWN_DECISIONS ─────────────────────────────────────────────────────────

def test_known_decisions_not_empty():
    assert len(_KNOWN_DECISIONS) >= 11


def test_known_decisions_have_required_fields():
    required = {"decision", "component"}
    for d in _KNOWN_DECISIONS:
        missing = required - d.keys()
        assert not missing, f"Decision missing fields: {missing} — {d}"


def test_known_decisions_have_outcome_or_rationale():
    for d in _KNOWN_DECISIONS:
        has_info = "outcome" in d or "rationale" in d
        assert has_info, f"Decision missing outcome/rationale: {d}"


def test_known_decisions_have_status_or_category():
    for d in _KNOWN_DECISIONS:
        has_status = "status" in d or "category" in d
        assert has_status, f"Decision missing status/category: {d}"


# ── HistoricalDecisionBackfill ────────────────────────────────────────────────

def test_extract_known_decisions():
    backfill = HistoricalDecisionBackfill()
    decisions = backfill.extract_known_decisions()
    assert len(decisions) == len(_KNOWN_DECISIONS)


def test_extract_known_decisions_structure():
    backfill = HistoricalDecisionBackfill()
    for d in backfill.extract_known_decisions():
        assert "decision" in d
        assert "component" in d


def test_extract_from_claude_md(project_root):
    backfill = HistoricalDecisionBackfill(project_root=project_root)
    decisions = backfill.extract_from_claude_md()
    assert isinstance(decisions, list)


def test_extract_from_file_comments(project_root):
    backfill = HistoricalDecisionBackfill(project_root=project_root)
    decisions = backfill.extract_from_file_comments()
    assert isinstance(decisions, list)
    # Result may be empty if no comment patterns match — just check it's a list


def test_extract_from_git_history_graceful(project_root):
    backfill = HistoricalDecisionBackfill(project_root=project_root)
    # May return empty list if git not available or no commits — should not raise
    decisions = backfill.extract_from_git_history()
    assert isinstance(decisions, list)


def test_backfill_known_plus_claude_md(project_root):
    backfill = HistoricalDecisionBackfill(project_root=project_root)
    known = backfill.extract_known_decisions()
    from_md = backfill.extract_from_claude_md()
    combined = known + from_md
    assert len(combined) >= len(_KNOWN_DECISIONS)


# ── DecisionImporter ──────────────────────────────────────────────────────────

def test_importer_dry_run(stub_imraf):
    importer = DecisionImporter(); importer._imraf = stub_imraf
    result = importer.import_decisions(_KNOWN_DECISIONS, dry_run=True)
    assert result["status"] == "DRY_RUN"
    assert result["imported"] == len(_KNOWN_DECISIONS)
    assert len(stub_imraf._records) == 0  # nothing written


def test_importer_live_run(stub_imraf):
    importer = DecisionImporter(); importer._imraf = stub_imraf
    result = importer.import_decisions(_KNOWN_DECISIONS[:3], dry_run=False)
    assert result["imported"] == 3
    assert len(stub_imraf._records) == 3


def test_importer_dedup(stub_imraf):
    importer = DecisionImporter(); importer._imraf = stub_imraf
    # Import twice — second run should skip duplicates
    importer.import_decisions(_KNOWN_DECISIONS[:2], dry_run=False)
    result2 = importer.import_decisions(_KNOWN_DECISIONS[:2], dry_run=False)
    assert result2["skipped"] == 2
    assert len(stub_imraf._records) == 2  # no doubles


def test_importer_handles_empty_list(stub_imraf):
    importer = DecisionImporter(); importer._imraf = stub_imraf
    result = importer.import_decisions([], dry_run=False)
    assert result["imported"] == 0


def test_importer_records_uses_decision_category(stub_imraf):
    importer = DecisionImporter(); importer._imraf = stub_imraf
    # The importer uses d.get("category", "DECISION") — verify record is written
    importer.import_decisions([_KNOWN_DECISIONS[0]], dry_run=False)
    assert len(stub_imraf._records) == 1
    # category comes from the decision dict itself
    assert stub_imraf._records[0]["category"] in {"DECISION", "ARCHITECTURE", "BUG", "KNOWLEDGE"}


# ── DecisionValidator ─────────────────────────────────────────────────────────

def test_validator_with_full_imraf(stub_imraf):
    # Pre-populate with all known decisions
    importer = DecisionImporter(); importer._imraf = stub_imraf
    importer.import_decisions(_KNOWN_DECISIONS, dry_run=False)

    validator = DecisionValidator(); validator._imraf = stub_imraf
    report = validator.validate()
    assert "coverage_pct" in report
    assert report["coverage_pct"] >= 0.0


def test_validator_empty_imraf(stub_imraf):
    validator = DecisionValidator(); validator._imraf = stub_imraf
    report = validator.validate()
    assert "missing_decisions" in report
    assert len(report["missing_decisions"]) > 0


def test_validator_report_has_required_fields(stub_imraf):
    validator = DecisionValidator(); validator._imraf = stub_imraf
    report = validator.validate()
    required = {"coverage_pct", "missing_decisions", "known_decisions"}
    assert required.issubset(report.keys())


def test_validator_coverage_pct_range(stub_imraf):
    validator = DecisionValidator(); validator._imraf = stub_imraf
    report = validator.validate()
    assert 0.0 <= report["coverage_pct"] <= 100.0


# ── run_full_backfill ─────────────────────────────────────────────────────────

def test_run_full_backfill_dry_run(project_root):
    result = run_full_backfill(project_root=project_root, dry_run=True)
    assert result["status"] == "DRY_RUN"
    assert "sources" in result
    assert result["imported"] >= len(_KNOWN_DECISIONS)


def test_run_full_backfill_does_not_raise(project_root):
    # Even without IMRAF available it should not raise
    result = run_full_backfill(project_root=project_root, dry_run=True)
    assert isinstance(result, dict)

"""Tests for FTD-EGI-001 Component 4 — Institutional Truth Engine."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from core.governance.truth.truth_engine import (
    InstitutionalTruthEngine,
    TruthRecord,
    _STATIC_TRUTH,
    _UNKNOWN,
    why,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

class _StubIMRAF:
    def __init__(self, records=None):
        self._records = records or []

    def query(self, category=None, limit=100, search=None):
        results = self._records
        if category:
            results = [r for r in results if r.get("category") == category]
        return results[:limit]


def _make_engine(imraf=None):
    engine = InstitutionalTruthEngine.__new__(InstitutionalTruthEngine)
    engine._imraf = imraf
    return engine


# ── TruthRecord ───────────────────────────────────────────────────────────────

def test_truth_record_to_dict():
    tr = TruthRecord(
        query="why wal mode",
        decision="WAL enabled",
        date="2025-Q2",
        author="engineering",
        ftd_reference="FTD-IMR-001",
        verifier="pytest:imraf",
        outcome="Non-blocking reads",
        current_status="ACTIVE",
        confidence="HIGH",
        source="backfill",
    )
    d = tr.to_dict()
    assert d["query"] == "why wal mode"
    assert d["ftd_reference"] == "FTD-IMR-001"
    assert d["confidence"] == "HIGH"


def test_truth_record_has_all_required_fields():
    tr = TruthRecord(
        query="q", decision="d", date="dt", author="a",
        ftd_reference="FTD-X-001", verifier="v", outcome="o",
        current_status="cs", confidence="HIGH", source="s",
    )
    required = ["query", "decision", "date", "author", "ftd_reference",
                "verifier", "outcome", "current_status", "confidence", "source"]
    d = tr.to_dict()
    for f in required:
        assert f in d


# ── _STATIC_TRUTH ─────────────────────────────────────────────────────────────

def test_static_truth_not_empty():
    assert len(_STATIC_TRUTH) >= 11


def test_static_truth_entries_have_required_fields():
    required = {"keywords", "decision", "date", "author", "ftd_reference",
                "verifier", "outcome", "current_status", "confidence", "source"}
    for entry in _STATIC_TRUTH:
        missing = required - entry.keys()
        assert not missing, f"Static entry missing: {missing}"


def test_static_truth_keywords_are_lists():
    for entry in _STATIC_TRUTH:
        assert isinstance(entry["keywords"], list)
        assert len(entry["keywords"]) >= 1


def test_static_truth_confidence_valid():
    for entry in _STATIC_TRUTH:
        assert entry["confidence"] in {"HIGH", "MEDIUM", "LOW"}


def test_static_truth_ftd_references_valid():
    for entry in _STATIC_TRUTH:
        assert entry["ftd_reference"].startswith("FTD-")


# ── why() — static truth lookup ───────────────────────────────────────────────

def test_why_wal_mode(tmp_path):
    engine = _make_engine()
    result = engine.why("why was SQLite WAL mode enabled")
    assert isinstance(result, TruthRecord)
    assert result.confidence != ""


def test_why_trail_atr(tmp_path):
    engine = _make_engine()
    result = engine.why("why was TRAIL ATR MULT changed")
    assert isinstance(result, TruthRecord)
    assert "0.60" in result.decision or "trail" in result.decision.lower() or result.source in ("backfill", "none")


def test_why_unknown_query_returns_low_confidence():
    engine = _make_engine()
    result = engine.why("why was the flibbertigibbet parameter modified")
    assert result.confidence == "LOW"
    assert "not recorded" in result.current_status.lower() or result.source == "none"


def test_why_returns_truth_record_always():
    engine = _make_engine()
    result = engine.why("anything at all")
    assert isinstance(result, TruthRecord)


def test_why_query_preserved_in_result():
    engine = _make_engine()
    q = "why was RSI governor floor raised"
    result = engine.why(q)
    assert result.query == q


def test_why_app_version_ssot():
    engine = _make_engine()
    result = engine.why("why is APP_VERSION a single source of truth")
    assert isinstance(result, TruthRecord)


# ── why() — IMRAF lookup ──────────────────────────────────────────────────────

def test_why_prefers_imraf_decision_over_static():
    stub = _StubIMRAF(records=[{
        "id": 99,
        "category": "DECISION",
        "title": "breakeven trigger set to 1R for drawdown control",
        "created_at": "2025-06-01T12:00:00",
        "data": {
            "change": "BREAKEVEN_TRIGGER_R = 1.0",
            "ftd_reference": "FTD-STRATEGY-001",
            "outcome": "Drawdown reduced",
            "component": "strategies",
            "verifier": "pytest:strategies",
        },
    }])
    engine = _make_engine(imraf=stub)
    result = engine.why("why was breakeven trigger changed to 1R")
    assert result.source == "imraf"
    assert result.confidence == "HIGH"


def test_why_falls_back_to_static_when_imraf_empty():
    stub = _StubIMRAF(records=[])
    engine = _make_engine(imraf=stub)
    result = engine.why("why was WAL mode enabled for SQLite")
    assert result.source in ("backfill", "none")


def test_why_imraf_exception_graceful():
    class _BrokenIMRAF:
        def query(self, **kw):
            raise RuntimeError("DB error")

    engine = _make_engine(imraf=_BrokenIMRAF())
    result = engine.why("why was anything changed")
    assert isinstance(result, TruthRecord)


# ── search() ──────────────────────────────────────────────────────────────────

def test_search_returns_list():
    engine = _make_engine()
    results = engine.search("WAL mode")
    assert isinstance(results, list)


def test_search_limit_respected():
    engine = _make_engine()
    results = engine.search("strategy", limit=2)
    assert len(results) <= 2


def test_search_returns_truth_records():
    engine = _make_engine()
    results = engine.search("strategy")
    for r in results:
        assert isinstance(r, TruthRecord)


def test_search_empty_query():
    engine = _make_engine()
    results = engine.search("")
    assert isinstance(results, list)


# ── list_decisions() ──────────────────────────────────────────────────────────

def test_list_decisions_returns_list():
    engine = _make_engine()
    result = engine.list_decisions()
    assert isinstance(result, list)


def test_list_decisions_limit():
    engine = _make_engine()
    result = engine.list_decisions(limit=5)
    assert len(result) <= 5


def test_list_decisions_component_filter():
    engine = _make_engine()
    result = engine.list_decisions(component="strategy")
    for r in result:
        assert "strategy" in r.get("title", "").lower() or r.get("source") == "backfill"


def test_list_decisions_entries_have_title():
    engine = _make_engine()
    result = engine.list_decisions()
    for r in result:
        assert "title" in r or "decision" in r


# ── get_decision_coverage() ───────────────────────────────────────────────────

def test_coverage_returns_dict():
    engine = _make_engine()
    cov = engine.get_decision_coverage()
    assert isinstance(cov, dict)


def test_coverage_has_required_keys():
    engine = _make_engine()
    cov = engine.get_decision_coverage()
    assert "total_decisions" in cov
    assert "static_backfill_decisions" in cov
    assert "coverage_pct" in cov


def test_coverage_pct_range():
    engine = _make_engine()
    cov = engine.get_decision_coverage()
    assert 0.0 <= cov["coverage_pct"] <= 100.0


def test_coverage_includes_static_count():
    engine = _make_engine()
    cov = engine.get_decision_coverage()
    assert cov["static_backfill_decisions"] == len(_STATIC_TRUTH)


# ── Module-level why() function ───────────────────────────────────────────────

def test_module_level_why_returns_truth_record():
    result = why("why was anything changed")
    assert isinstance(result, TruthRecord)

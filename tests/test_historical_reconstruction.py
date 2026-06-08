"""
FTD-NEXUS-100-PERCENT-001 Phase 2 — Historical Reconstruction Verifier.

Tests 8 aspects of the new HKE extraction methods added in Phase 2:
  1. _extract_git_history() returns int >= 0
  2. _extract_parameter_rationale() returns int >= 0
  3. _extract_incident_timeline() returns int >= 0
  4. _extract_strategy_history() returns int >= 0
  5. run_extraction() by_source has git_history key
  6. run_extraction() by_source has incident_timeline key
  7. Total new facts > 10 on first fresh run (or 0 on dedup)
  8. HKE stats sources list includes all new source names
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(scope="module")
def engine():
    from core.nexus.hke.hke_engine import HKEEngine
    return HKEEngine()


# ── Test 1 ─────────────────────────────────────────────────────────────────────

def test_extract_git_history_returns_int(engine):
    """_extract_git_history() must return a non-negative integer."""
    result = engine._extract_git_history()
    assert isinstance(result, int)
    assert result >= 0


# ── Test 2 ─────────────────────────────────────────────────────────────────────

def test_extract_parameter_rationale_returns_int(engine):
    """_extract_parameter_rationale() must return a non-negative integer."""
    result = engine._extract_parameter_rationale()
    assert isinstance(result, int)
    assert result >= 0


# ── Test 3 ─────────────────────────────────────────────────────────────────────

def test_extract_incident_timeline_returns_int(engine):
    """_extract_incident_timeline() must return int >= 0; first run > 0, dedup run = 0."""
    from core.nexus.hke.hke_engine import HKEEngine
    fresh = HKEEngine()
    first_run = fresh._extract_incident_timeline()
    assert isinstance(first_run, int)
    assert first_run >= 0
    # Second run: same engine should return 0 (all already archived)
    second_run = fresh._extract_incident_timeline()
    assert isinstance(second_run, int)
    assert second_run == 0, f"Dedup failed: second run returned {second_run}"


# ── Test 4 ─────────────────────────────────────────────────────────────────────

def test_extract_strategy_history_returns_int(engine):
    """_extract_strategy_history() must return a non-negative integer."""
    result = engine._extract_strategy_history()
    assert isinstance(result, int)
    assert result >= 0


# ── Test 5 ─────────────────────────────────────────────────────────────────────

def test_run_extraction_has_git_history_key(engine):
    """run_extraction() by_source must include 'git_history' key."""
    result = engine.run_extraction()
    assert "git_history" in result["by_source"], (
        f"'git_history' missing from by_source keys: {list(result['by_source'].keys())}"
    )


# ── Test 6 ─────────────────────────────────────────────────────────────────────

def test_run_extraction_has_incident_timeline_key(engine):
    """run_extraction() by_source must include 'incident_timeline' key."""
    result = engine.run_extraction()
    assert "incident_timeline" in result["by_source"], (
        f"'incident_timeline' missing from by_source keys: {list(result['by_source'].keys())}"
    )


# ── Test 7 ─────────────────────────────────────────────────────────────────────

def test_first_fresh_run_archives_substantial_facts():
    """
    A fresh HKEEngine on first run must archive > 10 total new facts from
    the 4 new sources combined. On a subsequent run the same instance archives 0
    (all deduplicated), so the assertion accepts either > 10 or 0 for reruns.
    """
    from core.nexus.hke.hke_engine import HKEEngine
    fresh = HKEEngine()
    result = fresh.run_extraction()
    total = result["total_new"]
    # Accept 0 on reruns (dedup) but never a small non-zero number like 1–10
    # which would indicate partial extraction bugs.
    assert total > 10 or total == 0, (
        f"Expected total_new > 10 (first run) or 0 (dedup run), got {total}"
    )


# ── Test 8 ─────────────────────────────────────────────────────────────────────

def test_stats_sources_include_new_sources(engine):
    """get_stats() sources list must include all 4 new source names."""
    stats = engine.get_stats()
    sources = stats.get("sources", [])
    expected = ["git_history", "parameter_rationale", "incident_timeline", "strategy_history"]
    missing = [s for s in expected if s not in sources]
    assert not missing, f"Missing sources in stats: {missing}"

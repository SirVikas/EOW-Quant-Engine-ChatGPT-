"""
Tests for HKE audit functionality (P3).

Covers:
  - audit_extracted_facts() returns dict with all required keys
  - quality_score is between 0 and 100
  - by_category is a dict
  - get_stats() returns dict with total_extracted_lifetime and sources
  - After run_extraction(), get_stats() last_run_new >= 0
"""
import sys
import os

# Ensure the worktree root is on the path for config / core imports
_WORKTREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKTREE not in sys.path:
    sys.path.insert(0, _WORKTREE)


def _get_hke():
    from core.nexus.hke.hke_engine import HKEEngine
    return HKEEngine()


def test_audit_returns_required_keys():
    hke = _get_hke()
    result = hke.audit_extracted_facts()
    required_keys = {
        "total_hke_facts",
        "by_category",
        "duplicates_found",
        "duplicate_groups",
        "potentially_outdated",
        "low_quality",
        "quality_score",
        "audit_passed",
    }
    missing = required_keys - set(result.keys())
    assert not missing, f"Missing keys: {missing}"


def test_quality_score_in_range():
    hke = _get_hke()
    result = hke.audit_extracted_facts()
    score = result["quality_score"]
    assert isinstance(score, float), f"quality_score must be float, got {type(score)}"
    assert 0.0 <= score <= 100.0, f"quality_score out of range: {score}"


def test_by_category_is_dict():
    hke = _get_hke()
    result = hke.audit_extracted_facts()
    assert isinstance(result["by_category"], dict), "by_category must be a dict"


def test_audit_passed_is_bool():
    hke = _get_hke()
    result = hke.audit_extracted_facts()
    assert isinstance(result["audit_passed"], bool), "audit_passed must be bool"


def test_get_stats_required_keys():
    hke = _get_hke()
    stats = hke.get_stats()
    required = {"total_extracted_lifetime", "last_run_new", "last_run_ts", "sources"}
    missing = required - set(stats.keys())
    assert not missing, f"get_stats() missing keys: {missing}"


def test_get_stats_sources_is_list():
    hke = _get_hke()
    stats = hke.get_stats()
    assert isinstance(stats["sources"], list), "sources must be a list"
    assert len(stats["sources"]) > 0, "sources must not be empty"


def test_get_stats_after_run_extraction():
    hke = _get_hke()
    hke.run_extraction()
    stats = hke.get_stats()
    assert stats["last_run_new"] >= 0, "last_run_new must be >= 0 after run_extraction()"
    assert stats["last_run_ts"] > 0, "last_run_ts must be set after run_extraction()"
    assert stats["total_extracted_lifetime"] >= 0


def test_total_extracted_accumulates():
    hke = _get_hke()
    hke.run_extraction()
    first = hke.get_stats()["total_extracted_lifetime"]
    # Run again — second run should add 0 new facts (already archived) but counter stable
    hke.run_extraction()
    second = hke.get_stats()["total_extracted_lifetime"]
    assert second >= first, "total_extracted_lifetime must not decrease"

"""
Tests for Governance Intelligence real contradiction detection (P4).

Covers:
  - detect_real_contradictions() returns a list
  - detect_stale_assumptions() returns a list
  - generate_report() includes real_contradictions and stale_assumptions keys
  - governance_health_score is between 0 and 100
  - Report has real_contradiction_count key
"""
import sys
import os

_WORKTREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKTREE not in sys.path:
    sys.path.insert(0, _WORKTREE)


def _get_engine():
    from core.nexus.governance_intelligence.governance_intelligence import GovernanceIntelligenceEngine
    return GovernanceIntelligenceEngine()


def test_detect_real_contradictions_returns_list():
    engine = _get_engine()
    result = engine.detect_real_contradictions()
    assert isinstance(result, list), f"Expected list, got {type(result)}"


def test_contradiction_items_have_required_keys():
    engine = _get_engine()
    result = engine.detect_real_contradictions()
    required = {"component", "contradiction_type", "fact_a", "fact_b", "severity"}
    for item in result:
        missing = required - set(item.keys())
        assert not missing, f"Contradiction item missing keys: {missing}"


def test_detect_stale_assumptions_returns_list():
    engine = _get_engine()
    result = engine.detect_stale_assumptions()
    assert isinstance(result, list), f"Expected list, got {type(result)}"


def test_stale_items_have_required_keys():
    engine = _get_engine()
    result = engine.detect_stale_assumptions()
    required = {"content", "version", "age_versions", "component"}
    for item in result:
        missing = required - set(item.keys())
        assert not missing, f"Stale item missing keys: {missing}"


def test_generate_report_includes_real_contradictions():
    engine = _get_engine()
    report = engine.generate_report()
    assert "real_contradictions" in report, "generate_report() must include real_contradictions"
    assert isinstance(report["real_contradictions"], list)


def test_generate_report_includes_stale_assumptions():
    engine = _get_engine()
    report = engine.generate_report()
    assert "stale_assumptions" in report, "generate_report() must include stale_assumptions"
    assert isinstance(report["stale_assumptions"], list)


def test_generate_report_has_real_contradiction_count():
    engine = _get_engine()
    report = engine.generate_report()
    assert "real_contradiction_count" in report, "generate_report() must have real_contradiction_count"
    assert isinstance(report["real_contradiction_count"], int)


def test_generate_report_has_stale_count():
    engine = _get_engine()
    report = engine.generate_report()
    assert "stale_count" in report, "generate_report() must have stale_count"
    assert isinstance(report["stale_count"], int)


def test_governance_health_score_in_range():
    engine = _get_engine()
    report = engine.generate_report()
    score = report["governance_health_score"]
    assert isinstance(score, (int, float)), f"health_score must be numeric, got {type(score)}"
    assert 0 <= score <= 100, f"health_score out of range: {score}"


def test_real_contradiction_count_matches_list():
    engine = _get_engine()
    report = engine.generate_report()
    assert report["real_contradiction_count"] == len(report["real_contradictions"])


def test_stale_count_matches_list():
    engine = _get_engine()
    report = engine.generate_report()
    assert report["stale_count"] == len(report["stale_assumptions"])

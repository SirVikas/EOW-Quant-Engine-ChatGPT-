"""Tests for Governance Intelligence Engine."""
import pytest


def make_engine():
    from core.nexus.governance_intelligence.governance_intelligence import GovernanceIntelligenceEngine
    return GovernanceIntelligenceEngine()


def test_instantiates():
    engine = make_engine()
    assert engine is not None


def test_scan_assumptions_returns_at_least_5():
    engine = make_engine()
    results = engine.scan_assumptions()
    assert len(results) >= 5


def test_scan_stale_decisions_returns_list():
    engine = make_engine()
    results = engine.scan_stale_decisions()
    assert isinstance(results, list)


def test_scan_contradictions_returns_list():
    engine = make_engine()
    results = engine.scan_contradictions()
    assert isinstance(results, list)


def test_generate_cleanup_report_has_required_keys():
    engine = make_engine()
    report = engine.generate_cleanup_report()
    assert "contradictions" in report
    assert "stale_decisions" in report
    assert "assumption_violations" in report
    assert "governance_health_score" in report
    assert "total_issues" in report
    assert "recommended_actions" in report


def test_governance_health_score_in_range():
    engine = make_engine()
    report = engine.generate_cleanup_report()
    assert 0 <= report["governance_health_score"] <= 100


def test_high_severity_assumptions_present():
    engine = make_engine()
    assumptions = engine.scan_assumptions()
    severities = [a.severity for a in assumptions]
    assert "HIGH" in severities


def test_recommended_actions_is_list():
    engine = make_engine()
    report = engine.generate_cleanup_report()
    assert isinstance(report["recommended_actions"], list)
    assert len(report["recommended_actions"]) >= 1

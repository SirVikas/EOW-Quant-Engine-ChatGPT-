"""
Tests for FTD-NEXUS-100-PERCENT-001 Phase 6 — Governance Completeness.
8 tests covering lifecycle registry, contradiction escalation, coverage, and report.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.nexus.governance_intelligence.governance_intelligence import GovernanceIntelligenceEngine


@pytest.fixture
def gov():
    return GovernanceIntelligenceEngine()


def test_build_lifecycle_registry_returns_dict_with_by_state(gov):
    result = gov.build_lifecycle_registry()
    assert isinstance(result, dict)
    assert "by_state" in result
    assert isinstance(result["by_state"], dict)


def test_escalate_contradictions_to_imraf_returns_int(gov):
    result = gov.escalate_contradictions_to_imraf()
    assert isinstance(result, int)
    assert result >= 0


def test_governance_coverage_report_returns_dict_with_coverage_pct(gov):
    result = gov.governance_coverage_report()
    assert isinstance(result, dict)
    assert "coverage_pct" in result


def test_coverage_pct_is_float_0_to_100(gov):
    result = gov.governance_coverage_report()
    pct = result["coverage_pct"]
    assert isinstance(pct, float)
    assert 0.0 <= pct <= 100.0


def test_generate_report_has_lifecycle_summary(gov):
    report = gov.generate_report()
    assert "lifecycle_summary" in report
    assert isinstance(report["lifecycle_summary"], dict)


def test_generate_report_has_coverage_pct(gov):
    report = gov.generate_report()
    assert "coverage_pct" in report
    pct = report["coverage_pct"]
    assert isinstance(pct, float)


def test_generate_report_has_governance_health_score_in_range(gov):
    report = gov.generate_report()
    assert "governance_health_score" in report
    score = report["governance_health_score"]
    assert 0 <= score <= 100


def test_escalate_contradictions_idempotent(gov):
    # First call may create incidents
    gov.escalate_contradictions_to_imraf()
    # Second call must return 0 (already archived)
    second = gov.escalate_contradictions_to_imraf()
    assert second == 0

"""Tests for Institutional IQ Dashboard."""
import pytest


def make_dashboard():
    from core.nexus.iq.iq_dashboard import IQDashboard
    return IQDashboard()


def test_instantiates():
    dashboard = make_dashboard()
    assert dashboard is not None


def test_compute_returns_institutional_iq():
    dashboard = make_dashboard()
    result = dashboard.compute()
    assert "institutional_iq" in result


def test_institutional_iq_in_range():
    dashboard = make_dashboard()
    result = dashboard.compute()
    assert 0 <= result["institutional_iq"] <= 100


def test_all_5_dimensions_present():
    dashboard = make_dashboard()
    result = dashboard.compute()
    dims = result["dimensions"]
    assert "memory_coverage" in dims
    assert "economic_attribution" in dims
    assert "knowledge_coverage" in dims
    assert "governance_health" in dims
    assert "aeg_readiness" in dims


def test_grade_is_valid():
    dashboard = make_dashboard()
    result = dashboard.compute()
    assert result["grade"] in ("A", "B", "C", "D", "F")


def test_aeg_blocked_is_bool():
    dashboard = make_dashboard()
    result = dashboard.compute()
    assert isinstance(result["aeg_blocked"], bool)


def test_next_milestone_is_nonempty_string():
    dashboard = make_dashboard()
    result = dashboard.compute()
    assert isinstance(result["next_milestone"], str)
    assert len(result["next_milestone"]) > 0


def test_get_quick_score_has_institutional_iq():
    dashboard = make_dashboard()
    quick = dashboard.get_quick_score()
    assert "institutional_iq" in quick
    assert 0 <= quick["institutional_iq"] <= 100


def test_vs_baseline_is_float():
    dashboard = make_dashboard()
    result = dashboard.compute()
    assert isinstance(result["vs_baseline"], (int, float))

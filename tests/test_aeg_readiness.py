"""
Tests for FTD-NEXUS-100-PERCENT-001 Phase 7 — AEG Readiness Framework.
8 tests covering instantiation, audit structure, check results, and verdict logic.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.nexus.aeg_readiness.aeg_readiness_engine import AEGReadinessEngine, _CHECK_NAMES


@pytest.fixture
def engine():
    return AEGReadinessEngine()


def test_aeg_readiness_engine_instantiates(engine):
    assert isinstance(engine, AEGReadinessEngine)


def test_run_readiness_audit_returns_dict_with_verdict(engine):
    result = engine.run_readiness_audit()
    assert isinstance(result, dict)
    assert "verdict" in result


def test_verdict_is_valid_value(engine):
    result = engine.run_readiness_audit()
    assert result["verdict"] in ("GO", "NO_GO", "PARTIAL")


def test_counts_sum_to_eight(engine):
    result = engine.run_readiness_audit()
    total = result["pass_count"] + result["fail_count"] + result["warn_count"]
    assert total == 8


def test_blocking_failures_is_list(engine):
    result = engine.run_readiness_audit()
    assert isinstance(result["blocking_failures"], list)


def test_check_safety_system_returns_fail(engine):
    result = engine.check_safety_system()
    assert result["status"] == "FAIL"
    assert "not yet implemented" in result["message"]


def test_readiness_pct_is_float_0_to_100(engine):
    result = engine.run_readiness_audit()
    pct = result["readiness_pct"]
    assert isinstance(pct, float)
    assert 0.0 <= pct <= 100.0


def test_all_eight_check_names_present(engine):
    result = engine.run_readiness_audit()
    check_names_in_result = {c["check"] for c in result["checks"]}
    for name in _CHECK_NAMES:
        assert name in check_names_in_result

"""Tests for AEGSandboxEngine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.nexus.aeg_sandbox.aeg_sandbox_engine import AEGSandboxEngine


@pytest.fixture
def sandbox(tmp_path):
    return AEGSandboxEngine(data_file=tmp_path / "aeg_sandbox.json")


def test_instantiates(sandbox):
    assert isinstance(sandbox, AEGSandboxEngine)


def test_generate_recommendations_returns_list(sandbox):
    result = sandbox.generate_recommendations()
    assert isinstance(result, list)


def test_each_recommendation_has_required_keys(sandbox):
    recs = sandbox.generate_recommendations()
    # May be empty if all NEXUS subsystems are unavailable in test env
    required_keys = {"id", "type", "title", "recommendation", "confidence", "status"}
    for rec in recs:
        for key in required_keys:
            assert key in rec, f"Recommendation missing key: {key}"


def test_get_accuracy_stats_has_promotion_eligible(sandbox):
    stats = sandbox.get_accuracy_stats()
    assert isinstance(stats, dict)
    assert "promotion_eligible" in stats
    assert isinstance(stats["promotion_eligible"], bool)


def test_get_sandbox_status_has_promotion_status(sandbox):
    status = sandbox.get_sandbox_status()
    assert isinstance(status, dict)
    assert "promotion_status" in status
    assert status["promotion_status"] in ("ELIGIBLE", "INSUFFICIENT_DATA", "BELOW_THRESHOLD")


def test_run_sandbox_cycle_has_recommendations_key(sandbox):
    result = sandbox.run_sandbox_cycle()
    assert isinstance(result, dict)
    assert "recommendations" in result

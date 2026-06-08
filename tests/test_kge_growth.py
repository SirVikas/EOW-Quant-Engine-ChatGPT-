"""
Tests for KGEEngine.bootstrap_from_codebase.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nexus.kge.kge_engine import KGEEngine


@pytest.fixture
def engine(tmp_path):
    db = tmp_path / "kge_test.db"
    eng = KGEEngine(db_path=db)
    yield eng


# Project root is two levels above this test file
PROJECT_ROOT = str(Path(__file__).parent.parent)


def test_bootstrap_from_codebase_returns_dict(engine):
    result = engine.bootstrap_from_codebase(root_path=PROJECT_ROOT)
    assert isinstance(result, dict)
    for key in ("modules_added", "config_added", "verifiers_added", "endpoints_added", "edges_added"):
        assert key in result, f"Missing key: {key}"


def test_modules_added_greater_than_10(engine):
    result = engine.bootstrap_from_codebase(root_path=PROJECT_ROOT)
    assert result["modules_added"] > 10, (
        f"Expected >10 modules but got {result['modules_added']}"
    )


def test_config_added_greater_than_20(engine):
    result = engine.bootstrap_from_codebase(root_path=PROJECT_ROOT)
    assert result["config_added"] > 20, (
        f"Expected >20 config params but got {result['config_added']}"
    )


def test_endpoints_added_greater_than_5(engine):
    result = engine.bootstrap_from_codebase(root_path=PROJECT_ROOT)
    assert result["endpoints_added"] > 5, (
        f"Expected >5 endpoints but got {result['endpoints_added']}"
    )


def test_deduplication_on_second_call(engine):
    r1 = engine.bootstrap_from_codebase(root_path=PROJECT_ROOT)
    r2 = engine.bootstrap_from_codebase(root_path=PROJECT_ROOT)
    # Second run should add nothing — all nodes already exist
    assert r2["modules_added"] == 0
    assert r2["config_added"] == 0
    assert r2["endpoints_added"] == 0

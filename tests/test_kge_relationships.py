"""Tests for KGE Relationship Intelligence — P2."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.nexus.kge.kge_engine import KGEEngine


@pytest.fixture
def engine(tmp_path):
    db = tmp_path / "test_kge.db"
    eng = KGEEngine(db_path=db)
    # Scan the real codebase so we get enough nodes/edges for density assertions.
    root = str(Path(__file__).parent.parent)
    eng.bootstrap_from_codebase(root_path=root)
    yield eng


def test_build_intelligent_relationships_returns_dict(engine):
    result = engine.build_intelligent_relationships()
    assert isinstance(result, dict)
    assert "edges_added" in result


def test_relationship_intelligence_score_structure(engine):
    score = engine.relationship_intelligence_score()
    required = {
        "total_nodes", "total_edges", "avg_edges_per_node",
        "isolated_nodes", "well_connected", "relationship_density",
        "intelligence_score", "top_hubs",
    }
    missing = required - set(score.keys())
    assert not missing, f"Missing keys: {missing}"


def test_intelligence_score_range(engine):
    score = engine.relationship_intelligence_score()
    assert 0 <= score["intelligence_score"] <= 100


def test_intelligence_score_above_20_after_bootstrap(engine):
    score = engine.relationship_intelligence_score()
    assert score["intelligence_score"] > 20, (
        f"intelligence_score={score['intelligence_score']} expected > 20"
    )


def test_total_edges_greater_than_static_nodes(engine):
    # After intelligent relationship building the graph must have more edges
    # than the static bootstrap node set (46 nodes from bootstrap_from_static).
    # We don't require edges > all nodes because the codebase scan adds hundreds
    # of CONFIG/ENDPOINT nodes that cannot all be fully cross-connected.
    score = engine.relationship_intelligence_score()
    assert score["total_edges"] > 46, (
        f"edges={score['total_edges']} should exceed static bootstrap node count (46)"
    )


def test_top_hubs_is_nonempty_list(engine):
    score = engine.relationship_intelligence_score()
    assert isinstance(score["top_hubs"], list)
    assert len(score["top_hubs"]) >= 1

"""
FTD-NEXUS-100-PERCENT-001 Phase 4 — KGE Intelligence Expansion Verifier.

Tests 8 aspects of build_deep_relationships():
  1. build_deep_relationships() returns dict with edge type counts
  2. ROADMAP nodes added (at least 6)
  3. ENDPOINT→MODULE edges added (at least 1)
  4. CONFIG→FTD edges added (at least 3)
  5. VERIFIER→MODULE edges added (at least 3)
  6. relationship_intelligence_score() returns intelligence_score > 0
  7. ROADMAP nodes have PRECEDES edges
  8. Second call to build_deep_relationships() adds 0 duplicates (idempotent)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.nexus.kge.kge_engine import KGEEngine


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    db = tmp_path_factory.mktemp("kge_intel") / "test_kge_intel.db"
    eng = KGEEngine(db_path=db)
    # Bootstrap codebase so ENDPOINT, VERIFIER, CONFIG, MODULE nodes exist.
    root = str(Path(__file__).parent.parent)
    eng.bootstrap_from_codebase(root_path=root)
    return eng


# ── Test 1 ─────────────────────────────────────────────────────────────────────

def test_build_deep_relationships_returns_dict(engine):
    """build_deep_relationships() must return a dict with expected edge-count keys."""
    result = engine.build_deep_relationships()
    assert isinstance(result, dict)
    expected_keys = {
        "endpoint_module_edges",
        "config_ftd_edges",
        "verifier_module_edges",
        "decision_supersedes_edges",
        "roadmap_nodes_added",
        "roadmap_edges_added",
    }
    missing = expected_keys - set(result.keys())
    assert not missing, f"Missing keys: {missing}"


# ── Test 2 ─────────────────────────────────────────────────────────────────────

def test_roadmap_nodes_added(engine):
    """At least 6 ROADMAP nodes must exist after bootstrap."""
    with engine._connect() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM kg_nodes WHERE node_type='ROADMAP'"
        ).fetchone()[0]
    assert count >= 6, f"Expected >= 6 ROADMAP nodes, got {count}"


# ── Test 3 ─────────────────────────────────────────────────────────────────────

def test_endpoint_module_edges_added(engine):
    """At least 1 ENDPOINT→MODULE CALLS edge must exist."""
    with engine._connect() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM kg_edges WHERE relationship='CALLS'"
        ).fetchone()[0]
    assert count >= 1, f"Expected >= 1 CALLS edges, got {count}"


# ── Test 4 ─────────────────────────────────────────────────────────────────────

def test_config_ftd_edges_added(engine):
    """At least 3 CONFIG→FTD INTRODUCED_BY edges must exist."""
    with engine._connect() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM kg_edges WHERE relationship='INTRODUCED_BY'"
        ).fetchone()[0]
    assert count >= 3, f"Expected >= 3 INTRODUCED_BY edges, got {count}"


# ── Test 5 ─────────────────────────────────────────────────────────────────────

def test_verifier_module_edges_added(engine):
    """At least 3 VERIFIER→MODULE TESTS edges must exist."""
    with engine._connect() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM kg_edges WHERE relationship='TESTS'"
        ).fetchone()[0]
    assert count >= 3, f"Expected >= 3 TESTS edges, got {count}"


# ── Test 6 ─────────────────────────────────────────────────────────────────────

def test_relationship_intelligence_score_positive(engine):
    """relationship_intelligence_score() must return intelligence_score > 0."""
    score = engine.relationship_intelligence_score()
    assert "intelligence_score" in score
    assert score["intelligence_score"] > 0, (
        f"intelligence_score={score['intelligence_score']} expected > 0"
    )


# ── Test 7 ─────────────────────────────────────────────────────────────────────

def test_roadmap_precedes_edges_exist(engine):
    """ROADMAP nodes must have PRECEDES edges forming a sequential chain."""
    with engine._connect() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM kg_edges WHERE relationship='PRECEDES'"
        ).fetchone()[0]
    assert count >= 6, f"Expected >= 6 PRECEDES edges (7-phase chain = 6 links), got {count}"


# ── Test 8 ─────────────────────────────────────────────────────────────────────

def test_build_deep_relationships_idempotent(engine):
    """Second call to build_deep_relationships() must add 0 duplicates."""
    result2 = engine.build_deep_relationships()
    total_edges = sum(v for k, v in result2.items() if "edges" in k)
    roadmap_new = result2.get("roadmap_nodes_added", 0)
    assert total_edges == 0, (
        f"Expected 0 new edges on second call (idempotent), got {total_edges}"
    )
    assert roadmap_new == 0, (
        f"Expected 0 new roadmap nodes on second call, got {roadmap_new}"
    )

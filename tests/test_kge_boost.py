"""
Tests for KGE Phase-5 intelligence boost methods.
Uses an in-memory temp DB so production graph is not touched.
"""
import tempfile
import os
import pytest
from pathlib import Path


def _fresh_engine():
    """Return a KGEEngine backed by a brand-new temp DB with static bootstrap done."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    # Remove the file so KGEEngine creates it clean (bootstrap will run)
    os.unlink(tmp.name)
    from core.nexus.kge.kge_engine import KGEEngine
    engine = KGEEngine(db_path=Path(tmp.name))
    return engine, tmp.name


def _cleanup(path: str):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Test 1: build_semantic_edges returns dict with semantic_edges_added >= 0
# ---------------------------------------------------------------------------
def test_build_semantic_edges_returns_dict():
    engine, db_path = _fresh_engine()
    try:
        result = engine.build_semantic_edges()
        assert isinstance(result, dict)
        assert "semantic_edges_added" in result
        assert result["semantic_edges_added"] >= 0
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 2: build_temporal_chain returns dict with temporal_edges_added > 0
# ---------------------------------------------------------------------------
def test_build_temporal_chain_adds_edges():
    engine, db_path = _fresh_engine()
    try:
        result = engine.build_temporal_chain()
        assert isinstance(result, dict)
        assert "temporal_edges_added" in result
        assert result["temporal_edges_added"] > 0, (
            f"Expected >0 temporal edges, got {result['temporal_edges_added']}"
        )
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 3: build_impact_propagation_edges returns metric_nodes_added >= 7
# ---------------------------------------------------------------------------
def test_build_impact_propagation_edges_metric_nodes():
    engine, db_path = _fresh_engine()
    try:
        result = engine.build_impact_propagation_edges()
        assert isinstance(result, dict)
        assert "metric_nodes_added" in result
        assert result["metric_nodes_added"] >= 7, (
            f"Expected >=7 metric nodes, got {result['metric_nodes_added']}"
        )
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 4: build_causal_hypothesis_edges returns dict with causal_edges_added >= 0
# ---------------------------------------------------------------------------
def test_build_causal_hypothesis_edges_returns_dict():
    engine, db_path = _fresh_engine()
    try:
        # Ensure metric nodes exist first (causal hypotheses target METRIC nodes)
        engine.build_impact_propagation_edges()
        result = engine.build_causal_hypothesis_edges()
        assert isinstance(result, dict)
        assert "causal_edges_added" in result
        assert result["causal_edges_added"] >= 0
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 5: After all 4 methods, intelligence_score > 41
# ---------------------------------------------------------------------------
def test_intelligence_score_improves_after_boost():
    engine, db_path = _fresh_engine()
    try:
        baseline = engine.relationship_intelligence_score()
        baseline_score = baseline["intelligence_score"]

        engine.build_semantic_edges()
        engine.build_temporal_chain()
        engine.build_impact_propagation_edges()
        engine.build_causal_hypothesis_edges()

        after = engine.relationship_intelligence_score()
        after_score = after["intelligence_score"]

        assert after_score > 41, (
            f"Expected intelligence_score > 41, got {after_score} "
            f"(baseline was {baseline_score})"
        )
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 6: isolated_nodes after boost < 714
# ---------------------------------------------------------------------------
def test_isolated_nodes_reduced_after_boost():
    engine, db_path = _fresh_engine()
    try:
        engine.build_semantic_edges()
        engine.build_temporal_chain()
        engine.build_impact_propagation_edges()
        engine.build_causal_hypothesis_edges()

        after = engine.relationship_intelligence_score()
        isolated = after["isolated_nodes"]

        assert isolated < 714, (
            f"Expected isolated_nodes < 714 after boost, got {isolated}"
        )
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 7: relationship_intelligence_score() dict has semantic_edges key
# ---------------------------------------------------------------------------
def test_relationship_intelligence_score_has_semantic_edges_key():
    engine, db_path = _fresh_engine()
    try:
        result = engine.relationship_intelligence_score()
        assert "semantic_edges" in result, (
            f"Expected 'semantic_edges' key in result, got keys: {list(result.keys())}"
        )
        assert "temporal_edges" in result
        assert "causal_hypotheses" in result
        assert "metric_nodes" in result
    finally:
        _cleanup(db_path)


# ---------------------------------------------------------------------------
# Test 8: temporal chain creates PRECEDED_BY edges between consecutive FTDs
# ---------------------------------------------------------------------------
def test_temporal_chain_creates_preceded_by_edges():
    engine, db_path = _fresh_engine()
    try:
        engine.build_temporal_chain()

        with engine._connect() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM kg_edges WHERE relationship='PRECEDED_BY'"
            ).fetchone()[0]

        assert count > 0, f"Expected PRECEDED_BY edges, got {count}"

        # Verify specific consecutive pair exists: FTD-IMR-001 → FTD-DIAL-001
        with engine._connect() as con:
            row = con.execute(
                "SELECT 1 FROM kg_edges "
                "WHERE from_node='FTD-IMR-001' AND to_node='FTD-DIAL-001' "
                "AND relationship='PRECEDED_BY'"
            ).fetchone()
        assert row is not None, "Expected FTD-IMR-001 PRECEDED_BY FTD-DIAL-001 edge"
    finally:
        _cleanup(db_path)

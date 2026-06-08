"""Tests for KGE v2 — Knowledge Graph Engine."""
import pytest
from pathlib import Path


def make_kge(tmp_path):
    from core.nexus.kge.kge_engine import KGEEngine
    return KGEEngine(db_path=tmp_path / "kge.db")


def test_kge_initializes_and_bootstraps(tmp_path):
    kge = make_kge(tmp_path)
    stats = kge.get_stats()
    assert stats["node_count"] >= 20


def test_add_node_new_returns_true(tmp_path):
    kge = make_kge(tmp_path)
    result = kge.add_node("MODULE", "test_module_unique", "Test Module")
    assert result is True


def test_add_node_duplicate_returns_false(tmp_path):
    kge = make_kge(tmp_path)
    kge.add_node("MODULE", "dup_node", "Dup")
    result = kge.add_node("MODULE", "dup_node", "Dup Again")
    assert result is False


def test_add_edge_new_returns_true(tmp_path):
    kge = make_kge(tmp_path)
    kge.add_node("MODULE", "nodeA", "A")
    kge.add_node("MODULE", "nodeB", "B")
    result = kge.add_edge("nodeA", "nodeB", "DEPENDS_ON")
    assert result is True


def test_add_edge_duplicate_returns_false(tmp_path):
    kge = make_kge(tmp_path)
    kge.add_node("MODULE", "nodeX", "X")
    kge.add_node("MODULE", "nodeY", "Y")
    kge.add_edge("nodeX", "nodeY", "RELATED_TO")
    result = kge.add_edge("nodeX", "nodeY", "RELATED_TO")
    assert result is False


def test_get_neighbors_for_genome_engine(tmp_path):
    kge = make_kge(tmp_path)
    result = kge.get_neighbors("genome_engine", max_depth=2)
    assert result["node"] is not None
    assert result["node"]["node_id"] == "genome_engine"
    assert isinstance(result["neighbors"], list)
    assert len(result["neighbors"]) > 0


def test_get_stats_has_min_nodes_and_edges(tmp_path):
    kge = make_kge(tmp_path)
    stats = kge.get_stats()
    assert "node_count" in stats
    assert "edge_count" in stats
    assert stats["node_count"] >= 20
    assert stats["edge_count"] >= 10


def test_get_stats_coverage_score_in_range(tmp_path):
    kge = make_kge(tmp_path)
    stats = kge.get_stats()
    assert 0 <= stats["coverage_score"] <= 100


def test_enrich_from_imraf_runs_without_error(tmp_path):
    kge = make_kge(tmp_path)
    kge.enrich_from_imraf()  # Should not raise even if imraf DB is empty


def test_get_full_graph_returns_nodes_and_edges(tmp_path):
    kge = make_kge(tmp_path)
    result = kge.get_full_graph()
    assert "nodes" in result
    assert "edges" in result
    assert isinstance(result["nodes"], list)
    assert isinstance(result["edges"], list)
    assert result["total_nodes"] >= 20


def test_get_signal_chain_has_chain_key(tmp_path):
    kge = make_kge(tmp_path)
    result = kge.get_signal_chain()
    assert "chain" in result
    assert isinstance(result["chain"], list)
    assert len(result["chain"]) > 0
    assert "completeness" in result
    assert 0.0 <= result["completeness"] <= 1.0

"""
Tests for FTD-NEXUS-100-PERCENT-001 Phase 5 — Confidence Engine.
8 tests covering instantiation, scoring, and composite metrics.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.nexus.confidence.confidence_engine import ConfidenceEngine


@pytest.fixture
def engine():
    return ConfidenceEngine()


def test_confidence_engine_instantiates(engine):
    assert isinstance(engine, ConfidenceEngine)


def test_score_fact_returns_float_in_range(engine):
    record = {
        "category": "DECISION",
        "tags": ["decision", "test"],
        "data": {},
        "ts": int(__import__("time").time() * 1000),
    }
    score = engine.score_fact(record)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_verifier_scores_higher_than_knowledge(engine):
    ts = int(__import__("time").time() * 1000)
    verifier_rec = {"category": "VERIFIER", "tags": ["test"], "data": {}, "ts": ts}
    knowledge_rec = {"category": "KNOWLEDGE", "tags": ["fact"], "data": {}, "ts": ts}
    assert engine.score_fact(verifier_rec) > engine.score_fact(knowledge_rec)


def test_record_with_provenance_scores_higher(engine):
    ts = int(__import__("time").time() * 1000)
    with_prov = {
        "category": "DECISION",
        "tags": ["decision"],
        "data": {"provenance": {"source": "git", "git_sha": "abc123"}},
        "ts": ts,
    }
    without_prov = {
        "category": "DECISION",
        "tags": ["decision"],
        "data": {},
        "ts": ts,
    }
    assert engine.score_fact(with_prov) > engine.score_fact(without_prov)


def test_compute_nexus_confidence_returns_dict_with_composite(engine):
    result = engine.compute_nexus_confidence()
    assert isinstance(result, dict)
    assert "nexus_composite_confidence" in result
    assert isinstance(result["nexus_composite_confidence"], float)


def test_get_low_confidence_facts_returns_list(engine):
    result = engine.get_low_confidence_facts(threshold=0.9, limit=10)
    assert isinstance(result, list)


def test_score_attribution_returns_float(engine):
    attr = {"confidence": "HIGH", "notes": "", "post_trades": 250}
    score = engine.score_attribution(attr)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_compute_nexus_confidence_recommendation_ready_is_bool(engine):
    result = engine.compute_nexus_confidence()
    assert "recommendation_ready" in result
    assert isinstance(result["recommendation_ready"], bool)

"""
Tests for DOAEEngine.compute_attribution_from_raw and run_all_attributions.
"""
import sys
import os
import tempfile
from pathlib import Path

import pytest

# Ensure project root is on path so config imports succeed
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nexus.doae.doae_engine import DOAEEngine


@pytest.fixture
def engine(tmp_path):
    db = tmp_path / "doae_test.db"
    eng = DOAEEngine(db_path=db)
    yield eng
    eng.close()


PRE = {
    "win_rate": 0.50,
    "profit_factor": 1.2,
    "avg_pnl": 5.0,
    "total_pnl": 500.0,
    "trades_count": 10,
}

POST_BETTER = {
    "win_rate": 0.60,
    "profit_factor": 1.5,
    "avg_pnl": 8.0,
    "total_pnl": 800.0,
    "trades_count": 10,
}

POST_WORSE = {
    "win_rate": 0.40,
    "profit_factor": 0.9,
    "avg_pnl": 2.0,
    "total_pnl": 200.0,
    "trades_count": 10,
}

POST_MEDIUM_CONFIDENCE = {**POST_BETTER, "trades_count": 50}
POST_HIGH_CONFIDENCE = {**POST_BETTER, "trades_count": 150}


def test_compute_attribution_from_raw_returns_dict(engine):
    result = engine.compute_attribution_from_raw("FTD-TEST-001", PRE, POST_BETTER)
    assert isinstance(result, dict)
    assert "impact_score" in result
    assert result["ftd_id"] == "FTD-TEST-001"


def test_positive_impact_score_when_post_better(engine):
    result = engine.compute_attribution_from_raw("FTD-TEST-POS", PRE, POST_BETTER)
    assert result["impact_score"] > 0, (
        f"Expected positive impact_score but got {result['impact_score']}"
    )


def test_negative_impact_score_when_post_worse(engine):
    result = engine.compute_attribution_from_raw("FTD-TEST-NEG", PRE, POST_WORSE)
    assert result["impact_score"] < 0, (
        f"Expected negative impact_score but got {result['impact_score']}"
    )


def test_confidence_low_when_trades_under_20(engine):
    pre = {**PRE, "trades_count": 5}
    post = {**POST_BETTER, "trades_count": 10}
    result = engine.compute_attribution_from_raw("FTD-CONF-LOW", pre, post)
    assert result["confidence"] == "LOW"


def test_confidence_medium_when_trades_20_to_99(engine):
    result = engine.compute_attribution_from_raw("FTD-CONF-MED", PRE, POST_MEDIUM_CONFIDENCE)
    assert result["confidence"] == "MEDIUM"


def test_confidence_high_when_trades_100_plus(engine):
    result = engine.compute_attribution_from_raw("FTD-CONF-HIGH", PRE, POST_HIGH_CONFIDENCE)
    assert result["confidence"] == "HIGH"


def test_deltas_in_result(engine):
    result = engine.compute_attribution_from_raw("FTD-DELTA", PRE, POST_BETTER)
    assert "wr_delta" in result
    assert "pf_delta" in result
    assert "pnl_delta" in result
    assert round(result["wr_delta"], 4) == round(POST_BETTER["win_rate"] - PRE["win_rate"], 4)

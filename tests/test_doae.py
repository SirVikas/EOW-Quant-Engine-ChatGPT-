"""
Tests for PHOENIX NEXUS DOAE — Decision Outcome Attribution Engine.
FTD-NEXUS-ACCELERATION-001 Phase-B
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


def _make_doae(tmp_path: Path):
    """Create a fresh DOAEEngine instance with an isolated temp DB."""
    from core.nexus.doae.doae_engine import DOAEEngine
    engine = DOAEEngine(db_path=tmp_path / "doae_test.db")
    return engine


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_init_and_seed(tmp_path):
    """DOAEEngine initialises and seeds without error."""
    engine = _make_doae(tmp_path)
    stats = engine.get_stats()
    assert stats["total_ftds"] >= 13
    assert stats["total_config_changes"] >= 10
    engine.close()


def test_get_ftd_registry(tmp_path):
    engine = _make_doae(tmp_path)
    registry = engine.get_ftd_registry()
    assert len(registry) >= 13
    ftd_ids = [r["ftd_id"] for r in registry]
    assert "FTD-IMR-001" in ftd_ids
    assert "FTD-NEXUS-ACCELERATION-001" in ftd_ids
    engine.close()


def test_get_config_changes(tmp_path):
    engine = _make_doae(tmp_path)
    changes = engine.get_config_changes()
    assert len(changes) >= 10
    params = [c["param_name"] for c in changes]
    assert "BREAKEVEN_TRIGGER_R" in params
    engine.close()


def test_record_snapshot(tmp_path):
    engine = _make_doae(tmp_path)
    row_id = engine.record_snapshot(
        win_rate=0.58,
        profit_factor=1.7,
        avg_pnl=12.5,
        total_pnl=1500.0,
        trades_count=120,
        active_ftds=["FTD-057", "FTD-037"],
    )
    assert row_id is not None and row_id > 0
    stats = engine.get_stats()
    assert stats["snapshot_count"] == 1
    engine.close()


def test_compute_attribution_returns_required_keys(tmp_path):
    engine = _make_doae(tmp_path)
    result = engine.compute_attribution("FTD-057")
    required = {
        "ftd_id", "pre_pf", "post_pf", "pf_delta",
        "impact_score", "confidence",
    }
    for key in required:
        assert key in result, f"Missing key: {key}"
    assert result["ftd_id"] == "FTD-057"
    engine.close()


def test_compute_attribution_no_snapshots_notes(tmp_path):
    """Without trade snapshots, attribution notes = 'insufficient snapshot history'."""
    engine = _make_doae(tmp_path)
    result = engine.compute_attribution("FTD-037")
    assert "insufficient" in result["notes"]
    assert result["confidence"] == "LOW"
    engine.close()


def test_compute_attribution_with_snapshots(tmp_path):
    """With pre and post snapshots, deltas should be computed."""
    engine = _make_doae(tmp_path)
    # Insert pre-deploy snapshot
    engine._conn.execute(
        "INSERT INTO trade_snapshots "
        "(snapshot_date, engine_version, active_ftds, trades_count, "
        "win_rate, profit_factor, avg_pnl, total_pnl, ts) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("2024-04-01", "1.0.0", "[]", 50, 0.50, 1.2, 8.0, 400.0, 1700000000000),
    )
    # Insert post-deploy snapshot (FTD-057 deploy_date = 2024-06-01)
    engine._conn.execute(
        "INSERT INTO trade_snapshots "
        "(snapshot_date, engine_version, active_ftds, trades_count, "
        "win_rate, profit_factor, avg_pnl, total_pnl, ts) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("2024-07-01", "1.2.0", "[]", 80, 0.58, 1.7, 12.0, 960.0, 1720000000000),
    )
    engine._conn.commit()

    result = engine.compute_attribution("FTD-057")
    assert result["notes"] == ""
    assert result["pre_pf"] == pytest.approx(1.2)
    assert result["post_pf"] == pytest.approx(1.7)
    assert result["pf_delta"] == pytest.approx(0.5, abs=0.01)
    assert result["impact_score"] != 0.0
    engine.close()


def test_get_top_positive(tmp_path):
    engine = _make_doae(tmp_path)
    result = engine.get_top_positive(n=5)
    assert isinstance(result, list)
    engine.close()


def test_get_top_negative(tmp_path):
    engine = _make_doae(tmp_path)
    result = engine.get_top_negative(n=5)
    assert isinstance(result, list)
    engine.close()


def test_get_attribution_report_keys(tmp_path):
    engine = _make_doae(tmp_path)
    report = engine.get_attribution_report()
    assert "ftd_registry" in report
    assert "config_changes" in report
    assert "attributions" in report
    assert "is_operational" in report
    assert isinstance(report["ftd_registry"], list)
    engine.close()


def test_compute_all_attributions(tmp_path):
    """compute_all_attributions runs without error for all seeded FTDs."""
    engine = _make_doae(tmp_path)
    engine.compute_all_attributions()
    stats = engine.get_stats()
    # Some attributions should be computed (for FTDs with deploy_date set)
    assert stats["ftds_with_attribution"] >= 1
    engine.close()


def test_get_stats_keys(tmp_path):
    engine = _make_doae(tmp_path)
    stats = engine.get_stats()
    assert "total_ftds" in stats
    assert "ftds_with_attribution" in stats
    assert "attribution_operational" in stats
    assert "total_config_changes" in stats
    assert "snapshot_count" in stats
    engine.close()


def test_seed_idempotent(tmp_path):
    """Calling seed() twice should not duplicate rows."""
    engine = _make_doae(tmp_path)
    engine.seed()  # called again explicitly
    registry = engine.get_ftd_registry()
    ftd_ids = [r["ftd_id"] for r in registry]
    # Should not have duplicates
    assert len(ftd_ids) == len(set(ftd_ids))
    engine.close()

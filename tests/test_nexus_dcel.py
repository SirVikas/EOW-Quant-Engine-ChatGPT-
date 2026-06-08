"""
Tests for PHOENIX NEXUS DCEL — Decision Capture Expansion Layer.
FTD-NEXUS-ACCELERATION-001 Phase-A
"""
from __future__ import annotations

import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_fresh_imraf(tmp_path: Path):
    """Instantiate a fresh IMRAFEngine backed by a temp DB."""
    from core.institutional_memory.imraf_engine import IMRAFEngine
    return IMRAFEngine(db_path=tmp_path / "imraf_test.db")


def _patch_imraf(imraf_instance):
    """Patch the _imraf() helper in dcel_engine to use our test instance."""
    from core.institutional_memory.imraf_engine import Category, Provenance

    def _fake_imraf():
        return imraf_instance, Category, Provenance

    return patch("core.nexus.dcel.dcel_engine._imraf", side_effect=_fake_imraf)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_archive_genome_decision(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_genome_decision
        archive_genome_decision(
            strategy_type="TREND_FOLLOW",
            decision="PROMOTED",
            genome_id="g-001",
            train_pf=1.8,
            oos_pf=1.5,
            avg_r=0.4,
            win_rate=0.6,
            cost_drag=0.5,
            trades=120,
            reason="passed all gates",
            dna_keys=["rsi_lo", "rsi_hi"],
        )
    stats = im.get_stats()
    assert stats["by_category"].get("EVOLUTION", 0) >= 1


def test_archive_genome_decision_rejected(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_genome_decision
        archive_genome_decision(
            strategy_type="MR",
            decision="REJECTED",
            genome_id="g-002",
            train_pf=0.9,
            oos_pf=0.8,
            avg_r=0.1,
            win_rate=0.4,
            cost_drag=2.0,
            trades=30,
            reason="below min PF",
            dna_keys=["rsi_lo"],
        )
    stats = im.get_stats()
    assert stats["by_category"].get("EVOLUTION", 0) >= 1


def test_archive_rsi_adaptation(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_rsi_adaptation
        archive_rsi_adaptation(
            regime="TRENDING",
            action="TIGHTEN",
            old_bands={"long_rsi_min": 44.0},
            new_bands={"long_rsi_min": 46.0},
            survival_rate=0.88,
        )
    stats = im.get_stats()
    assert stats["by_category"].get("EVOLUTION", 0) >= 1
    # Verify subcategory contains the regime + action
    records = im.timeline(limit=10)
    assert any("RSI_TRENDING_TIGHTEN" in r.get("subcategory", "") for r in records)


def test_archive_lcc_pause(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_lcc_event
        archive_lcc_event(
            event_type="PAUSE_START",
            consecutive_losses=5,
            pause_minutes=30,
        )
    stats = im.get_stats()
    assert stats["by_category"].get("OPERATIONAL", 0) >= 1


def test_archive_lcc_resume(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_lcc_event
        archive_lcc_event(event_type="RESUME", consecutive_losses=0)
    stats = im.get_stats()
    assert stats["by_category"].get("OPERATIONAL", 0) >= 1


def test_archive_safe_mode(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_safe_mode_event
        archive_safe_mode_event(action="ACTIVATED", reason="drawdown exceeded threshold")
    stats = im.get_stats()
    assert stats["by_category"].get("OPERATIONAL", 0) >= 1


def test_archive_scorer_near_miss_archives(tmp_path):
    """Score within 10 of threshold should be archived even if passed."""
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_scorer_decision
        archive_scorer_decision(
            symbol="BTCUSDT",
            regime="TRENDING",
            score=65.0,
            threshold=60.0,  # score - threshold = 5 → near-miss
            passed=True,
            factors={"edge": 0.8},
            strategy="TREND_FOLLOW",
        )
    stats = im.get_stats()
    assert stats["by_category"].get("DECISION", 0) >= 1


def test_archive_scorer_far_pass_skips(tmp_path):
    """Score far above threshold (passed=True, gap>10) should not be archived."""
    im = _make_fresh_imraf(tmp_path)
    initial_stats = im.get_stats()
    initial_count = initial_stats["by_category"].get("DECISION", 0)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_scorer_decision
        archive_scorer_decision(
            symbol="BTCUSDT",
            regime="TRENDING",
            score=80.0,
            threshold=30.0,  # gap = 50 > 10, passed → skip
            passed=True,
            factors={"edge": 0.9},
            strategy="TREND_FOLLOW",
        )
    stats = im.get_stats()
    assert stats["by_category"].get("DECISION", 0) == initial_count


def test_archive_scorer_fail_always_archives(tmp_path):
    """Failed scorer decisions should always be archived regardless of gap."""
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_scorer_decision
        archive_scorer_decision(
            symbol="ETHUSDT",
            regime="MR",
            score=20.0,
            threshold=70.0,  # gap = 50, failed
            passed=False,
            factors={},
            strategy="MEAN_REVERTING",
        )
    stats = im.get_stats()
    assert stats["by_category"].get("DECISION", 0) >= 1


def test_archive_rl_summary_throttle(tmp_path):
    """Second RL archive within 60 seconds should be suppressed."""
    im = _make_fresh_imraf(tmp_path)
    import core.nexus.dcel.dcel_engine as dcel_mod
    # Reset throttle
    dcel_mod._last_rl_archive_ts = 0.0

    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_rl_summary
        archive_rl_summary(
            total_contexts=10,
            total_pulls=50,
            avg_q=0.3,
            toxic_count=2,
            eco_toxic_count=1,
            convergence_state="CONVERGING",
            intelligence_score=0.75,
        )
        count_after_first = im.get_stats()["by_category"].get("EVOLUTION", 0)

        # Second call immediately — should NOT archive
        archive_rl_summary(
            total_contexts=11,
            total_pulls=51,
            avg_q=0.31,
            toxic_count=2,
            eco_toxic_count=1,
            convergence_state="CONVERGING",
            intelligence_score=0.76,
        )
        count_after_second = im.get_stats()["by_category"].get("EVOLUTION", 0)

    assert count_after_second == count_after_first


def test_archive_regime_transition(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_regime_transition
        archive_regime_transition(
            symbol="BTCUSDT",
            old_regime="MEAN_REVERTING",
            new_regime="TRENDING",
            trigger="volatility_spike",
            session="LONDON",
        )
    stats = im.get_stats()
    assert stats["by_category"].get("REGIME", 0) >= 1


def test_archive_risk_state_change(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import archive_risk_state_change
        archive_risk_state_change(
            event="DAILY_LIMIT_APPROACH",
            daily_used_pct=85.0,
            daily_cap_pct=90.0,
            drawdown_pct=3.5,
            safe_mode=False,
            reason="approaching daily cap",
        )
    stats = im.get_stats()
    assert stats["by_category"].get("OPERATIONAL", 0) >= 1


def test_coverage_stats_keys(tmp_path):
    im = _make_fresh_imraf(tmp_path)
    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import get_coverage_stats
        stats = get_coverage_stats()
    assert "operational" in stats
    assert "evolution" in stats
    assert "regime" in stats
    assert "decision" in stats
    assert "dcel_total" in stats
    assert "target" in stats
    assert "coverage_pct" in stats
    assert stats["target"] == 800


def test_multi_category_records(tmp_path):
    """Call 5+ distinct DCEL functions → IMRAF shows records in multiple categories."""
    im = _make_fresh_imraf(tmp_path)
    import core.nexus.dcel.dcel_engine as dcel_mod
    dcel_mod._last_rl_archive_ts = 0.0

    with _patch_imraf(im):
        from core.nexus.dcel.dcel_engine import (
            archive_genome_decision,
            archive_rsi_adaptation,
            archive_lcc_event,
            archive_safe_mode_event,
            archive_regime_transition,
        )
        archive_genome_decision("T", "PROMOTED", "g1", 1.5, 1.3, 0.3, 0.55, 0.4, 80, "ok", [])
        archive_rsi_adaptation("TRENDING", "RELAX", {}, {}, 0.12)
        archive_lcc_event("PAUSE_START", 5, 30)
        archive_safe_mode_event("ACTIVATED", "test")
        archive_regime_transition("BTC", "UNKNOWN", "TRENDING", "vol", "NY")

    stats = im.get_stats()
    by_cat = stats["by_category"]
    assert by_cat.get("EVOLUTION", 0) >= 1
    assert by_cat.get("OPERATIONAL", 0) >= 1
    assert by_cat.get("REGIME", 0) >= 1

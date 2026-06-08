"""Tests for EvidenceAccumulationTracker."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.nexus.evidence_tracker.evidence_tracker import EvidenceAccumulationTracker


@pytest.fixture
def tracker(tmp_path):
    return EvidenceAccumulationTracker(data_file=tmp_path / "nexus_evidence_tracker.json")


def test_instantiates(tracker):
    assert isinstance(tracker, EvidenceAccumulationTracker)


def test_get_progress_required_keys(tracker):
    progress = tracker.get_progress()
    assert isinstance(progress, dict)
    for key in ("live_days", "target_days", "progress_pct", "milestones", "projected_activation_date"):
        assert key in progress, f"Missing key: {key}"


def test_milestones_five_entries_correct_thresholds(tracker):
    milestones = tracker.get_milestone_status()
    assert len(milestones) == 5
    expected_days = [7, 14, 30, 45, 60]
    for ms, exp in zip(milestones, expected_days):
        assert ms["days"] == exp


def test_is_threshold_met_returns_bool(tracker):
    result = tracker.is_threshold_met()
    assert isinstance(result, bool)


def test_progress_pct_is_float_in_range(tracker):
    progress = tracker.get_progress()
    pct = progress["progress_pct"]
    assert isinstance(pct, float)
    assert 0.0 <= pct


def test_evidence_velocity_non_negative(tracker):
    progress = tracker.get_progress()
    velocity = progress["evidence_velocity"]
    assert isinstance(velocity, float)
    assert velocity >= 0.0

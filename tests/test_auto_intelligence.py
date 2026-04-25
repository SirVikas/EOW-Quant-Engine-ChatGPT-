"""
FTD-030 — tests/test_auto_intelligence.py
Autonomous Background Intelligence Loop — unit tests.
"""
from __future__ import annotations
import time
import pytest

from core.intelligence.auto_intelligence_engine import (
    AutoIntelligenceEngine,
    CycleRecord,
    PHASE_IDLE, PHASE_VALIDATING, PHASE_CORRECTING, PHASE_COMPLETE, PHASE_BLOCKED,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _healthy_state():
    from core.deep_validation.contradiction_engine import ContradictionEngine
    system_state = {
        "equity":               1000.0,
        "total_trades":         40,
        "total_pnl":            150.0,
        "win_rate":             0.60,
        "current_drawdown_pct": 0.03,
        "halted":               False,
        "risk_halted":          False,
        "sharpe_ratio":         1.5,
    }
    contradiction = ContradictionEngine().run({
        **system_state,
        "total_signals":      40,
        "trades_active":      True,
        "max_drawdown_pct":   0.15,
        "kill_switch_active": False,
    })
    current_params = {
        "P7B_PERF_WIN_THRESHOLD":  0.65,
        "P7B_PERF_LOSS_THRESHOLD": 0.40,
        "P7B_EV_HIGH_THRESHOLD":   0.15,
        "P7B_EV_LOW_THRESHOLD":    0.03,
        "TR_EV_WEIGHT":            0.55,
        "ADAPTIVE_LR":             0.05,
        "ADAPTIVE_MIN_WEIGHT":     0.05,
        "ADAPTIVE_MAX_WEIGHT":     0.40,
        "KELLY_FRACTION":          0.25,
        "EXPLORE_EV_FLOOR":        0.50,
    }
    ftd028_validators = {
        "contradiction": contradiction,
        "performance":   {"passed": True,  "issue_count": 0},
        "risk":          {"passed": True,  "error_count": 0, "errors": []},
    }
    ftd028_meta = {
        "system_score":    85.0,
        "stability_score": 90.0,
        "confidence_score": 75.0,
    }
    ai_brain_score = 70.0
    halted         = False
    return system_state, current_params, ftd028_validators, ftd028_meta, ai_brain_score, halted


def _make_engine(
    n_trades=40,
    interval_min=0.0,  # 0 → no interval gate
    min_trades=30,
    min_score=55.0,
    broadcast_log=None,
):
    state_fn  = _healthy_state
    trades_fn = lambda: n_trades

    captured = broadcast_log if broadcast_log is not None else []
    def bc(payload):
        captured.append(payload)

    eng = AutoIntelligenceEngine(
        state_fn=state_fn,
        trades_fn=trades_fn,
        broadcast_fn=bc,
    )
    # Override with test-friendly settings
    eng._interval_sec   = interval_min * 60.0
    eng._min_trades     = min_trades
    eng._min_score      = min_score
    eng._post_wait_trades = 2
    eng._max_daily      = 20
    return eng, captured


# ── Tests: gate checks ────────────────────────────────────────────────────────

class TestGateChecks:
    def test_disabled_returns_skipped(self):
        eng, _ = _make_engine()
        eng.disable()
        r = eng.tick()
        assert r["action"] == "SKIPPED"
        assert "DISABLED" in r["reason"]

    def test_interval_not_elapsed_returns_skipped(self):
        eng, _ = _make_engine(interval_min=60.0)  # 60 min interval
        eng._last_run_ts = time.time()             # just ran
        r = eng.tick()
        assert r["action"] == "SKIPPED"
        assert "INTERVAL" in r["reason"]

    def test_insufficient_trades_returns_skipped(self):
        eng, _ = _make_engine(n_trades=5, min_trades=30)
        r = eng.tick()
        assert r["action"] == "SKIPPED"
        assert "INSUFFICIENT_TRADES" in r["reason"]

    def test_daily_cap_returns_skipped(self):
        eng, _ = _make_engine()
        eng._daily_cycles = eng._max_daily      # cap already reached
        r = eng.tick()
        assert r["action"] == "SKIPPED"
        assert "DAILY_CAP" in r["reason"]


# ── Tests: successful cycle execution ────────────────────────────────────────

class TestCycleExecution:
    def test_cycle_runs_when_all_gates_pass(self):
        eng, _ = _make_engine()
        r = eng.tick()
        # Should not be skipped
        assert r.get("action") != "SKIPPED"
        assert eng._cycle_num == 1

    def test_cycle_increments_counter(self):
        eng, _ = _make_engine()
        eng.tick()
        eng._last_run_ts = 0.0    # reset so it can run again
        eng.tick()
        assert eng._cycle_num == 2

    def test_daily_counter_increments(self):
        eng, _ = _make_engine()
        eng.tick()
        assert eng._daily_cycles == 1

    def test_history_populated(self):
        eng, _ = _make_engine()
        eng.tick()
        assert len(eng.history()) == 1

    def test_broadcast_fires_on_cycle(self):
        log = []
        eng, log = _make_engine(broadcast_log=log)
        eng.tick()
        assert len(log) >= 1

    def test_last_run_ts_updated(self):
        eng, _ = _make_engine()
        before = time.time()
        eng.tick()
        assert eng._last_run_ts >= before

    def test_summary_has_required_keys(self):
        eng, _ = _make_engine()
        eng.tick()
        s = eng.summary()
        for key in ("enabled", "cycles_run", "daily_cycles", "last_cycle", "last_run_ts"):
            assert key in s, f"Missing key: {key}"

    def test_cycle_returns_meta_score(self):
        eng, _ = _make_engine()
        r = eng.tick()
        assert "meta_score" in r
        assert isinstance(r["meta_score"], float)


# ── Tests: meta score gate ────────────────────────────────────────────────────

class TestMetaScoreGate:
    def test_blocked_when_score_too_low(self):
        eng, _ = _make_engine(min_score=99.0)   # impossibly high threshold
        r = eng.tick()
        # Blocked at meta score gate
        assert r.get("blocked") is True or "META_SCORE_TOO_LOW" in r.get("block_reason", "")

    def test_passes_when_score_sufficient(self):
        eng, _ = _make_engine(min_score=10.0)   # very low threshold
        r = eng.tick()
        assert r.get("blocked") is not True


# ── Tests: controls ───────────────────────────────────────────────────────────

class TestControls:
    def test_enable_disable(self):
        eng, _ = _make_engine()
        eng.disable()
        assert not eng._enabled
        eng.enable()
        assert eng._enabled

    def test_force_run_clears_interval(self):
        eng, _ = _make_engine(interval_min=999.0)
        eng._last_run_ts = time.time()
        eng.force_run()
        assert eng._last_run_ts == 0.0

    def test_reset_daily_counter(self):
        eng, _ = _make_engine()
        eng._daily_cycles = 10
        eng.reset_daily_counter()
        assert eng._daily_cycles == 0

    def test_history_capped_at_50(self):
        eng, _ = _make_engine()
        for _ in range(60):
            rec = CycleRecord(cycle_num=_, ts_start=0)
            eng._history.append(rec)
        # Trim via history()
        trimmed = eng.history(50)
        assert len(trimmed) <= 50

    def test_history_returns_dicts(self):
        eng, _ = _make_engine()
        eng.tick()
        h = eng.history()
        assert isinstance(h[0], dict)
        assert "cycle_num" in h[0]


# ── Tests: CycleRecord ────────────────────────────────────────────────────────

class TestCycleRecord:
    def test_to_dict_has_expected_keys(self):
        rec = CycleRecord(cycle_num=1, ts_start=1000)
        d = rec.to_dict()
        for key in ("cycle_num", "ts_start", "ts_end", "phase", "meta_score",
                    "blocked", "block_reason", "correction_verdict",
                    "applied_count", "rollback_count"):
            assert key in d, f"Missing key: {key}"

    def test_defaults_are_safe(self):
        rec = CycleRecord(cycle_num=1, ts_start=0)
        d = rec.to_dict()
        assert d["blocked"] is False
        assert d["meta_score"] == 0.0
        assert d["applied_count"] == 0

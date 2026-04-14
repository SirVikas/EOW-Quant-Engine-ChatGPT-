"""
FTD-REF-025 — tests/test_ws_truth.py
Tests for WsTruthEngine, ErrorRegistry, and WsStabilizer two-tier logic.

Covers:
  • WS state transitions (CONNECTED / RECONNECTING / STALE / DOWN)
  • UI label mapping
  • record_tick / reconnect attempt / reconnect success lifecycle
  • ErrorRegistry log + catalogue lookup + counts + summary
  • Default/initial mode selection
  • WsStabilizer ping-tier and reconnect-tier dispatch
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Async helper (no pytest-asyncio needed) ───────────────────────────────────
def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


from core.ws_truth_engine import (
    WsTruthEngine,
    WS_CONNECTED,
    WS_RECONNECTING,
    WS_STALE,
    WS_DOWN,
    CONNECTED_THRESH,
    RECONNECTING_THRESH,
    MAX_ATTEMPTS_FOR_STALE,
    _UI_LABELS,
)
from core.error_registry import (
    ErrorRegistry,
    ERROR_CATALOGUE,
    SEV_WARNING,
    SEV_ERROR,
    SEV_INFO,
    MAX_HISTORY,
)
from core.ws_stabilizer import (
    WsStabilizer,
    WsStats,
    WsState,
    PING_GAP_SEC,
    RECONNECT_GAP_SEC,
    PING_INTERVAL,
    MAX_BACKOFF,
    MAX_BACKOFF_SEC,
    MAX_GAP_SECONDS,
)


# ── WsTruthEngine ─────────────────────────────────────────────────────────────

class TestWsTruthEngineDefaultState:
    """Immediately after construction the engine should report CONNECTED."""

    def test_initial_state_is_connected(self):
        engine = WsTruthEngine()
        assert engine.get_state() == WS_CONNECTED

    def test_initial_ui_label_is_live(self):
        engine = WsTruthEngine()
        assert engine.get_ui_label() == _UI_LABELS[WS_CONNECTED]

    def test_snapshot_returns_correct_type(self):
        engine = WsTruthEngine()
        snap = engine.snapshot()
        assert snap.state == WS_CONNECTED
        assert snap.gap_seconds >= 0
        assert snap.reconnect_attempts == 0

    def test_to_dict_contains_required_keys(self):
        engine = WsTruthEngine()
        d = engine.to_dict()
        for key in ("state", "ui_label", "gap_seconds", "reconnect_attempts", "thresholds"):
            assert key in d, f"Missing key: {key}"
        for tkey in ("connected_thresh_sec", "reconnecting_thresh_sec", "max_attempts_for_stale"):
            assert tkey in d["thresholds"], f"Missing threshold key: {tkey}"


class TestWsTruthEngineStateTransitions:
    """State machine transitions based on tick gap and reconnect attempts."""

    def _engine_with_gap(self, gap_sec: float) -> WsTruthEngine:
        engine = WsTruthEngine()
        engine._last_tick_ts = time.time() - gap_sec
        return engine

    def test_connected_when_gap_below_thresh(self):
        engine = self._engine_with_gap(CONNECTED_THRESH - 1)
        assert engine.get_state() == WS_CONNECTED

    def test_reconnecting_when_gap_between_thresholds(self):
        engine = self._engine_with_gap(CONNECTED_THRESH + 1)
        assert engine.get_state() == WS_RECONNECTING

    def test_stale_when_gap_beyond_reconnecting_few_attempts(self):
        engine = self._engine_with_gap(RECONNECTING_THRESH + 1)
        engine._reconnect_attempts = MAX_ATTEMPTS_FOR_STALE - 1
        assert engine.get_state() == WS_STALE

    def test_down_when_gap_beyond_reconnecting_many_attempts(self):
        engine = self._engine_with_gap(RECONNECTING_THRESH + 1)
        engine._reconnect_attempts = MAX_ATTEMPTS_FOR_STALE
        assert engine.get_state() == WS_DOWN

    def test_record_tick_resets_to_connected(self):
        engine = self._engine_with_gap(RECONNECTING_THRESH + 10)
        engine._reconnect_attempts = MAX_ATTEMPTS_FOR_STALE + 2
        engine.record_tick()
        assert engine.get_state() == WS_CONNECTED
        assert engine._reconnect_attempts == 0

    def test_reconnect_attempt_increments_counter(self):
        engine = WsTruthEngine()
        engine.record_reconnect_attempt()
        engine.record_reconnect_attempt()
        assert engine._reconnect_attempts == 2

    def test_reconnect_success_resets_attempts(self):
        engine = WsTruthEngine()
        engine._reconnect_attempts = 5
        engine.record_reconnect_success()
        assert engine._reconnect_attempts == 0

    def test_reconnect_success_updates_tick_ts(self):
        engine = WsTruthEngine()
        engine._last_tick_ts = time.time() - 120
        engine.record_reconnect_success()
        assert time.time() - engine._last_tick_ts < 2


class TestWsTruthEngineUILabels:
    """UI label mapping covers all four states."""

    def test_all_states_have_ui_labels(self):
        for state in (WS_CONNECTED, WS_RECONNECTING, WS_STALE, WS_DOWN):
            assert state in _UI_LABELS
            assert _UI_LABELS[state]  # not empty

    def test_connected_label_contains_live(self):
        assert "LIVE" in _UI_LABELS[WS_CONNECTED].upper()

    def test_reconnecting_label_contains_reconnecting(self):
        assert "RECONNECTING" in _UI_LABELS[WS_RECONNECTING].upper()

    def test_stale_label_contains_delayed(self):
        assert "DELAYED" in _UI_LABELS[WS_STALE].upper()

    def test_down_label_contains_disconnected(self):
        assert "DISCONNECTED" in _UI_LABELS[WS_DOWN].upper()

    def test_get_ui_label_uses_current_state(self):
        engine = WsTruthEngine()
        engine._last_tick_ts = time.time() - (CONNECTED_THRESH + 5)
        assert engine.get_ui_label() == _UI_LABELS[WS_RECONNECTING]


# ── ErrorRegistry ─────────────────────────────────────────────────────────────

class TestErrorRegistryCatalogue:
    """Catalogue contains expected error codes and fields."""

    def test_ws_codes_present(self):
        for code in ("WS_001", "WS_002", "WS_003"):
            assert code in ERROR_CATALOGUE

    def test_data_codes_present(self):
        for code in ("DATA_001", "DATA_002"):
            assert code in ERROR_CATALOGUE

    def test_strat_codes_present(self):
        for code in ("STRAT_001", "STRAT_002"):
            assert code in ERROR_CATALOGUE

    def test_catalogue_entries_have_required_fields(self):
        required = ("type", "message", "reason", "severity", "auto_fix")
        for code, entry in ERROR_CATALOGUE.items():
            for field in required:
                assert field in entry, f"{code} missing field: {field}"

    def test_ws001_severity_is_warning(self):
        assert ERROR_CATALOGUE["WS_001"]["severity"] == SEV_WARNING

    def test_ws002_severity_is_error(self):
        assert ERROR_CATALOGUE["WS_002"]["severity"] == SEV_ERROR

    def test_data001_severity_is_info(self):
        assert ERROR_CATALOGUE["DATA_001"]["severity"] == SEV_INFO


class TestErrorRegistryLogging:
    """log() stores records and returns ErrorRecord with correct fields."""

    def test_log_known_code_returns_record(self):
        reg = ErrorRegistry()
        rec = reg.log("WS_001")
        assert rec.code == "WS_001"
        assert rec.type == ERROR_CATALOGUE["WS_001"]["type"]
        assert rec.severity == ERROR_CATALOGUE["WS_001"]["severity"]

    def test_log_stores_symbol_and_extra(self):
        reg = ErrorRegistry()
        rec = reg.log("WS_003", symbol="BTCUSDT", extra="errno=10054")
        assert rec.symbol == "BTCUSDT"
        assert rec.extra == "errno=10054"

    def test_log_unknown_code_falls_back_gracefully(self):
        reg = ErrorRegistry()
        rec = reg.log("CUSTOM_999", message="Custom error", type="Custom")
        assert rec.code == "CUSTOM_999"
        assert rec.message == "Custom error"

    def test_log_increments_count(self):
        reg = ErrorRegistry()
        reg.log("WS_001")
        reg.log("WS_001")
        reg.log("WS_002")
        counts = reg.counts()
        assert counts["WS_001"] == 2
        assert counts["WS_002"] == 1

    def test_log_sets_timestamp(self):
        reg = ErrorRegistry()
        before = time.time()
        rec = reg.log("WS_001")
        after = time.time()
        assert before <= rec.ts <= after

    def test_recent_returns_most_recent_first(self):
        reg = ErrorRegistry()
        reg.log("WS_001")
        reg.log("WS_002")
        reg.log("WS_003")
        recent = reg.recent(2)
        assert len(recent) == 2
        # Most recent first — WS_003 was logged last
        assert recent[0]["code"] == "WS_003"

    def test_recent_respects_n_limit(self):
        reg = ErrorRegistry()
        for _ in range(10):
            reg.log("WS_001")
        assert len(reg.recent(3)) == 3

    def test_summary_contains_required_keys(self):
        reg = ErrorRegistry()
        reg.log("WS_001")
        s = reg.summary()
        for key in ("total_errors", "unique_codes", "counts", "recent_5", "catalogue_size"):
            assert key in s, f"Missing key: {key}"

    def test_summary_total_errors_matches_logs(self):
        reg = ErrorRegistry()
        reg.log("WS_001")
        reg.log("WS_002")
        reg.log("DATA_001")
        assert reg.summary()["total_errors"] == 3

    def test_max_history_evicts_old_records(self):
        reg = ErrorRegistry(max_history=5)
        for i in range(10):
            reg.log("WS_001", extra=str(i))
        assert len(reg.recent(100)) == 5

    def test_caller_can_override_severity(self):
        reg = ErrorRegistry()
        rec = reg.log("WS_001", severity="CRITICAL")
        assert rec.severity == "CRITICAL"

    def test_catalogue_size_reflects_built_in_codes(self):
        reg = ErrorRegistry()
        s = reg.summary()
        assert s["catalogue_size"] == len(ERROR_CATALOGUE)


# ── WsStabilizer ─────────────────────────────────────────────────────────────

class TestWsStabilizerConstants:
    """Configuration constants match FTD-REF-025 spec."""

    def test_ping_gap(self):
        assert PING_GAP_SEC == 30

    def test_reconnect_gap(self):
        assert RECONNECT_GAP_SEC == 60

    def test_max_backoff_steps(self):
        assert MAX_BACKOFF == 3

    def test_max_backoff_sec_ceiling(self):
        assert MAX_BACKOFF_SEC == 60

    def test_backward_compat_alias(self):
        assert MAX_GAP_SECONDS == RECONNECT_GAP_SEC


class TestWsStabilizerRecordTick:
    """record_tick() resets state and clears ping_in_flight."""

    def test_record_tick_sets_connected(self):
        stab = WsStabilizer(MagicMock())
        stab._stats.state = WsState.RECONNECTING
        stab.record_tick()
        assert stab._stats.state == WsState.CONNECTED

    def test_record_tick_increments_consecutive_ok(self):
        stab = WsStabilizer(MagicMock())
        stab.record_tick()
        stab.record_tick()
        assert stab._stats.consecutive_ok == 2

    def test_record_tick_clears_ping_in_flight(self):
        stab = WsStabilizer(MagicMock())
        stab._ping_in_flight = True
        stab.record_tick()
        assert stab._ping_in_flight is False

    def test_record_tick_resets_backoff(self):
        stab = WsStabilizer(MagicMock())
        stab._backoff_step = MAX_BACKOFF
        stab.record_tick()
        assert stab._backoff_step == 0

    def test_record_tick_resets_gap_seconds(self):
        stab = WsStabilizer(MagicMock())
        stab._stats.gap_seconds = 999.0
        stab.record_tick()
        assert stab._stats.gap_seconds == 0.0


class TestWsStabilizerTierDispatch:
    """Watchdog loop sends ping at 30-60s gap and reconnects at >60s gap."""

    def _make_stab(self, gap_sec: float):
        mdp = MagicMock()
        mdp.reconnect = AsyncMock()
        mdp.ping      = AsyncMock()
        stab = WsStabilizer(mdp)
        stab._stats.last_tick_ts = time.time() - gap_sec
        stab._running = True
        return stab

    def test_ping_tier_calls_ping(self):
        stab = self._make_stab(gap_sec=PING_GAP_SEC + 5)
        stab._stats.last_ping_ts = 0
        run(stab._maybe_ping(PING_GAP_SEC + 5))
        stab._mdp.ping.assert_awaited_once()

    def test_ping_tier_skips_if_in_flight(self):
        stab = self._make_stab(gap_sec=PING_GAP_SEC + 5)
        stab._ping_in_flight = True
        run(stab._maybe_ping(PING_GAP_SEC + 5))
        stab._mdp.ping.assert_not_awaited()

    def test_ping_tier_respects_interval(self):
        stab = self._make_stab(gap_sec=PING_GAP_SEC + 5)
        stab._stats.last_ping_ts = time.time()  # just sent a ping
        run(stab._maybe_ping(PING_GAP_SEC + 5))
        stab._mdp.ping.assert_not_awaited()

    def test_reconnect_tier_calls_reconnect(self):
        stab = self._make_stab(gap_sec=RECONNECT_GAP_SEC + 5)
        run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))
        stab._mdp.reconnect.assert_awaited_once()

    def test_reconnect_tier_increments_reconnect_count(self):
        stab = self._make_stab(gap_sec=RECONNECT_GAP_SEC + 5)
        before = stab._stats.reconnect_count
        run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))
        assert stab._stats.reconnect_count == before + 1

    def test_reconnect_tier_advances_backoff_step(self):
        stab = self._make_stab(gap_sec=RECONNECT_GAP_SEC + 5)
        stab._backoff_step = 0
        run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))
        assert stab._backoff_step == 1

    def test_reconnect_tier_caps_backoff_at_max(self):
        stab = self._make_stab(gap_sec=RECONNECT_GAP_SEC + 5)
        stab._backoff_step = MAX_BACKOFF
        run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))
        assert stab._backoff_step == MAX_BACKOFF  # should not exceed cap

    def test_force_reconnect_resets_tick_ts(self):
        stab = self._make_stab(gap_sec=RECONNECT_GAP_SEC + 5)
        before = time.time()
        run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))
        assert stab._stats.last_tick_ts >= before

    def test_ping_increments_ping_sent_count(self):
        stab = self._make_stab(gap_sec=PING_GAP_SEC + 5)
        stab._stats.last_ping_ts = 0
        run(stab._maybe_ping(PING_GAP_SEC + 5))
        assert stab._stats.ping_sent_count == 1


class TestWsStabilizerBackoffComputation:
    """Backoff delays follow 2^step pattern capped at MAX_BACKOFF_SEC."""

    def test_backoff_step_0_is_1_sec(self):
        mdp = MagicMock()
        mdp.reconnect = AsyncMock()
        stab = WsStabilizer(mdp)
        stab._backoff_step = 0
        stab._stats.last_tick_ts = time.time() - (RECONNECT_GAP_SEC + 5)

        delays = []

        async def capture_sleep(n):
            delays.append(n)

        with patch("core.ws_stabilizer.asyncio.sleep", side_effect=capture_sleep):
            run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))

        # delay should be 2^0=1 + jitter (up to 30%)
        assert delays[0] >= 1.0
        assert delays[0] <= 1.0 * 1.30 + 0.01  # 30% jitter ceiling

    def test_backoff_capped_at_max_backoff_sec(self):
        mdp = MagicMock()
        mdp.reconnect = AsyncMock()
        stab = WsStabilizer(mdp)
        stab._backoff_step = 20  # way above MAX_BACKOFF
        stab._stats.last_tick_ts = time.time() - (RECONNECT_GAP_SEC + 5)

        delays = []

        async def capture_sleep(n):
            delays.append(n)

        with patch("core.ws_stabilizer.asyncio.sleep", side_effect=capture_sleep):
            run(stab._force_reconnect(RECONNECT_GAP_SEC + 5))

        # delay base should be capped at MAX_BACKOFF_SEC
        assert delays[0] <= MAX_BACKOFF_SEC * 1.31  # with max jitter

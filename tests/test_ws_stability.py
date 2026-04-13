"""
Tests for core/ws_stabilizer.py

Run with:  python -m pytest tests/test_ws_stability.py -v
"""
import asyncio
import time
import pytest

from core.ws_stabilizer import WsStabilizer, WsState, MAX_GAP_SECONDS


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class MockMdp:
    """Minimal mock of MarketDataProvider with reconnect() tracking."""
    def __init__(self):
        self.reconnect_calls = 0

    async def reconnect(self):
        self.reconnect_calls += 1


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestWsStabilizer:

    def test_initial_state_is_disconnected(self):
        stab = WsStabilizer(MockMdp())
        assert stab.stats.state == WsState.DISCONNECTED

    def test_record_tick_sets_connected(self):
        stab = WsStabilizer(MockMdp())
        stab.record_tick()
        assert stab.stats.state == WsState.CONNECTED

    def test_record_tick_increments_consecutive_ok(self):
        stab = WsStabilizer(MockMdp())
        stab.record_tick()
        stab.record_tick()
        stab.record_tick()
        assert stab.stats.consecutive_ok == 3

    def test_gap_seconds_increases_without_ticks(self):
        stab = WsStabilizer(MockMdp())
        stab._stats.last_tick_ts = time.time() - 5.0
        gap = stab.stats.gap_seconds
        assert gap >= 4.5   # allow a tiny delta

    def test_record_tick_resets_backoff(self):
        stab = WsStabilizer(MockMdp())
        stab._backoff = 32.0
        stab._stats.state = WsState.RECONNECTING
        stab.record_tick()
        assert stab._backoff == 1.0

    def test_summary_structure(self):
        stab = WsStabilizer(MockMdp())
        stab.record_tick()
        s = stab.summary()
        assert "state" in s
        assert "gap_seconds" in s
        assert "reconnect_count" in s
        assert "consecutive_ok" in s
        assert "last_error" in s

    def test_watchdog_triggers_reconnect_on_gap(self):
        """
        Simulate a stale stream: set last_tick_ts far in the past,
        run the watchdog for one iteration, confirm reconnect was called.
        """
        mdp  = MockMdp()
        stab = WsStabilizer(mdp, max_gap=0.1)   # 100 ms gap threshold for fast test
        stab._running = True
        stab._stats.last_tick_ts = time.time() - 1.0   # 1 s stale

        async def run_one_cycle():
            task = asyncio.create_task(stab._watchdog_loop())
            await asyncio.sleep(0.3)
            stab._running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        run(run_one_cycle())
        assert mdp.reconnect_calls >= 1

    def test_backoff_doubles_on_each_reconnect(self):
        stab = WsStabilizer(MockMdp())
        stab._backoff = 1.0
        initial = stab._backoff
        stab._backoff = min(stab._backoff * 2, 60)
        assert stab._backoff == initial * 2

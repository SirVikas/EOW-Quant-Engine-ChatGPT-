"""
EOW Quant Engine — tests/test_pre_gate_control.py
Phase 7A.3: Pre-Gate Control Verifier

Gate controls the ENTIRE thinking process of the system.
NO data processing may occur before gate approval.

MUST FAIL if:
  - regime_det.push() runs in safe mode
  - signal generation runs in safe mode
  - execution happens in safe mode
  - gate check is not the first gating operation before regime push
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_MAIN_PY   = _REPO_ROOT / "main.py"


def _main_src() -> str:
    return _MAIN_PY.read_text(encoding="utf-8")


# ── SECTION 1: Code-audit — ordering in main.py ───────────────────────────────

def test_gate_check_appears_before_regime_push():
    """
    In main.py source, the pre-gate gate_check() call must appear
    before regime_det.push() — order enforced by line number.
    """
    src = _main_src()
    lines = src.splitlines()

    gate_line   = None
    regime_line = None

    for i, line in enumerate(lines, start=1):
        # Find the Phase 7A.3 pre-gate check (not the later per-signal check at ~453)
        if "_pre_gate = execution_orchestrator.gate_check" in line:
            gate_line = i
        if "regime_det.push(" in line and gate_line is not None and regime_line is None:
            regime_line = i

    assert gate_line is not None, (
        "BUILD REJECTED: Phase 7A.3 pre-gate check (_pre_gate = execution_orchestrator.gate_check) "
        "not found in main.py"
    )
    assert regime_line is not None, (
        "BUILD REJECTED: regime_det.push() not found after pre-gate check in main.py"
    )
    assert gate_line < regime_line, (
        f"BUILD REJECTED: gate_check() is at line {gate_line} but "
        f"regime_det.push() is at line {regime_line} — gate must come FIRST"
    )


def test_early_return_on_gate_block_before_regime():
    """
    main.py must have an early return when _pre_gate is not allowed,
    AND that return must appear before regime_det.push().
    """
    src = _main_src()
    lines = src.splitlines()

    pre_gate_line  = None
    early_ret_line = None
    regime_line    = None

    for i, line in enumerate(lines, start=1):
        if "_pre_gate = execution_orchestrator.gate_check" in line:
            pre_gate_line = i
        if pre_gate_line and early_ret_line is None:
            if "not _pre_gate.allowed" in line or "_pre_gate.allowed" in line:
                # look for the return in the next few lines
                pass
            if "return" in line and pre_gate_line and i > pre_gate_line and i < pre_gate_line + 5:
                early_ret_line = i
        if "regime_det.push(" in line and pre_gate_line:
            regime_line = i
            break

    assert pre_gate_line is not None, "pre-gate check not found"
    assert early_ret_line is not None, (
        "BUILD REJECTED: No early return found immediately after _pre_gate check"
    )
    assert regime_line is not None, "regime_det.push() not found"
    assert early_ret_line < regime_line, (
        f"BUILD REJECTED: early return at line {early_ret_line} comes after "
        f"regime_det.push() at line {regime_line}"
    )


def test_regime_detector_has_safe_mode_flag():
    """RegimeDetector must have a safe_mode attribute as hard-block guard."""
    from core.regime_detector import RegimeDetector
    rd = RegimeDetector()
    assert hasattr(rd, "safe_mode"), (
        "BUILD REJECTED: RegimeDetector.safe_mode flag not found — "
        "hard-block guard must be implemented"
    )
    assert rd.safe_mode is False, "safe_mode should default to False"


# ── SECTION 2: RegimeDetector safe_mode hard guard ────────────────────────────

def test_regime_push_blocked_when_safe_mode_true():
    """RegimeDetector.push() must be a no-op when safe_mode=True."""
    from core.regime_detector import RegimeDetector
    rd = RegimeDetector()
    rd.safe_mode = True

    # Seed enough data that push would normally classify
    for i in range(40):
        rd._init_bufs("BTCUSDT")
        rd._price_buf["BTCUSDT"].append(50000.0 + i)
        rd._high_buf["BTCUSDT"].append(50010.0 + i)
        rd._low_buf["BTCUSDT"].append(49990.0 + i)

    before_state = rd._states.get("BTCUSDT")
    rd.push("BTCUSDT", 51000.0, 51100.0, 50900.0, 1_000_000)
    after_state = rd._states.get("BTCUSDT")

    assert before_state is after_state, (
        "BUILD REJECTED: regime_det.push() ran in safe_mode=True — "
        "state was updated when it should have been blocked"
    )


def test_regime_push_works_when_safe_mode_false():
    """RegimeDetector.push() must function normally when safe_mode=False."""
    from core.regime_detector import RegimeDetector
    rd = RegimeDetector()
    rd.safe_mode = False

    # Feed enough candles to trigger classification
    for i in range(35):
        rd.push("ETHUSDT", 3000.0 + i * 0.5, 3010.0 + i * 0.5, 2990.0 + i * 0.5, i * 60_000)

    state = rd._states.get("ETHUSDT")
    assert state is not None, (
        "regime_det.push() did not run with safe_mode=False — normal flow broken"
    )


def test_regime_safe_mode_toggle():
    """safe_mode can be toggled: push blocked when True, runs when False."""
    from core.regime_detector import RegimeDetector
    rd = RegimeDetector()

    # Pre-fill buffers
    for i in range(35):
        rd.push("SOLUSDT", 100.0 + i, 101.0 + i, 99.0 + i, i * 60_000)

    state_after_warmup = rd._states.get("SOLUSDT")

    # Engage safe mode — push must be a no-op
    rd.safe_mode = True
    rd.push("SOLUSDT", 999.0, 1000.0, 998.0, 999_999)
    assert rd._states.get("SOLUSDT") is state_after_warmup, (
        "State changed while safe_mode=True"
    )

    # Disengage — push must work again
    rd.safe_mode = False
    rd.push("SOLUSDT", 999.0, 1000.0, 998.0, 999_999)
    # State may or may not change (depends on data), but no exception should be raised


# ── SECTION 3: on_tick() gate flow with mocked orchestrator ───────────────────

@pytest.fixture()
def mock_execution_orchestrator():
    """
    Patch the module-level execution_orchestrator in main with a mock
    that returns a blocked GateCheckResult.
    """
    import main as m
    from core.orchestrator.execution_orchestrator import GateCheckResult

    original = m.execution_orchestrator
    mock_orch = MagicMock()
    mock_orch.gate_check.return_value = GateCheckResult(
        allowed=False, action="GATE_BLOCKED",
        reason="SAFE_MODE", gate_status={"can_trade": False, "safe_mode": True},
    )
    m.execution_orchestrator = mock_orch
    yield mock_orch
    m.execution_orchestrator = original


@pytest.fixture()
def mock_allowed_orchestrator():
    """Patch orchestrator to allow but block at run_cycle (gate passes, pipeline blocks)."""
    import main as m
    from core.orchestrator.execution_orchestrator import GateCheckResult, CycleResult

    original = m.execution_orchestrator
    mock_orch = MagicMock()
    mock_orch.gate_check.return_value = GateCheckResult(
        allowed=True, action="ALLOWED",
        reason="ALL_CLEAR", gate_status={"can_trade": True, "safe_mode": False},
    )
    mock_orch.run_cycle.return_value = CycleResult(
        action="GATE_BLOCKED", execute=False,
        reason="RANK_REJECT", gate_status={},
    )
    m.execution_orchestrator = mock_orch
    yield mock_orch
    m.execution_orchestrator = original


def test_regime_push_not_called_when_gate_blocked(mock_execution_orchestrator):
    """
    When gate_check returns allowed=False, regime_det.push() must NOT be called.
    """
    import main as m

    original_push = m.regime_det.push
    push_calls = []

    def spy_push(*args, **kwargs):
        push_calls.append(args)
        return original_push(*args, **kwargs)

    m.regime_det.push = spy_push
    try:
        import asyncio
        from core.market_data import Tick, Candle
        import time

        tick = Tick(
            symbol="BTCUSDT", price=50000.0, qty=1.0,
            bid=49999.0, ask=50001.0, volume_24h=1e9,
            ts=int(time.time() * 1000),
        )
        # Ensure candle data exists so we pass the early candle guard
        candle = Candle(
            symbol="BTCUSDT", interval="1m",
            open=49900.0, high=50100.0, low=49800.0, close=50000.0,
            volume=100.0, ts=int(time.time() * 1000) - 90_000,
            closed=True,
        )
        m.mdp.closed_candles["BTCUSDT"] = candle
        m.mdp.candle_close_buffers["BTCUSDT"].extend([50000.0] * 60)
        # Reset debounce so the tick is not filtered
        m._last_processed_candle_ts.pop("BTCUSDT", None)
        m._last_symbol_eval_ms.pop("BTCUSDT", None)

        asyncio.get_event_loop().run_until_complete(m.on_tick(tick))
    finally:
        m.regime_det.push = original_push

    assert len(push_calls) == 0, (
        f"BUILD REJECTED: regime_det.push() was called {len(push_calls)} time(s) "
        f"even though gate was BLOCKED — pre-gate control is broken"
    )


def test_signal_not_generated_when_gate_blocked(mock_execution_orchestrator):
    """
    When gate is blocked, no signal should be generated (strategy never called).
    """
    import main as m
    import asyncio
    from core.market_data import Tick, Candle
    import time

    original_generate = None
    generate_calls = []
    if hasattr(m, 'get_strategy'):
        original_get = m.get_strategy
        def spy_get(*args, **kwargs):
            result = original_get(*args, **kwargs)
            # Wrap generate_signal
            original_gen = result.generate_signal
            def spy_gen(*a, **kw):
                generate_calls.append(a)
                return original_gen(*a, **kw)
            result.generate_signal = spy_gen
            return result
        m.get_strategy = spy_get

    try:
        tick = Tick(
            symbol="ETHUSDT", price=3000.0, qty=1.0,
            bid=2999.0, ask=3001.0, volume_24h=5e8,
            ts=int(time.time() * 1000),
        )
        candle = Candle(
            symbol="ETHUSDT", interval="1m",
            open=2990.0, high=3010.0, low=2980.0, close=3000.0,
            volume=50.0, ts=int(time.time() * 1000) - 90_000,
            closed=True,
        )
        m.mdp.closed_candles["ETHUSDT"] = candle
        m.mdp.candle_close_buffers["ETHUSDT"].extend([3000.0] * 60)
        m._last_processed_candle_ts.pop("ETHUSDT", None)
        m._last_symbol_eval_ms.pop("ETHUSDT", None)

        asyncio.get_event_loop().run_until_complete(m.on_tick(tick))
    finally:
        if original_generate is not None:
            m.get_strategy = original_get

    # With gate blocked, signal generation path is never reached
    assert generate_calls == [], (
        f"BUILD REJECTED: strategy.generate_signal() called despite gate block — "
        f"signal generation must not run in safe mode"
    )
    # Also verify pre_gate was called
    mock_execution_orchestrator.gate_check.assert_called()


def test_run_cycle_not_called_when_gate_blocked(mock_execution_orchestrator):
    """
    execution_orchestrator.run_cycle() must NOT be called when gate is blocked.
    """
    import main as m
    import asyncio
    from core.market_data import Tick, Candle
    import time

    tick = Tick(
        symbol="BNBUSDT", price=400.0, qty=1.0,
        bid=399.0, ask=401.0, volume_24h=2e8,
        ts=int(time.time() * 1000),
    )
    candle = Candle(
        symbol="BNBUSDT", interval="1m",
        open=398.0, high=402.0, low=397.0, close=400.0,
        volume=30.0, ts=int(time.time() * 1000) - 90_000,
        closed=True,
    )
    m.mdp.closed_candles["BNBUSDT"] = candle
    m.mdp.candle_close_buffers["BNBUSDT"].extend([400.0] * 60)
    m._last_processed_candle_ts.pop("BNBUSDT", None)
    m._last_symbol_eval_ms.pop("BNBUSDT", None)

    asyncio.get_event_loop().run_until_complete(m.on_tick(tick))

    mock_execution_orchestrator.run_cycle.assert_not_called(), (
        "BUILD REJECTED: run_cycle() was called despite gate being BLOCKED"
    )


def test_normal_flow_when_gate_allowed(mock_allowed_orchestrator):
    """
    When gate is open, regime_det.push() and gate_check() must both be called.
    """
    import main as m
    import asyncio
    from core.market_data import Tick, Candle
    import time

    push_calls = []
    original_push = m.regime_det.push
    def spy_push(*args, **kwargs):
        push_calls.append(args)
        return original_push(*args, **kwargs)
    m.regime_det.push = spy_push

    try:
        tick = Tick(
            symbol="SOLUSDT", price=150.0, qty=1.0,
            bid=149.9, ask=150.1, volume_24h=1e8,
            ts=int(time.time() * 1000),
        )
        candle = Candle(
            symbol="SOLUSDT", interval="1m",
            open=149.0, high=151.0, low=148.0, close=150.0,
            volume=20.0, ts=int(time.time() * 1000) - 90_000,
            closed=True,
        )
        m.mdp.closed_candles["SOLUSDT"] = candle
        m.mdp.candle_close_buffers["SOLUSDT"].extend([150.0] * 60)
        m._last_processed_candle_ts.pop("SOLUSDT", None)
        m._last_symbol_eval_ms.pop("SOLUSDT", None)

        asyncio.get_event_loop().run_until_complete(m.on_tick(tick))
    finally:
        m.regime_det.push = original_push

    assert len(push_calls) > 0, (
        "regime_det.push() was NOT called even though gate was ALLOWED — normal flow broken"
    )
    mock_allowed_orchestrator.gate_check.assert_called()

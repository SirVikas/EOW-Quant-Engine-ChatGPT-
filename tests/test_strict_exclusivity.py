"""
EOW Quant Engine — tests/test_strict_exclusivity.py
Phase 7A.2: Strict Execution Enforcement Verifier

BUILD IS REJECTED if any of these tests fail:
  - scan_markets() detected in main.py
  - legacy scanning loop detected in main.py
  - legacy infinite execution loop detected in main.py
  - regime_detector.push() inside a while-True loop in main.py
  - direct execute_trade() / place_order() calls in main.py
  - ExecutionLock missing or broken
  - enforce_no_scan() missing or broken
  - Orchestrator not using ExecutionLock
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── Paths ─────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
_MAIN_PY   = _REPO_ROOT / "main.py"


def _main_src() -> str:
    return _MAIN_PY.read_text(encoding="utf-8")


# ── LAYER 1: main.py code audit ───────────────────────────────────────────────

def test_no_scan_markets_in_main():
    """scan_markets() must not exist anywhere in main.py."""
    assert "scan_markets" not in _main_src(), (
        "BUILD REJECTED: scan_markets() found in main.py — "
        "legacy scan loop must be deleted"
    )


def test_no_legacy_for_symbol_loop():
    """Legacy 'for symbol in symbols:' scan loop must not exist."""
    assert "for symbol in symbols" not in _main_src(), (
        "BUILD REJECTED: legacy scanning loop 'for symbol in symbols' "
        "found in main.py"
    )


def test_no_legacy_scan_while_loop():
    """while True: scan_markets() pattern must not exist."""
    src = _main_src()
    # Both compact and indented variants
    assert "while True:\n    scan_markets" not in src, (
        "BUILD REJECTED: legacy while-True scan loop found in main.py"
    )
    assert "while True:\n        scan_markets" not in src, (
        "BUILD REJECTED: legacy while-True scan loop found in main.py"
    )


def test_no_direct_execute_trade():
    """execute_trade() must not be called directly in main.py."""
    assert "execute_trade(" not in _main_src(), (
        "BUILD REJECTED: direct execute_trade() found in main.py — "
        "all execution must flow through the orchestrator"
    )


def test_no_direct_place_order():
    """place_order() must not be called directly in main.py."""
    assert "place_order(" not in _main_src(), (
        "BUILD REJECTED: direct place_order() found in main.py — "
        "all execution must flow through the orchestrator"
    )


def test_no_regime_push_in_while_true_loop():
    """regime_detector.push() must not appear inside a standalone while-True loop."""
    src = _main_src()
    # Find every while True: block and verify none contain regime_det.push
    # Strategy: look for 'while True:' followed by regime push before a dedent/return
    found = re.search(
        r"while\s+True\s*:.*?regime_det\.push",
        src,
        re.DOTALL,
    )
    assert found is None, (
        "BUILD REJECTED: regime_detector.push() detected inside a while-True loop "
        "in main.py — standalone regime auto-push loop must be deleted"
    )


def test_orchestrator_is_only_execution_path():
    """run_cycle() must be called in main.py (orchestrator is wired in)."""
    src = _main_src()
    assert "execution_orchestrator" in src, (
        "BUILD REJECTED: execution_orchestrator not found in main.py — "
        "orchestrator must be the single execution authority"
    )
    assert "run_cycle(" in src, (
        "BUILD REJECTED: run_cycle() not called in main.py — "
        "all trade execution must go through orchestrator.run_cycle()"
    )


# ── LAYER 2: ExecutionLock unit tests ─────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_lock():
    """Ensure ExecutionLock is always released between tests."""
    from core.orchestrator.execution_lock import ExecutionLock
    ExecutionLock._active = False
    yield
    ExecutionLock._active = False


def test_execution_lock_exists():
    """ExecutionLock must exist with acquire() and release() class methods."""
    from core.orchestrator.execution_lock import ExecutionLock
    assert hasattr(ExecutionLock, "acquire"), "ExecutionLock.acquire() missing"
    assert hasattr(ExecutionLock, "release"), "ExecutionLock.release() missing"
    assert callable(ExecutionLock.acquire)
    assert callable(ExecutionLock.release)


def test_execution_lock_starts_inactive():
    from core.orchestrator.execution_lock import ExecutionLock
    assert ExecutionLock._active is False


def test_execution_lock_acquire_sets_active():
    from core.orchestrator.execution_lock import ExecutionLock
    ExecutionLock.acquire()
    assert ExecutionLock._active is True


def test_execution_lock_release_clears_active():
    from core.orchestrator.execution_lock import ExecutionLock
    ExecutionLock.acquire()
    ExecutionLock.release()
    assert ExecutionLock._active is False


def test_execution_lock_double_acquire_crashes():
    """Second acquire() MUST raise RuntimeError — system must crash, not silently bypass."""
    from core.orchestrator.execution_lock import ExecutionLock
    ExecutionLock.acquire()
    with pytest.raises(RuntimeError, match="CRITICAL: Multiple execution loops detected"):
        ExecutionLock.acquire()


def test_execution_lock_release_after_double_acquire_crash():
    """Lock must remain acquirable after release following a crash scenario."""
    from core.orchestrator.execution_lock import ExecutionLock
    ExecutionLock.acquire()
    with pytest.raises(RuntimeError):
        ExecutionLock.acquire()
    ExecutionLock.release()
    # Should be acquirable again after release
    ExecutionLock.acquire()
    assert ExecutionLock._active is True


# ── LAYER 3: Orchestrator uses ExecutionLock ──────────────────────────────────

@pytest.fixture(autouse=True)
def reset_authority():
    from core.orchestrator.execution_orchestrator import ExecutionOrchestrator
    ExecutionOrchestrator._reset_authority()
    yield
    ExecutionOrchestrator._reset_authority()


def _blocked_gate_orch() -> "ExecutionOrchestrator":
    """Return a non-exclusive orchestrator whose gate always blocks."""
    from core.orchestrator.execution_orchestrator import ExecutionOrchestrator
    orch = ExecutionOrchestrator(exclusive=False)
    orch._gate = MagicMock()
    orch._gate.evaluate.return_value = {
        "can_trade": False, "safe_mode": False, "reason": "TEST_BLOCKED"
    }
    orch._sme = MagicMock()
    return orch


def _tick_ctx() -> "TickContext":
    from core.orchestrator.execution_orchestrator import TickContext
    return TickContext(
        symbol="BTCUSDT", price=50000.0, regime="TRENDING",
        strategy="TrendFollowing", ev=2.0, trade_score=0.8,
        volume_ratio=1.2, equity=10000.0, base_risk_usdt=100.0,
        upstream_mult=1.0, indicator_ok=True, data_fresh=True,
    )


def test_run_cycle_releases_lock_on_gate_block():
    """ExecutionLock must be released even when gate blocks early."""
    from core.orchestrator.execution_lock import ExecutionLock
    orch = _blocked_gate_orch()

    assert ExecutionLock._active is False
    result = orch.run_cycle(_tick_ctx())
    assert result.execute is False
    assert ExecutionLock._active is False, (
        "ExecutionLock was not released after early gate block"
    )


def test_run_cycle_lock_held_during_execution():
    """ExecutionLock must be active while run_cycle is executing."""
    from core.orchestrator.execution_lock import ExecutionLock
    from core.orchestrator.execution_orchestrator import ExecutionOrchestrator

    captured_states = []
    original_inner = ExecutionOrchestrator._run_cycle_inner

    def spy_inner(self, ctx):
        captured_states.append(ExecutionLock._active)
        return original_inner(self, ctx)

    ExecutionOrchestrator._run_cycle_inner = spy_inner
    try:
        orch = _blocked_gate_orch()
        orch.run_cycle(_tick_ctx())
    finally:
        ExecutionOrchestrator._run_cycle_inner = original_inner

    assert len(captured_states) > 0
    assert captured_states[0] is True, (
        "ExecutionLock was not acquired before _run_cycle_inner was called"
    )


def test_run_cycle_lock_released_after_execution():
    """ExecutionLock must be False after run_cycle returns normally."""
    from core.orchestrator.execution_lock import ExecutionLock
    orch = _blocked_gate_orch()
    orch.run_cycle(_tick_ctx())
    assert ExecutionLock._active is False


# ── LAYER 4: ScanController.enforce_no_scan() ─────────────────────────────────

def test_enforce_no_scan_raises_on_safe_mode():
    """enforce_no_scan() must crash if safe_mode is True."""
    from core.profit.scan_controller import ScanController
    ctrl = ScanController()
    with pytest.raises(RuntimeError, match="CRITICAL: Scan attempted in SAFE MODE"):
        ctrl.enforce_no_scan({"can_trade": True, "safe_mode": True, "reason": "SAFE_MODE"})


def test_enforce_no_scan_raises_when_cannot_trade():
    """enforce_no_scan() must crash if can_trade is False."""
    from core.profit.scan_controller import ScanController
    ctrl = ScanController()
    with pytest.raises(RuntimeError, match="CRITICAL: Scan attempted in SAFE MODE"):
        ctrl.enforce_no_scan({"can_trade": False, "safe_mode": False, "reason": "WS_DOWN"})


def test_enforce_no_scan_passes_when_gate_clear():
    """enforce_no_scan() must NOT raise when gate is clear."""
    from core.profit.scan_controller import ScanController
    ctrl = ScanController()
    ctrl.enforce_no_scan({"can_trade": True, "safe_mode": False, "reason": "ALL_CLEAR"})


def test_enforce_no_scan_raises_both_blocked():
    """enforce_no_scan() must crash when both can_trade=False and safe_mode=True."""
    from core.profit.scan_controller import ScanController
    ctrl = ScanController()
    with pytest.raises(RuntimeError):
        ctrl.enforce_no_scan({"can_trade": False, "safe_mode": True, "reason": "FULL_STOP"})


# ── LAYER 5: ExecutionLock exported from package ──────────────────────────────

def test_execution_lock_importable_from_orchestrator_package():
    """ExecutionLock must be importable from core.orchestrator."""
    from core.orchestrator import ExecutionLock  # noqa: F401
    assert ExecutionLock is not None


def test_execution_lock_importable_from_module():
    """ExecutionLock must be importable from core.orchestrator.execution_lock."""
    from core.orchestrator.execution_lock import ExecutionLock  # noqa: F401
    assert ExecutionLock is not None

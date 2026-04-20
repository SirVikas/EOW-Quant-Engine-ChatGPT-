"""
EOW Quant Engine — tests/test_phase6_6_gating_system.py
Phase 6.6: Hard Gating + Safety Enforcement — Integration Tests

Coverage:
    1. HardStartValidator blocks boot when indicators missing
    2. HardStartValidator passes when all conditions met
    3. SafeModeEngine activates on WS failure (gate blocked → safe mode)
    4. No trades allowed when GlobalGate returns can_trade=False
    5. PreTradeGate blocks when safe mode is active
    6. PreTradeGate allows when all conditions clear
    7. Gate logger records events correctly
    8. SafeModeEngine auto-recovery when deploy score recovers
    9. SafeModeEngine BLOCKED state cannot auto-recover
   10. GlobalGateController.evaluate() returns spec-compliant dict
"""
from __future__ import annotations

import pytest

from core.gating.gate_logger import GatingLogger
from core.gating.safe_mode_engine import SafeModeEngine, SafeMode
from core.gating.global_gate_controller import GlobalGateController
from core.gating.hard_start_validator import HardStartValidator
from core.gating.pre_trade_gate import PreTradeGate


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sme():
    return SafeModeEngine()


@pytest.fixture
def logger():
    return GatingLogger()


@pytest.fixture
def gate(sme):
    return GlobalGateController(safe_mode=sme)


@pytest.fixture
def ptg(sme):
    return PreTradeGate(safe_mode=sme)


@pytest.fixture
def hsv():
    return HardStartValidator()


# ── 1. HardStartValidator blocks boot when indicators not ready ───────────────

def test_hard_start_blocks_on_missing_indicators(hsv):
    with pytest.raises(RuntimeError, match="HARD BLOCK"):
        hsv.run(
            candle_count=30,
            indicator_ok=False,
            ws_reachable=True,
        )


def test_hard_start_blocks_on_insufficient_candles(hsv):
    with pytest.raises(RuntimeError, match="HARD BLOCK"):
        hsv.run(
            candle_count=5,
            indicator_ok=True,
            ws_reachable=True,
        )


def test_hard_start_blocks_on_ws_unreachable(hsv):
    with pytest.raises(RuntimeError, match="HARD BLOCK"):
        hsv.run(
            candle_count=30,
            indicator_ok=True,
            ws_reachable=False,
        )


# ── 2. HardStartValidator passes when all conditions met ─────────────────────

def test_hard_start_passes_when_all_clear(hsv):
    result = hsv.run(
        candle_count=30,
        indicator_ok=True,
        ws_reachable=True,
    )
    assert result.ok is True
    assert result.failures == []


def test_hard_start_collects_all_failures(hsv):
    with pytest.raises(RuntimeError):
        hsv.run(
            candle_count=0,
            indicator_ok=False,
            ws_reachable=False,
        )


def test_hard_start_extra_checks_failure(hsv):
    with pytest.raises(RuntimeError, match="HARD BLOCK"):
        hsv.run(
            candle_count=30,
            indicator_ok=True,
            ws_reachable=True,
            extra_checks={"REDIS_ONLINE": False},
        )


# ── 3. GlobalGateController triggers safe mode on WS failure ─────────────────

def test_gate_activates_safe_mode_on_ws_failure(sme):
    gate = GlobalGateController(
        ws_score_fn=lambda: 10.0,   # well below GGL_WS_MIN_SCORE=50
        safe_mode=sme,
    )
    result = gate.evaluate()
    assert result["can_trade"] is False
    assert sme.mode == SafeMode.SAFE
    assert result["safe_mode"] is True


def test_gate_activates_safe_mode_on_deploy_failure(sme):
    gate = GlobalGateController(
        deploy_score_fn=lambda: 20.0,  # below GGL_DEPLOY_MIN_SCORE=70
        safe_mode=sme,
    )
    result = gate.evaluate()
    assert result["can_trade"] is False
    assert sme.mode == SafeMode.SAFE


# ── 4. No trades when GlobalGate returns can_trade=False ─────────────────────

def test_gate_blocks_trade_on_data_not_fresh(sme):
    gate = GlobalGateController(
        data_fresh_fn=lambda: False,
        safe_mode=sme,
    )
    result = gate.evaluate()
    assert result["can_trade"] is False
    assert "DATA_NOT_FRESH" in result["reason"]


def test_gate_blocks_trade_on_indicators_not_ready(sme):
    gate = GlobalGateController(
        indicator_ready_fn=lambda: False,
        safe_mode=sme,
    )
    result = gate.evaluate()
    assert result["can_trade"] is False
    assert "INDICATOR_NOT_READY" in result["reason"]


def test_gate_allows_trade_when_all_clear(sme):
    gate = GlobalGateController(
        indicator_ready_fn=lambda: True,
        ws_score_fn=lambda: 100.0,
        data_fresh_fn=lambda: True,
        deploy_score_fn=lambda: 100.0,
        safe_mode=sme,
    )
    result = gate.evaluate()
    assert result["can_trade"] is True
    assert result["reason"] == "ALL_CLEAR"
    assert result["safe_mode"] is False


# ── 5. PreTradeGate blocks when safe mode active ──────────────────────────────

def test_ptg_blocks_when_safe_mode_active(sme, ptg):
    sme.activate("TEST_REASON")
    gate_status = {"can_trade": True, "reason": "ALL_CLEAR", "safe_mode": True}
    result = ptg.check(gate_status)
    assert result["allowed"] is False
    assert "SAFE_MODE_ACTIVE" in result["reason"]


def test_ptg_blocks_when_gate_says_no_trade(ptg):
    gate_status = {"can_trade": False, "reason": "WS_UNSTABLE", "safe_mode": True}
    result = ptg.check(gate_status)
    assert result["allowed"] is False
    assert result["reason"] == "WS_UNSTABLE"


def test_ptg_blocks_when_indicators_not_ready(sme, ptg):
    gate_status = {"can_trade": True, "reason": "ALL_CLEAR", "safe_mode": False}
    result = ptg.check(gate_status, indicator_ok=False)
    assert result["allowed"] is False
    assert result["reason"] == "INDICATORS_NOT_READY"


def test_ptg_blocks_when_data_not_fresh(sme, ptg):
    gate_status = {"can_trade": True, "reason": "ALL_CLEAR", "safe_mode": False}
    result = ptg.check(gate_status, data_fresh=False)
    assert result["allowed"] is False
    assert result["reason"] == "DATA_NOT_FRESH"


# ── 6. PreTradeGate allows when all conditions clear ─────────────────────────

def test_ptg_allows_when_all_clear(sme, ptg):
    gate_status = {"can_trade": True, "reason": "ALL_CLEAR", "safe_mode": False}
    result = ptg.check(gate_status, indicator_ok=True, data_fresh=True)
    assert result["allowed"] is True
    assert result["reason"] == "OK"
    assert result["managed"] is True


# ── 7. Gate logger records events ────────────────────────────────────────────

def test_gate_logger_records_blocked(logger):
    logger.blocked(reason="TEST_BLOCK", context="BTCUSDT/TrendFollowing")
    stats = logger.stats()
    assert stats["total_blocked"] == 1
    assert stats["by_reason"]["TEST_BLOCK"] == 1


def test_gate_logger_records_allowed(logger):
    logger.allowed(context="ETHUSDT")
    stats = logger.stats()
    assert stats["total_allowed"] == 1


def test_gate_logger_records_safe_mode(logger):
    logger.safe_mode(reason="WS_UNSTABLE")
    stats = logger.stats()
    assert stats["safe_mode_count"] == 1


def test_gate_logger_recent_blocks(logger):
    logger.blocked(reason="BLOCK_1")
    logger.allowed()
    logger.blocked(reason="BLOCK_2")
    blocks = logger.recent_blocks(n=5)
    assert len(blocks) == 2
    reasons = [b.reason for b in blocks]
    assert "BLOCK_1" in reasons
    assert "BLOCK_2" in reasons


def test_gate_logger_boot_events(logger):
    logger.boot_ok(stage="CANDLE_CHECK")
    logger.boot_fail(stage="WS_CHECK", detail="unreachable")
    recent = logger.recent(n=10)
    events = [e.event for e in recent]
    assert "BOOT_OK" in events
    assert "BOOT_FAIL" in events


# ── 8. SafeModeEngine auto-recovery ──────────────────────────────────────────

def test_safe_mode_auto_recovery(sme, monkeypatch):
    sme.activate("WS_UNSTABLE")
    assert sme.mode == SafeMode.SAFE

    monkeypatch.setattr(sme, "_last_resume_check", 0.0)
    from config import cfg
    recovered = sme.check_recovery(deploy_score=cfg.SMC_MIN_SCORE_RESUME + 1.0)
    assert recovered is True
    assert sme.mode == SafeMode.NORMAL


def test_safe_mode_no_recovery_when_score_low(sme, monkeypatch):
    sme.activate("DEPLOY_LOW")
    monkeypatch.setattr(sme, "_last_resume_check", 0.0)
    from config import cfg
    recovered = sme.check_recovery(deploy_score=cfg.SMC_MIN_SCORE_RESUME - 10.0)
    assert recovered is False
    assert sme.mode == SafeMode.SAFE


# ── 9. BLOCKED state cannot auto-recover ─────────────────────────────────────

def test_safe_mode_blocked_no_auto_recovery(sme, monkeypatch):
    sme.activate_blocked("CATASTROPHIC_FAILURE")
    assert sme.mode == SafeMode.BLOCKED

    monkeypatch.setattr(sme, "_last_resume_check", 0.0)
    recovered = sme.check_recovery(deploy_score=100.0)
    assert recovered is False
    assert sme.mode == SafeMode.BLOCKED


def test_safe_mode_blocked_requires_force_reset(sme):
    sme.activate_blocked("CRITICAL")
    sme.deactivate()   # should be silently ignored
    assert sme.mode == SafeMode.BLOCKED

    sme.force_reset("OPERATOR")
    assert sme.mode == SafeMode.NORMAL


def test_safe_mode_activate_ignored_when_already_blocked(sme):
    sme.activate_blocked("HARD_FAIL")
    sme.activate("SOFT_FAIL")   # should not downgrade to SAFE
    assert sme.mode == SafeMode.BLOCKED


# ── 10. GlobalGateController.evaluate() spec compliance ──────────────────────

def test_gate_evaluate_returns_spec_dict(gate):
    result = gate.evaluate()
    assert "can_trade" in result
    assert "reason" in result
    assert "safe_mode" in result
    assert isinstance(result["can_trade"], bool)
    assert isinstance(result["reason"], str)
    assert isinstance(result["safe_mode"], bool)


def test_gate_evaluate_multiple_failures_pipe_delimited(sme):
    gate = GlobalGateController(
        indicator_ready_fn=lambda: False,
        ws_score_fn=lambda: 0.0,
        data_fresh_fn=lambda: False,
        deploy_score_fn=lambda: 0.0,
        safe_mode=sme,
    )
    result = gate.evaluate()
    assert result["can_trade"] is False
    parts = result["reason"].split(" | ")
    assert len(parts) >= 2


def test_gate_force_block(gate):
    gate.force_block("EMERGENCY_STOP")
    assert gate.can_trade() is False
    assert gate._last_result["can_trade"] is False
    assert "FORCED_BLOCK" in gate._last_result["reason"]


def test_gate_summary_structure(gate):
    gate.evaluate()
    s = gate.summary()
    assert s["module"] == "GLOBAL_GATE_CONTROLLER"
    assert s["phase"] == "6.6"
    assert "thresholds" in s
    assert "total_evals" in s

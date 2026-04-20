"""
EOW Quant Engine — Phase 6.6 Verifier
Tests: GateLogger, GlobalGateController, HardStartValidator,
       SafeModeEnforcer, PreTradeGate
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.gate_logger import GateLogger, GATE_ALLOWED, GATE_BLOCKED, GATE_SAFE_MODE, GATE_BOOT_FAIL, GATE_BOOT_OK
from core.global_gate import GlobalGateController, GateResult
from core.hard_start import HardStartValidator
from core.safe_mode_enforcer import SafeModeEnforcer
from core.pre_trade_gate import PreTradeGate, TradePermission
from core.safe_mode import SafeModeController
from config import cfg


# ═══════════════════════════════════════════════════════════════════════════════
# GateLogger
# ═══════════════════════════════════════════════════════════════════════════════

class TestGateLogger:

    def setup_method(self):
        self.gl = GateLogger()

    def test_log_blocked_recorded(self):
        self.gl.log_blocked("INDICATOR_NOT_READY", context="BTCUSDT")
        events = self.gl.recent_events()
        assert any(e.event == GATE_BLOCKED and e.reason == "INDICATOR_NOT_READY"
                   for e in events)

    def test_log_allowed_recorded(self):
        self.gl.log_allowed(context="ETHUSDT/TrendFollowing")
        events = self.gl.recent_events()
        assert any(e.event == GATE_ALLOWED for e in events)

    def test_log_safe_mode_recorded(self):
        self.gl.log_safe_mode("WS_UNSTABLE", enforcer="SafeModeEnforcer")
        events = self.gl.recent_events()
        assert any(e.event == GATE_SAFE_MODE for e in events)

    def test_log_boot_ok(self):
        self.gl.log_boot(ok=True, stage="HARD_START")
        events = self.gl.recent_events()
        assert any(e.event == GATE_BOOT_OK for e in events)

    def test_log_boot_fail(self):
        self.gl.log_boot(ok=False, stage="HARD_START", detail="no candles")
        events = self.gl.recent_events()
        assert any(e.event == GATE_BOOT_FAIL for e in events)

    def test_block_counts_incremented(self):
        self.gl.log_blocked("WS_UNSTABLE")
        self.gl.log_blocked("WS_UNSTABLE")
        self.gl.log_blocked("DATA_NOT_FRESH")
        stats = self.gl.stats()
        assert stats["block_reason_counts"]["WS_UNSTABLE"] == 2
        assert stats["block_reason_counts"]["DATA_NOT_FRESH"] == 1

    def test_total_allowed_blocked_tracked(self):
        self.gl.log_allowed()
        self.gl.log_allowed()
        self.gl.log_blocked("X")
        stats = self.gl.stats()
        assert stats["total_allowed"] == 2
        assert stats["total_blocked"] == 1

    def test_top_block_reason(self):
        self.gl.log_blocked("A")
        self.gl.log_blocked("B")
        self.gl.log_blocked("B")
        stats = self.gl.stats()
        assert stats["top_block_reason"] == "B"

    def test_recent_blocks_filter(self):
        self.gl.log_allowed()
        self.gl.log_blocked("X")
        self.gl.log_allowed()
        blocks = self.gl.recent_blocks()
        assert all(e.event == GATE_BLOCKED for e in blocks)

    def test_history_bounded(self):
        for i in range(cfg.GL_HISTORY_SIZE + 50):
            self.gl.log_blocked(f"REASON_{i}")
        assert len(self.gl.recent_events(n=cfg.GL_HISTORY_SIZE + 100)) <= cfg.GL_HISTORY_SIZE

    def test_summary_phase(self):
        s = self.gl.summary()
        assert s["phase"] == "6.6"
        assert s["module"] == "GATE_LOGGER"


# ═══════════════════════════════════════════════════════════════════════════════
# GlobalGateController
# ═══════════════════════════════════════════════════════════════════════════════

class TestGlobalGateController:

    def setup_method(self):
        self.gate = GlobalGateController()

    def test_all_green_allowed(self):
        result = self.gate.evaluate(
            indicators_ready=True,
            ws_score=cfg.GGL_WS_MIN_SCORE + 10,
            data_fresh=True,
            deploy_score=cfg.GGL_DEPLOY_MIN_SCORE + 10,
        )
        assert result.allowed is True
        assert result.reason == "ALL_CLEAR"

    def test_indicators_not_ready_blocks(self):
        result = self.gate.evaluate(
            indicators_ready=False,
            ws_score=90.0, data_fresh=True, deploy_score=85.0,
        )
        assert result.allowed is False
        assert "INDICATOR_NOT_READY" in result.reason

    def test_ws_unstable_blocks(self):
        result = self.gate.evaluate(
            indicators_ready=True,
            ws_score=cfg.GGL_WS_MIN_SCORE - 10,
            data_fresh=True, deploy_score=85.0,
        )
        assert result.allowed is False
        assert "WS_UNSTABLE" in result.reason

    def test_data_not_fresh_blocks(self):
        result = self.gate.evaluate(
            indicators_ready=True,
            ws_score=90.0, data_fresh=False, deploy_score=85.0,
        )
        assert result.allowed is False
        assert "DATA_NOT_FRESH" in result.reason

    def test_deploy_low_blocks(self):
        result = self.gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True,
            deploy_score=cfg.GGL_DEPLOY_MIN_SCORE - 5,
        )
        assert result.allowed is False
        assert "DEPLOY_LOW" in result.reason

    def test_multiple_failures_all_reported(self):
        result = self.gate.evaluate(
            indicators_ready=False, ws_score=10.0,
            data_fresh=False, deploy_score=10.0,
        )
        assert result.allowed is False
        # All four failures should be in the reason string
        assert "INDICATOR_NOT_READY" in result.reason
        assert "WS_UNSTABLE" in result.reason
        assert "DATA_NOT_FRESH" in result.reason
        assert "DEPLOY_LOW" in result.reason

    def test_can_trade_returns_false_before_eval(self):
        # No evaluation run yet
        assert self.gate.can_trade() is False

    def test_can_trade_reflects_last_result(self):
        self.gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True, deploy_score=85.0,
        )
        assert self.gate.can_trade() is True

    def test_force_block_overrides(self):
        self.gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True, deploy_score=85.0,
        )
        assert self.gate.can_trade() is True
        self.gate.force_block("EMERGENCY_STOP")
        assert self.gate.can_trade() is False

    def test_total_blocked_tracked(self):
        self.gate.evaluate(indicators_ready=False, ws_score=90.0,
                           data_fresh=True, deploy_score=85.0)
        self.gate.evaluate(indicators_ready=True, ws_score=90.0,
                           data_fresh=True, deploy_score=85.0)
        s = self.gate.summary()
        assert s["total_blocked"] >= 1
        assert s["total_checks"] == 2

    def test_summary_phase(self):
        s = self.gate.summary()
        assert s["phase"] == "6.6"
        assert s["module"] == "GLOBAL_GATE_CONTROLLER"


# ═══════════════════════════════════════════════════════════════════════════════
# HardStartValidator
# ═══════════════════════════════════════════════════════════════════════════════

class TestHardStartValidator:

    def setup_method(self):
        self.hsv = HardStartValidator()

    def test_sufficient_candles_and_indicators_passes(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True,
            ws_reachable=True,
        )
        assert result.ok is True
        assert len(result.failed) == 0

    def test_insufficient_candles_fails(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT - 1,
            indicator_ok=True,
            ws_reachable=True,
        )
        assert result.ok is False
        assert any("candle_count" in f for f in result.failed)

    def test_indicators_not_ready_fails(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=False,
            ws_reachable=True,
        )
        assert result.ok is False
        assert any("indicator_validator" in f for f in result.failed)

    def test_ws_not_reachable_is_soft_warning(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True,
            ws_reachable=False,
        )
        # WS not reachable at boot is soft — still passes if everything else ok
        assert result.ok is True

    def test_extra_checks_included(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True,
            extra_checks={"redis_alive": False},
        )
        assert result.ok is False
        assert any("redis_alive" in f for f in result.failed)

    def test_extra_checks_pass(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True,
            extra_checks={"redis_alive": True},
        )
        assert result.ok is True

    def test_enforce_raises_when_not_exit_mode(self):
        result = self.hsv.validate(
            candle_count=1, indicator_ok=False
        )
        assert result.ok is False
        with pytest.raises(RuntimeError, match="Engine start blocked"):
            self.hsv.enforce(result)

    def test_enforce_noop_on_ok(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True,
        )
        assert result.ok is True
        self.hsv.enforce(result)  # must not raise

    def test_config_sanity_check_runs(self):
        result = self.hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True,
        )
        # Default config is sane → config_sanity=OK should be in passed
        assert any("config_sanity" in p for p in result.passed)

    def test_summary_phase(self):
        s = self.hsv.summary()
        assert s["phase"] == "6.6"
        assert s["module"] == "HARD_START_VALIDATOR"


# ═══════════════════════════════════════════════════════════════════════════════
# SafeModeEnforcer
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeModeEnforcer:

    def setup_method(self):
        # Fresh controller to isolate each test
        self.smc = SafeModeController()
        self.enforcer = SafeModeEnforcer()
        # Patch enforcer to use isolated controller
        import core.safe_mode_enforcer as _mod
        self._orig_smc = _mod.safe_mode_controller

    def teardown_method(self):
        import core.safe_mode_enforcer as _mod
        _mod.safe_mode_controller = self._orig_smc

    def _patch(self):
        import core.safe_mode_enforcer as _mod
        _mod.safe_mode_controller = self.smc

    def test_all_healthy_no_safe_mode(self):
        self._patch()
        result = self.enforcer.evaluate(
            deploy_score=cfg.SME_DEPLOY_LOW_THRESHOLD + 10,
            ws_score=cfg.SME_WS_LOW_THRESHOLD + 10,
            data_health=cfg.SME_DATA_LOW_THRESHOLD + 10,
        )
        assert result.safe_mode_active is False
        assert result.triggers == []

    def test_deploy_low_triggers_safe_mode(self):
        self._patch()
        result = self.enforcer.evaluate(
            deploy_score=cfg.SME_DEPLOY_LOW_THRESHOLD - 10,
            ws_score=80.0, data_health=80.0,
        )
        assert result.safe_mode_active is True
        assert any("DEPLOY_LOW" in t for t in result.triggers)

    def test_ws_low_triggers_safe_mode(self):
        self._patch()
        result = self.enforcer.evaluate(
            deploy_score=80.0,
            ws_score=cfg.SME_WS_LOW_THRESHOLD - 10,
            data_health=80.0,
        )
        assert result.safe_mode_active is True
        assert any("WS_LOW" in t for t in result.triggers)

    def test_data_low_triggers_safe_mode(self):
        self._patch()
        result = self.enforcer.evaluate(
            deploy_score=80.0, ws_score=80.0,
            data_health=cfg.SME_DATA_LOW_THRESHOLD - 10,
        )
        assert result.safe_mode_active is True
        assert any("DATA_LOW" in t for t in result.triggers)

    def test_gate_blocked_triggers_safe_mode(self):
        self._patch()
        result = self.enforcer.evaluate(
            deploy_score=80.0, ws_score=80.0,
            data_health=80.0, gate_allowed=False,
        )
        assert result.safe_mode_active is True
        assert any("GLOBAL_GATE_BLOCKED" in t for t in result.triggers)

    def test_triggered_now_flag_only_on_first_activation(self):
        self._patch()
        r1 = self.enforcer.evaluate(
            deploy_score=10.0, ws_score=10.0, data_health=10.0
        )
        assert r1.safe_mode_triggered is True  # first activation

        r2 = self.enforcer.evaluate(
            deploy_score=10.0, ws_score=10.0, data_health=10.0
        )
        assert r2.safe_mode_triggered is False  # already active

    def test_is_system_safe_reflects_state(self):
        self._patch()
        self.enforcer.evaluate(deploy_score=80.0, ws_score=80.0, data_health=80.0)
        assert self.enforcer.is_system_safe() is True

    def test_summary_phase(self):
        s = self.enforcer.summary()
        assert s["phase"] == "6.6"
        assert s["module"] == "SAFE_MODE_ENFORCER"


# ═══════════════════════════════════════════════════════════════════════════════
# PreTradeGate
# ═══════════════════════════════════════════════════════════════════════════════

class TestPreTradeGate:

    def _fresh_gate_and_controller(self):
        smc  = SafeModeController()
        gate = GlobalGateController()
        ptg  = PreTradeGate()
        import core.pre_trade_gate as _ptg_mod
        import core.global_gate as _gg_mod
        _ptg_mod.safe_mode_controller = smc
        _ptg_mod.global_gate = gate
        return ptg, gate, smc

    def test_all_clear_allows_trade(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True, deploy_score=85.0,
        )
        perm = ptg.check(
            symbol="BTCUSDT", strategy="TrendFollowing",
            indicator_ok=True, data_fresh=True,
        )
        assert perm.allowed is True

    def test_safe_mode_active_blocks_all_trades(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        smc.activate("TEST")
        perm = ptg.check(symbol="BTCUSDT", strategy="TrendFollowing")
        assert perm.allowed is False
        assert perm.reason == "SAFE_MODE_ACTIVE"
        assert perm.gate_source == "SafeModeController"

    def test_global_gate_blocked_blocks_trade(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        gate.evaluate(
            indicators_ready=False, ws_score=10.0,
            data_fresh=False, deploy_score=10.0,
        )
        perm = ptg.check(symbol="BTCUSDT", strategy="TrendFollowing",
                         indicator_ok=True, data_fresh=True)
        assert perm.allowed is False
        assert perm.gate_source == "GlobalGateController"

    def test_indicator_not_ready_blocks(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True, deploy_score=85.0,
        )
        perm = ptg.check(
            symbol="BTCUSDT", strategy="TrendFollowing",
            indicator_ok=False, data_fresh=True,
        )
        assert perm.allowed is False
        assert perm.reason == "INDICATOR_NOT_READY"

    def test_data_not_fresh_blocks(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True, deploy_score=85.0,
        )
        perm = ptg.check(
            symbol="BTCUSDT", strategy="TrendFollowing",
            indicator_ok=True, data_fresh=False,
        )
        assert perm.allowed is False
        assert perm.reason == "DATA_NOT_FRESH"

    def test_manage_only_always_allowed(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        smc.activate("SAFE_MODE")
        assert ptg.check_manage_only(symbol="BTCUSDT") is True

    def test_blocked_before_any_gate_eval(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        # No gate.evaluate() called → can_trade() = False
        perm = ptg.check(symbol="BTCUSDT", indicator_ok=True, data_fresh=True)
        assert perm.allowed is False

    def test_block_count_tracked(self):
        ptg, gate, smc = self._fresh_gate_and_controller()
        smc.activate("TEST")
        ptg.check()
        ptg.check()
        s = ptg.summary()
        assert s["total_blocked"] >= 2

    def test_summary_phase(self):
        ptg = PreTradeGate()
        s = ptg.summary()
        assert s["phase"] == "6.6"
        assert s["module"] == "PRE_TRADE_GATE"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Full Phase 6.6 Control Flow
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhase66Integration:
    """
    Verifies the complete Phase 6.6 gating chain:
    HardStartValidator → GlobalGateController → SafeModeEnforcer → PreTradeGate
    """

    def test_healthy_system_trade_passes_all_gates(self):
        gl   = GateLogger()
        gate = GlobalGateController()
        smc  = SafeModeController()
        hsv  = HardStartValidator()
        ptg  = PreTradeGate()
        sme  = SafeModeEnforcer()

        import core.pre_trade_gate as _ptg_mod
        import core.global_gate as _gg_mod
        import core.safe_mode_enforcer as _sme_mod
        _ptg_mod.safe_mode_controller = smc
        _ptg_mod.global_gate = gate
        _sme_mod.safe_mode_controller = smc

        # Step 1: Hard start
        start_result = hsv.validate(
            candle_count=cfg.HSV_MIN_CANDLES_BOOT,
            indicator_ok=True, ws_reachable=True,
        )
        assert start_result.ok is True

        # Step 2: Global gate evaluation
        gate_result = gate.evaluate(
            indicators_ready=True, ws_score=90.0,
            data_fresh=True, deploy_score=85.0,
        )
        assert gate_result.allowed is True

        # Step 3: Enforcer sees healthy system
        enforcer_result = sme.evaluate(
            deploy_score=85.0, ws_score=90.0, data_health=85.0,
            gate_allowed=True,
        )
        assert enforcer_result.safe_mode_active is False

        # Step 4: Pre-trade gate — final check
        perm = ptg.check(
            symbol="BTCUSDT", strategy="TrendFollowing",
            indicator_ok=True, data_fresh=True,
        )
        assert perm.allowed is True

    def test_ws_failure_cascades_to_block(self):
        gate = GlobalGateController()
        smc  = SafeModeController()
        ptg  = PreTradeGate()
        sme  = SafeModeEnforcer()

        import core.pre_trade_gate as _ptg_mod
        import core.global_gate as _gg_mod
        import core.safe_mode_enforcer as _sme_mod
        _ptg_mod.safe_mode_controller = smc
        _ptg_mod.global_gate = gate
        _sme_mod.safe_mode_controller = smc

        # WS fails → gate fails → enforcer triggers safe mode → trade blocked
        gate_result = gate.evaluate(
            indicators_ready=True,
            ws_score=5.0,          # below GGL_WS_MIN_SCORE
            data_fresh=True, deploy_score=85.0,
        )
        assert gate_result.allowed is False

        sme.evaluate(
            deploy_score=50.0,
            ws_score=5.0,           # below SME_WS_LOW_THRESHOLD
            data_health=80.0,
            gate_allowed=False,
        )
        assert smc.is_active is True

        perm = ptg.check(symbol="ETHUSDT", indicator_ok=True, data_fresh=True)
        assert perm.allowed is False

    def test_no_trade_passes_without_gate_eval(self):
        gate = GlobalGateController()
        smc  = SafeModeController()
        ptg  = PreTradeGate()

        import core.pre_trade_gate as _ptg_mod
        _ptg_mod.safe_mode_controller = smc
        _ptg_mod.global_gate = gate

        # No gate.evaluate() called → blocked
        perm = ptg.check(symbol="BNBUSDT", indicator_ok=True, data_fresh=True)
        assert perm.allowed is False

    def test_indicator_failure_at_boot_cascades(self):
        hsv = HardStartValidator()
        smc = SafeModeController()

        result = hsv.validate(candle_count=2, indicator_ok=False)
        assert result.ok is False

        # Simulate: boot failure → activate safe mode
        smc.activate(result.reason)
        assert smc.is_active is True
        assert smc.can_open_new_trade() is False
        assert smc.can_manage_existing() is True

    def test_gate_logger_captures_all_events(self):
        gl   = GateLogger()
        gate = GlobalGateController()

        import core.global_gate as _gg_mod
        orig_gl = _gg_mod.gate_logger
        _gg_mod.gate_logger = gl

        try:
            gate.evaluate(
                indicators_ready=False, ws_score=10.0,
                data_fresh=False, deploy_score=10.0,
                context="SOLUSDT/MeanReversion",
            )
            blocks = gl.recent_blocks()
            assert len(blocks) >= 1
            assert gl.stats()["total_blocked"] >= 1
        finally:
            _gg_mod.gate_logger = orig_gl


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

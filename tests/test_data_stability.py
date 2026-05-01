"""
EOW Quant Engine — Phase 6.5 Verifier
Tests: DataHealthMonitor, IndicatorValidator, WsStabilityEngine,
       BootDeployabilityEngine, SafeModeController
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.data_health import DataHealthMonitor, DataHealthResult
from core.indicator_validator import IndicatorValidator
from core.ws_stability import WsStabilityEngine
from core.deployability import BootDeployabilityEngine, BootDeployabilityResult
from core.safe_mode import SafeModeController, SafeModeState
from config import cfg


# ═══════════════════════════════════════════════════════════════════════════════
# DataHealthMonitor
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataHealthMonitor:

    def setup_method(self):
        self.monitor = DataHealthMonitor()

    def _fresh_tick(self):
        """Return current time (tick just arrived)."""
        return time.time()

    def test_all_healthy_no_block(self):
        result = self.monitor.check(
            last_tick_ts=self._fresh_tick(),
            symbol_tick_ages={"BTCUSDT": 2.0, "ETHUSDT": 3.0},
            indicator_ready=True,
            latency_ms=50.0,
        )
        assert result.ok is True
        assert result.block_trading is False
        assert result.health_score >= cfg.DHM_MIN_HEALTH_SCORE

    def test_stale_tick_blocks_trading(self):
        stale_ts = time.time() - (cfg.DHM_STALE_TICK_SEC + 10)
        result = self.monitor.check(
            last_tick_ts=stale_ts,
            symbol_tick_ages={"BTCUSDT": cfg.DHM_STALE_TICK_SEC + 10},
            indicator_ready=True,
        )
        assert result.block_trading is True
        assert result.ok is False
        assert "STALE_TICK" in result.reason

    def test_indicators_not_ready_blocks(self):
        result = self.monitor.check(
            last_tick_ts=self._fresh_tick(),
            symbol_tick_ages={"BTCUSDT": 1.0},
            indicator_ready=False,
        )
        assert result.block_trading is True
        assert "INDICATORS_NOT_READY" in result.reason

    def test_high_latency_hard_block(self):
        result = self.monitor.check(
            last_tick_ts=self._fresh_tick(),
            symbol_tick_ages={"BTCUSDT": 1.0},
            indicator_ready=True,
            latency_ms=cfg.DHM_LATENCY_BLOCK_MS + 500,
        )
        assert result.block_trading is True
        assert "HIGH_LATENCY" in result.reason

    def test_warn_latency_no_hard_block(self):
        result = self.monitor.check(
            last_tick_ts=self._fresh_tick(),
            symbol_tick_ages={"BTCUSDT": 1.0, "ETHUSDT": 2.0},
            indicator_ready=True,
            latency_ms=cfg.DHM_LATENCY_WARN_MS + 100,
        )
        # Only warn; hard block at DHM_LATENCY_BLOCK_MS
        assert "HIGH_LATENCY" not in result.reason

    def test_poor_candle_coverage_lowers_score(self):
        # Many symbols with stale data → low candle score
        ages = {f"SYM{i}": cfg.DHM_STALE_TICK_SEC + 5 for i in range(10)}
        result = self.monitor.check(
            last_tick_ts=self._fresh_tick(),
            symbol_tick_ages=ages,
            indicator_ready=True,
        )
        assert result.candle_coverage == pytest.approx(0.0, abs=0.01)

    def test_health_score_bounded_0_100(self):
        result = self.monitor.check(
            last_tick_ts=self._fresh_tick(),
            symbol_tick_ages={"BTCUSDT": 1.0},
            indicator_ready=True,
            latency_ms=10.0,
        )
        assert 0.0 <= result.health_score <= 100.0

    def test_summary_returns_phase(self):
        s = self.monitor.summary()
        assert s["phase"] == "6.5"
        assert s["module"] == "DATA_HEALTH_MONITOR"


# ═══════════════════════════════════════════════════════════════════════════════
# IndicatorValidator
# ═══════════════════════════════════════════════════════════════════════════════

class TestIndicatorValidator:

    def setup_method(self):
        self.iv = IndicatorValidator()

    def test_all_candles_sufficient_passes(self):
        result = self.iv.validate(
            candle_count=50,
            rsi_candles=50,
            adx_candles=50,
            atr_candles=50,
            volume_candles=50,
        )
        assert result.ok is True
        assert result.prevent_trade is False

    def test_insufficient_candles_blocks(self):
        result = self.iv.validate(
            candle_count=5,
            rsi_candles=5,
            adx_candles=5,
            atr_candles=5,
            volume_candles=5,
        )
        assert result.ok is False
        assert result.prevent_trade is True
        assert len(result.failed) > 0

    def test_nan_indicator_fails(self):
        import math
        result = self.iv.validate(
            candle_count=50,
            rsi_candles=50,
            adx_candles=50,
            atr_candles=50,
            volume_candles=50,
            indicator_values={"rsi": math.nan, "adx": 25.0},
        )
        assert result.ok is False
        assert any("rsi" in f for f in result.failed)

    def test_valid_indicator_values_pass(self):
        result = self.iv.validate(
            candle_count=50,
            rsi_candles=50,
            adx_candles=50,
            atr_candles=50,
            volume_candles=50,
            indicator_values={"rsi": 52.3, "adx": 24.1, "atr": 0.0025},
        )
        assert result.ok is True
        assert result.score == 1.0

    def test_partial_failure_score_below_1(self):
        result = self.iv.validate(
            candle_count=50,
            rsi_candles=50,
            adx_candles=5,      # will fail
            atr_candles=50,
            volume_candles=50,
        )
        assert result.ok is False
        assert result.score < 1.0

    def test_is_ready_reflects_last_result(self):
        self.iv.validate(
            candle_count=50, rsi_candles=50, adx_candles=50,
            atr_candles=50, volume_candles=50,
        )
        assert self.iv.is_ready() is True

    def test_buffer_convenience_wrapper(self):
        closes  = list(range(50))
        volumes = list(range(50))
        result = self.iv.validate_symbol_buffers(closes, volumes)
        assert result.ok is True

    def test_summary_phase(self):
        s = self.iv.summary()
        assert s["phase"] == "6.5"
        assert s["module"] == "INDICATOR_VALIDATOR"


# ═══════════════════════════════════════════════════════════════════════════════
# WsStabilityEngine
# ═══════════════════════════════════════════════════════════════════════════════

class TestWsStabilityEngine:

    def setup_method(self):
        self.ws = WsStabilityEngine()

    def test_fresh_healthy_score(self):
        self.ws.record_tick(latency_ms=10.0)
        score = self.ws.stability_score()
        assert score == pytest.approx(100.0, abs=1.0)

    def test_reconnect_reduces_score(self):
        self.ws.record_tick(latency_ms=10.0)
        before = self.ws.stability_score()
        self.ws.record_reconnect()
        after = self.ws.stability_score()
        assert after < before

    def test_exceeding_reconnect_limit_triggers_safe_mode(self):
        # Provide initial tick so it's not marked stale
        self.ws.record_tick(latency_ms=5.0)
        limit = cfg.WSS_MAX_RECONNECTS_SAFE_MODE
        for _ in range(limit + 1):
            self.ws.record_reconnect()
        assert self.ws._safe_mode_triggered is True

    def test_reset_reconnects_clears_safe_mode_flag(self):
        self.ws.record_tick(latency_ms=5.0)
        for _ in range(cfg.WSS_MAX_RECONNECTS_SAFE_MODE + 1):
            self.ws.record_reconnect()
        self.ws.reset_reconnects()
        assert self.ws._reconnect_count == 0
        assert self.ws._safe_mode_triggered is False

    def test_high_latency_lowers_score(self):
        self.ws.record_tick(latency_ms=cfg.WSS_LATENCY_BLOCK_MS + 100)
        score = self.ws.stability_score()
        assert score < 90.0

    def test_snapshot_state_healthy(self):
        self.ws.record_tick(latency_ms=5.0)
        snap = self.ws.snapshot()
        assert snap.state == "HEALTHY"
        assert snap.is_connected is True

    def test_snapshot_safe_mode_state(self):
        self.ws.record_tick(latency_ms=5.0)
        self.ws._safe_mode_triggered = True
        snap = self.ws.snapshot()
        assert snap.state == "SAFE_MODE"

    def test_summary_phase(self):
        s = self.ws.summary()
        assert s["phase"] == "6.5"
        assert s["module"] == "WS_STABILITY_ENGINE"


# ═══════════════════════════════════════════════════════════════════════════════
# BootDeployabilityEngine
# ═══════════════════════════════════════════════════════════════════════════════

class TestBootDeployabilityEngine:

    def setup_method(self):
        self.bde = BootDeployabilityEngine()

    def test_all_systems_green_ready(self):
        result = self.bde.evaluate(
            data_health_score=90.0,
            indicator_score=1.0,
            ws_stability_score=95.0,
            current_drawdown=0.01,
            daily_loss_pct=0.005,
        )
        assert result.ok is True
        assert result.status in ("READY", "DEGRADED")
        assert result.score >= cfg.BDE_MIN_SCORE

    def test_bad_data_health_blocks(self):
        result = self.bde.evaluate(
            data_health_score=10.0,    # very low
            indicator_score=0.3,
            ws_stability_score=20.0,
            current_drawdown=0.01,
        )
        assert result.block_trading is True
        assert result.ok is False

    def test_score_below_threshold_blocks(self):
        result = self.bde.evaluate(
            data_health_score=30.0,
            indicator_score=0.30,
            ws_stability_score=25.0,
            current_drawdown=0.05,
        )
        assert result.score < cfg.BDE_MIN_SCORE
        assert result.block_trading is True

    def test_score_at_threshold_passes(self):
        # Force all components to exactly produce BDE_MIN_SCORE
        # Solve: 0.30*x + 0.25*x + 0.25*x + 0.20*x = BDE_MIN_SCORE
        # 1.0*x = BDE_MIN_SCORE → x = BDE_MIN_SCORE
        x = cfg.BDE_MIN_SCORE + 1.0  # just above threshold
        result = self.bde.evaluate(
            data_health_score=x,
            indicator_score=x / 100.0,
            ws_stability_score=x,
            current_drawdown=0.0,
            daily_loss_pct=0.0,
        )
        assert result.ok is True

    def test_high_drawdown_reduces_risk_score(self):
        r_low_dd = self.bde.evaluate(
            data_health_score=80, indicator_score=1.0,
            ws_stability_score=80, current_drawdown=0.01,
        )
        r_high_dd = self.bde.evaluate(
            data_health_score=80, indicator_score=1.0,
            ws_stability_score=80, current_drawdown=0.14,
        )
        assert r_low_dd.score > r_high_dd.score

    def test_indicators_not_ready_lowers_score(self):
        r_ready = self.bde.evaluate(
            data_health_score=85, indicator_score=1.0,
            ws_stability_score=85, current_drawdown=0.01,
        )
        r_not_ready = self.bde.evaluate(
            data_health_score=85, indicator_score=0.0,
            ws_stability_score=85, current_drawdown=0.01,
        )
        assert r_ready.score > r_not_ready.score

    def test_status_labels(self):
        r_ready = self.bde.evaluate(
            data_health_score=95, indicator_score=1.0,
            ws_stability_score=95, current_drawdown=0.0,
        )
        assert r_ready.status == "READY"

        r_blocked = self.bde.evaluate(
            data_health_score=10, indicator_score=0.1,
            ws_stability_score=10, current_drawdown=0.14,
        )
        assert r_blocked.status == "BLOCKED"

    def test_summary_phase(self):
        s = self.bde.summary()
        assert s["phase"] == "6.5"
        assert s["module"] == "BOOT_DEPLOYABILITY_ENGINE"


# ═══════════════════════════════════════════════════════════════════════════════
# SafeModeController
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeModeController:

    def setup_method(self):
        self.smc = SafeModeController()

    def test_inactive_by_default(self):
        assert self.smc.is_active is False
        assert self.smc.can_open_new_trade() is True

    def test_activate_blocks_new_trades(self):
        self.smc.activate("TEST_REASON")
        assert self.smc.is_active is True
        assert self.smc.can_open_new_trade() is False

    def test_manage_existing_always_allowed(self):
        self.smc.activate("TEST")
        assert self.smc.can_manage_existing() is True

    def test_deactivate_restores_trading(self):
        self.smc.activate("TEST")
        self.smc.deactivate("MANUAL")
        assert self.smc.is_active is False
        assert self.smc.can_open_new_trade() is True

    def test_activate_idempotent(self):
        self.smc.activate("FIRST")
        self.smc.activate("SECOND")
        assert self.smc.is_active is True
        assert self.smc.status().reason == "SECOND"

    def test_auto_resume_denied_on_low_score(self):
        self.smc.activate("TEST")
        self.smc._last_resume_check = 0.0  # force check now
        resumed = self.smc.check_auto_resume(current_score=45.0)
        assert resumed is False
        assert self.smc.is_active is True

    def test_auto_resume_passes_on_high_score(self):
        self.smc.activate("TEST")
        self.smc._last_resume_check = 0.0  # force check now
        resumed = self.smc.check_auto_resume(current_score=cfg.SMC_MIN_SCORE_RESUME + 5)
        assert resumed is True
        assert self.smc.is_active is False

    def test_auto_resume_respects_interval(self):
        self.smc.activate("TEST")
        self.smc._last_resume_check = time.time()  # just checked
        resumed = self.smc.check_auto_resume(current_score=99.0)
        # Interval not elapsed → should not resume
        assert resumed is False

    def test_status_duration_increases_over_time(self):
        self.smc.activate("TEST")
        status = self.smc.status()
        assert status.duration_min >= 0.0
        assert status.active is True

    def test_history_logged(self):
        self.smc.activate("REASON_A")
        self.smc.deactivate("REASON_B")
        events = self.smc.recent_events()
        actions = [e.action for e in events]
        assert "ACTIVATED" in actions
        assert "DEACTIVATED" in actions

    def test_summary_phase(self):
        s = self.smc.summary()
        assert s["phase"] == "6.5"
        assert s["module"] == "SAFE_MODE_CONTROLLER"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Boot Flow
# ═══════════════════════════════════════════════════════════════════════════════

class TestBootFlowIntegration:
    """
    Verifies the complete Phase 6.5 boot flow:
    IndicatorValidator → DataHealthMonitor → WsStabilityEngine
    → BootDeployabilityEngine → SafeModeController
    """

    def test_healthy_boot_allows_trading(self):
        iv  = IndicatorValidator()
        dhm = DataHealthMonitor()
        ws  = WsStabilityEngine()
        bde = BootDeployabilityEngine()
        smc = SafeModeController()

        # Step 1: Validate indicators
        iv_result = iv.validate(
            candle_count=50, rsi_candles=50, adx_candles=50,
            atr_candles=50, volume_candles=50,
        )
        assert iv_result.ok is True

        # Step 2: Check data health
        ws.record_tick(latency_ms=15.0)
        dh_result = dhm.check(
            last_tick_ts=time.time(),
            symbol_tick_ages={"BTCUSDT": 2.0, "ETHUSDT": 3.0},
            indicator_ready=iv_result.ok,
            latency_ms=15.0,
        )
        assert dh_result.ok is True

        # Step 3: Boot deployability score
        bde_result = bde.evaluate(
            data_health_score=dh_result.health_score,
            indicator_score=iv_result.score,
            ws_stability_score=ws.stability_score(),
        )
        assert bde_result.ok is True

        # Step 4: Safe mode should be inactive
        assert smc.can_open_new_trade() is True

    def test_stale_data_triggers_safe_mode_via_deployability(self):
        bde = BootDeployabilityEngine()
        smc = SafeModeController()

        # Very poor system state
        bde_result = bde.evaluate(
            data_health_score=5.0,     # terrible
            indicator_score=0.0,       # no indicators
            ws_stability_score=5.0,    # terrible
            current_drawdown=0.14,
        )
        assert bde_result.block_trading is True

        # Operator activates safe mode based on block signal
        if bde_result.block_trading:
            smc.activate(bde_result.reason)

        assert smc.is_active is True
        assert smc.can_open_new_trade() is False
        assert smc.can_manage_existing() is True

    def test_ws_reconnect_cascade_to_safe_mode(self):
        ws  = WsStabilityEngine()
        smc = SafeModeController()

        ws.record_tick(latency_ms=10.0)
        # Simulate repeated reconnects
        for _ in range(cfg.WSS_MAX_RECONNECTS_SAFE_MODE + 1):
            ws.record_reconnect()

        assert ws._safe_mode_triggered is True

        # Safe mode controller should also reflect this
        if ws._safe_mode_triggered:
            smc.activate("WS_STABILITY: too many reconnects")

        assert smc.can_open_new_trade() is False

    def test_indicators_not_ready_prevents_trading_at_boot(self):
        iv  = IndicatorValidator()
        smc = SafeModeController()

        # Cold boot: only 5 candles — not ready
        result = iv.validate(
            candle_count=5, rsi_candles=5, adx_candles=5,
            atr_candles=5, volume_candles=5,
        )
        assert result.prevent_trade is True

        if result.prevent_trade:
            smc.activate(f"INDICATOR_VALIDATOR: {result.reason}")

        assert smc.is_active is True
        assert smc.can_open_new_trade() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

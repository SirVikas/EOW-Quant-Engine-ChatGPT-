"""
EOW Quant Engine — core/gating/global_gate_controller.py
Phase 6.6: Global Gate Controller — Master Trading Authority

Single source of truth for two questions:
    1. Can the system trade right now?
    2. Should safe mode be activated?

Interface (spec-compliant):
    gate.evaluate() -> {
        "can_trade": bool,
        "reason":    str,
        "safe_mode": bool,
    }

Four gate conditions (ALL must pass to allow trading):
    indicators_ready  — IndicatorValidator confirmed all indicators warm
    websocket_stable  — WsStabilityEngine score ≥ GGL_WS_MIN_SCORE
    data_fresh        — DataHealthMonitor last result ok=True
    deployability_ok  — BootDeployabilityEngine score ≥ GGL_DEPLOY_MIN_SCORE

On any failure:
    → can_trade = False
    → reason = pipe-delimited list of failed conditions
    → safe_mode = True (SafeModeEngine.activate() called internally)

Dependencies are injected at construction so this class is independently
testable without the full Phase 6.5 singletons.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional, Union

from loguru import logger

from config import cfg
from core.gating.gate_logger import gate_logger
from core.gating.safe_mode_engine import SafeModeEngine, safe_mode_engine as _default_sme


class GlobalGateController:
    """
    Master trading permission authority.

    Constructor accepts optional callables (thunks) for each data source so
    the class can be used standalone in tests without the full Phase 6.5 stack.

    In production use global_gate_controller singleton (wired at module level).

    Args:
        indicator_ready_fn:  callable() → bool
        ws_score_fn:         callable() → float   (0–100)
        data_fresh_fn:       callable() → bool
        deploy_score_fn:     callable() → float   (0–100)
        safe_mode:           SafeModeEngine instance to activate on failure
    """

    def __init__(
        self,
        indicator_ready_fn: Callable[[], bool]  = lambda: True,
        ws_score_fn:        Callable[[], float] = lambda: 100.0,
        data_fresh_fn:      Callable[[], bool]  = lambda: True,
        deploy_score_fn:    Callable[[], float] = lambda: 100.0,
        safe_mode:          Optional[SafeModeEngine] = None,
    ):
        self._ind_fn    = indicator_ready_fn
        self._ws_fn     = ws_score_fn
        self._data_fn   = data_fresh_fn
        self._deploy_fn = deploy_score_fn
        self._sme       = safe_mode if safe_mode is not None else _default_sme

        self._last_result: dict = {}
        self._last_ts: float = 0.0
        self._total_evals: int = 0
        self._total_blocked: int = 0
        self._system_state: str = "BOOTING"   # qFTD-010: BOOTING → LIVE, set via set_system_state()

        logger.info(
            f"[GLOBAL-GATE] Phase 6.6 activated | "
            f"deploy_min={cfg.GGL_DEPLOY_MIN_SCORE} "
            f"ws_min={cfg.GGL_WS_MIN_SCORE} "
            f"cache_ttl={cfg.GGL_CACHE_TTL_SEC}s"
        )

    # ── System state management ───────────────────────────────────────────────

    def set_system_state(self, state: str) -> None:
        """
        Notify the gate of system state transitions (qFTD-010).

        During BOOTING, evaluate() returns ALL_CLEAR unconditionally so that
        run_cycle()'s internal gate re-evaluation never activates safe mode
        before indicator/data streams have fully opened.

        Args:
            state: "BOOTING" | "LIVE"
        """
        if state != self._system_state:
            logger.info(f"[GLOBAL-GATE] system_state transition: {self._system_state} → {state}")
            self._system_state = state

    # ── Primary spec-compliant interface ──────────────────────────────────────

    def evaluate(
        self,
        indicator_ok:       Optional[bool] = None,
        data_fresh:         Optional[bool] = None,
        activate_safe_mode: bool           = True,
    ) -> dict:
        """
        Evaluate all gate conditions and return the canonical gate dict.

        Args:
            indicator_ok:       When provided, overrides the internal indicator_ready_fn().
                                Pass the caller's pre-computed readiness value so the gate
                                uses a single source of truth instead of re-querying singletons.
            data_fresh:         When provided, overrides the internal data_fresh_fn().
                                Pass the result of data_health_monitor.check() from the caller.
            activate_safe_mode: When False, a failing gate does NOT activate SafeModeEngine.
                                Use during boot / diagnostic probes where the system is not
                                yet fully initialised and a failure is expected.

        Returns:
            {
                "can_trade": bool,
                "reason":    str,   — "ALL_CLEAR" or pipe-delimited failures
                "safe_mode": bool,  — True when safe mode was / is active
            }

        Side effects:
            • Logs every decision through GatingLogger
            • Activates SafeModeEngine on failure (only when activate_safe_mode=True)
            • Calls SafeModeEngine.check_recovery(can_trade=True) on success
        """
        self._total_evals += 1
        now = time.time()

        # qFTD-010: BOOTING grace — warmup noise must not activate safe mode.
        # During BOOTING, all conditions are unconditionally satisfied so that
        # run_cycle()'s internal gate re-evaluation does not block execution or
        # trip safe mode before indicator/data streams have fully opened.
        if self._system_state == "BOOTING":
            result = {
                "can_trade": True,
                "reason":    "BOOT_GRACE",
                "safe_mode": self._sme.mode.value != "NORMAL",
                "_ws_score":     100.0,
                "_deploy_score": 100.0,
                "_ind_ready":    True,
                "_data_fresh":   True,
            }
            self._last_result = result
            self._last_ts = now
            gate_logger.allowed()
            return result

        # qFTD-004: Use caller-supplied readiness when provided (single source of truth).
        # Fall back to internal singleton queries only when caller passes None.
        ind_ready      = indicator_ok if indicator_ok is not None else self._ind_fn()
        data_fresh_val = data_fresh   if data_fresh   is not None else self._data_fn()
        ws_score       = self._ws_fn()
        deploy         = self._deploy_fn()

        ws_ok     = ws_score  >= cfg.GGL_WS_MIN_SCORE
        deploy_ok = deploy    >= cfg.GGL_DEPLOY_MIN_SCORE

        failures = []
        if not ind_ready:
            failures.append("INDICATOR_NOT_READY")
        if not ws_ok:
            failures.append(f"WS_UNSTABLE(score={ws_score:.1f}<{cfg.GGL_WS_MIN_SCORE})")
        if not data_fresh_val:
            failures.append("DATA_NOT_FRESH")
        if not deploy_ok:
            failures.append(f"DEPLOY_LOW(score={deploy:.1f}<{cfg.GGL_DEPLOY_MIN_SCORE})")

        can_trade = len(failures) == 0
        reason    = " | ".join(failures) if failures else "ALL_CLEAR"

        if can_trade:
            gate_logger.allowed()
            # qFTD-005: pass can_trade=True so SAFE exits immediately on all-clear
            self._sme.check_recovery(deploy_score=deploy, can_trade=True)
        else:
            for f in failures:
                gate_logger.blocked(reason=f)
            # qFTD-005: skip safe mode activation during boot / diagnostic probes
            if activate_safe_mode:
                self._sme.activate(reason)
            self._total_blocked += 1

        result = {
            "can_trade": can_trade,
            "reason":    reason,
            "safe_mode": self._sme.mode.value != "NORMAL",
            # Extra diagnostic fields (not in spec but used by PreTradeGate)
            "_ws_score":     round(ws_score, 1),
            "_deploy_score": round(deploy, 1),
            "_ind_ready":    ind_ready,
            "_data_fresh":   data_fresh_val,
        }
        self._last_result = result
        self._last_ts = now
        return result

    def can_trade(self) -> bool:
        """
        Fast boolean from cached result. Returns False if never evaluated
        or if cache has expired (GGL_CACHE_TTL_SEC).
        """
        if not self._last_result:
            return False
        if time.time() - self._last_ts > cfg.GGL_CACHE_TTL_SEC:
            return False
        return bool(self._last_result.get("can_trade", False))

    def force_block(self, reason: str) -> None:
        """Emergency override — force-block all trading and activate safe mode."""
        self._last_result = {
            "can_trade": False,
            "reason":    f"FORCED_BLOCK: {reason}",
            "safe_mode": True,
        }
        self._last_ts = time.time()
        self._total_blocked += 1
        gate_logger.blocked(reason=f"FORCED_BLOCK: {reason}")
        self._sme.activate(f"FORCED_BLOCK: {reason}")
        logger.error(f"[GLOBAL-GATE] FORCE_BLOCK: {reason}")

    def summary(self) -> dict:
        block_rate = (self._total_blocked / self._total_evals
                      if self._total_evals else 0.0)
        return {
            "last_can_trade":  self._last_result.get("can_trade"),
            "last_reason":     self._last_result.get("reason", "NO_EVAL"),
            "safe_mode_mode":  self._sme.mode.value,
            "total_evals":     self._total_evals,
            "total_blocked":   self._total_blocked,
            "block_rate":      round(block_rate, 4),
            "thresholds": {
                "deploy_min": cfg.GGL_DEPLOY_MIN_SCORE,
                "ws_min":     cfg.GGL_WS_MIN_SCORE,
                "cache_ttl":  cfg.GGL_CACHE_TTL_SEC,
            },
            "module": "GLOBAL_GATE_CONTROLLER",
            "phase":  "6.6",
        }


# ── Production singleton (wired to Phase 6.5 singletons lazily) ──────────────

def _make_production_gate() -> GlobalGateController:
    """
    Wire GlobalGateController to the Phase 6.5 singletons.
    Lazy imports avoid circular dependency at module load time.
    """
    def _ind_ready() -> bool:
        try:
            from core.indicator_validator import indicator_validator
            return indicator_validator.is_ready()
        except Exception:
            return False

    def _ws_score() -> float:
        try:
            from core.ws_stability import ws_stability_engine
            return ws_stability_engine.stability_score()
        except Exception:
            return 0.0

    def _data_fresh() -> bool:
        try:
            from core.data_health import data_health_monitor
            r = data_health_monitor.last_result()
            return r.ok if r is not None else False
        except Exception:
            return False

    def _deploy_score() -> float:
        try:
            from core.data_health import data_health_monitor
            from core.indicator_validator import indicator_validator
            from core.ws_stability import ws_stability_engine
            from core.deployability import boot_deployability_engine
            dh = data_health_monitor.last_result()
            dh_score = dh.health_score if dh else 0.0
            iv_score = 1.0 if indicator_validator.is_ready() else 0.0
            ws_s     = ws_stability_engine.stability_score()
            r = boot_deployability_engine.evaluate(
                data_health_score=dh_score,
                indicator_score=iv_score,
                ws_stability_score=ws_s,
            )
            return r.score
        except Exception:
            return 0.0

    return GlobalGateController(
        indicator_ready_fn=_ind_ready,
        ws_score_fn=_ws_score,
        data_fresh_fn=_data_fresh,
        deploy_score_fn=_deploy_score,
        safe_mode=_default_sme,
    )


global_gate_controller = _make_production_gate()

"""
EOW Quant Engine — Phase 6.6: Global Gate Controller (Master Authority)
Single point of control for ALL trading permission in the system.

Every new trade entry MUST pass through can_trade() before any signal
processing or execution. This is the master override that no downstream
module can bypass.

Gate conditions (all must be True):
  indicators_ready      — IndicatorValidator confirms all indicators warm
  websocket_stable      — WsStabilityEngine score ≥ GGL_WS_MIN_SCORE
  data_fresh            — DataHealthMonitor reports ok=True
  deployability_ok      — BootDeployabilityEngine score ≥ GGL_DEPLOY_MIN_SCORE

Result is cached for GGL_CACHE_TTL_SEC to prevent redundant checks on
high-frequency signal paths.

Rule (non-negotiable):
  can_trade() == False → ALL new trades BLOCKED, no exception
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger

from config import cfg
from core.gate_logger import gate_logger, GATE_BLOCKED, GATE_ALLOWED


@dataclass
class GateResult:
    allowed:           bool
    indicators_ready:  bool
    ws_stable:         bool
    data_fresh:        bool
    deployability_ok:  bool
    deploy_score:      float
    ws_score:          float
    reason:            str = ""
    cached:            bool = False


class GlobalGateController:
    """
    Master trading permission authority.

    Aggregates four independent system health checks into a single
    boolean gate. All callers receive the same cached result within
    GGL_CACHE_TTL_SEC to minimise compute overhead on tick-level paths.

    Usage:
        result = global_gate.evaluate(
            indicators_ready=iv.is_ready(),
            ws_score=ws.stability_score(),
            data_fresh=dhm.last_result().ok if dhm.last_result() else False,
            deploy_score=bde.evaluate(...).score,
        )
        if not result.allowed:
            return  # hard block — do not proceed
    """

    def __init__(self):
        self._last_result: Optional[GateResult] = None
        self._last_eval_ts: float = 0.0
        self._total_checks: int = 0
        self._total_blocked: int = 0
        logger.info(
            f"[GLOBAL-GATE] Phase 6.6 activated | "
            f"deploy_min={cfg.GGL_DEPLOY_MIN_SCORE} "
            f"ws_min={cfg.GGL_WS_MIN_SCORE} "
            f"data_min={cfg.GGL_DATA_MIN_HEALTH} "
            f"cache_ttl={cfg.GGL_CACHE_TTL_SEC}s"
        )

    # ── Primary API ───────────────────────────────────────────────────────────

    def evaluate(
        self,
        indicators_ready: bool,
        ws_score:         float,
        data_fresh:       bool,
        deploy_score:     float,
        context:          str = "",
    ) -> GateResult:
        """
        Evaluate all four gate conditions and return a GateResult.

        This is the canonical gate call. All results are cached for
        GGL_CACHE_TTL_SEC; set context="" on cached-path callers.

        Args:
            indicators_ready: True when IndicatorValidator passed
            ws_score:         WsStabilityEngine.stability_score() 0–100
            data_fresh:       DataHealthMonitor reported ok=True
            deploy_score:     BootDeployabilityEngine score 0–100
            context:          optional label for logging (symbol/strategy)

        Returns GateResult; check result.allowed before any trade entry.
        """
        now = time.time()
        self._total_checks += 1

        # ── Per-condition evaluation ──────────────────────────────────────────
        ws_ok     = ws_score >= cfg.GGL_WS_MIN_SCORE
        deploy_ok = deploy_score >= cfg.GGL_DEPLOY_MIN_SCORE

        failures: List[str] = []
        if not indicators_ready:
            failures.append("INDICATOR_NOT_READY")
        if not ws_ok:
            failures.append(f"WS_UNSTABLE(score={ws_score:.1f}<{cfg.GGL_WS_MIN_SCORE})")
        if not data_fresh:
            failures.append("DATA_NOT_FRESH")
        if not deploy_ok:
            failures.append(f"DEPLOY_LOW(score={deploy_score:.1f}<{cfg.GGL_DEPLOY_MIN_SCORE})")

        allowed = len(failures) == 0
        reason  = " | ".join(failures) if failures else "ALL_CLEAR"

        result = GateResult(
            allowed=allowed,
            indicators_ready=indicators_ready,
            ws_stable=ws_ok,
            data_fresh=data_fresh,
            deployability_ok=deploy_ok,
            deploy_score=round(deploy_score, 1),
            ws_score=round(ws_score, 1),
            reason=reason,
            cached=False,
        )

        if allowed:
            gate_logger.log_allowed(context=context)
        else:
            for failure in failures:
                gate_logger.log_blocked(reason=failure, context=context)
            self._total_blocked += 1

        self._last_result  = result
        self._last_eval_ts = now
        return result

    def can_trade(self) -> bool:
        """
        Fast boolean check using cached result.
        Returns False when no evaluation has been run yet (safe default).
        """
        if self._last_result is None:
            return False
        age = time.time() - self._last_eval_ts
        if age > cfg.GGL_CACHE_TTL_SEC:
            return False  # cache expired → treat as blocked until re-evaluated
        return self._last_result.allowed

    def last_result(self) -> Optional[GateResult]:
        return self._last_result

    def force_block(self, reason: str) -> None:
        """Force the gate into BLOCKED state (e.g. called by SafeModeEnforcer)."""
        dummy = GateResult(
            allowed=False,
            indicators_ready=False,
            ws_stable=False,
            data_fresh=False,
            deployability_ok=False,
            deploy_score=0.0,
            ws_score=0.0,
            reason=f"FORCED_BLOCK: {reason}",
        )
        self._last_result  = dummy
        self._last_eval_ts = time.time()
        self._total_blocked += 1
        gate_logger.log_blocked(reason=f"FORCED_BLOCK: {reason}")
        logger.warning(f"[GLOBAL-GATE] Force-blocked: {reason}")

    # ── Introspection ─────────────────────────────────────────────────────────

    def summary(self) -> dict:
        r = self._last_result
        block_rate = (self._total_blocked / self._total_checks
                      if self._total_checks > 0 else 0.0)
        return {
            "allowed":         r.allowed if r else False,
            "reason":          r.reason  if r else "NO_EVAL",
            "total_checks":    self._total_checks,
            "total_blocked":   self._total_blocked,
            "block_rate":      round(block_rate, 4),
            "cache_age_sec":   round(time.time() - self._last_eval_ts, 2),
            "thresholds": {
                "deploy_min":  cfg.GGL_DEPLOY_MIN_SCORE,
                "ws_min":      cfg.GGL_WS_MIN_SCORE,
                "data_min":    cfg.GGL_DATA_MIN_HEALTH,
                "cache_ttl":   cfg.GGL_CACHE_TTL_SEC,
            },
            "module": "GLOBAL_GATE_CONTROLLER",
            "phase":  "6.6",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
global_gate = GlobalGateController()

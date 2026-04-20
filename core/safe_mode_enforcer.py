"""
EOW Quant Engine — Phase 6.6: Safe Mode Enforcer
Automatic runtime protection: monitors system health on every evaluation
cycle and activates SafeModeController the moment any threshold is breached.

Works in concert with GlobalGateController — the gate provides the
permission check; this module provides the automatic activation trigger.

Activation conditions (any one is sufficient):
  deploy_score  < SME_DEPLOY_LOW_THRESHOLD  (65)
  ws_score      < SME_WS_LOW_THRESHOLD      (40)
  data_health   < SME_DATA_LOW_THRESHOLD    (50)
  gate.can_trade() is False AND system has been blocked > TTL

Deactivation:
  Enforcer checks GlobalGateController.can_trade() every cycle.
  When all thresholds recover, it calls safe_mode_controller.check_auto_resume()
  with the current deploy_score. SafeModeController decides whether to lift.

Non-negotiable:
  Once activated, only SafeModeController's score gate can lift it.
  Enforcer never deactivates safe mode directly.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger

from config import cfg
from core.gate_logger import gate_logger
from core.safe_mode import safe_mode_controller


@dataclass
class EnforcerResult:
    safe_mode_active:   bool
    safe_mode_triggered: bool   # True if THIS call triggered it (newly activated)
    deploy_score:       float
    ws_score:           float
    data_health:        float
    triggers:           List[str]   # conditions that fired
    reason:             str = ""


class SafeModeEnforcer:
    """
    Runtime guardian that enforces safe mode automatically.

    Call evaluate() on every signal cycle or at a regular heartbeat
    interval. It is intentionally stateless w.r.t. thresholds — every
    call re-evaluates from fresh scores so recovery is not delayed.

    Usage:
        result = safe_mode_enforcer.evaluate(
            deploy_score=bde.score,
            ws_score=ws.stability_score(),
            data_health=dhm.health_score,
        )
        if result.safe_mode_active:
            return  # skip signal processing
    """

    def __init__(self):
        self._last_eval_ts: float = 0.0
        self._activations: int = 0
        logger.info(
            f"[SAFE-MODE-ENFORCER] Phase 6.6 activated | "
            f"deploy_threshold={cfg.SME_DEPLOY_LOW_THRESHOLD} "
            f"ws_threshold={cfg.SME_WS_LOW_THRESHOLD} "
            f"data_threshold={cfg.SME_DATA_LOW_THRESHOLD}"
        )

    def evaluate(
        self,
        deploy_score:    float,
        ws_score:        float,
        data_health:     float,
        gate_allowed:    Optional[bool] = None,
    ) -> EnforcerResult:
        """
        Evaluate runtime health and enforce safe mode if needed.

        Args:
            deploy_score:  BootDeployabilityEngine score (0–100)
            ws_score:      WsStabilityEngine.stability_score() (0–100)
            data_health:   DataHealthMonitor.check().health_score (0–100)
            gate_allowed:  optional pre-computed GlobalGate.can_trade()

        Returns EnforcerResult; check safe_mode_active before signal processing.
        """
        self._last_eval_ts = time.time()
        triggers: List[str] = []

        if deploy_score < cfg.SME_DEPLOY_LOW_THRESHOLD:
            triggers.append(
                f"DEPLOY_LOW({deploy_score:.1f}<{cfg.SME_DEPLOY_LOW_THRESHOLD})"
            )
        if ws_score < cfg.SME_WS_LOW_THRESHOLD:
            triggers.append(
                f"WS_LOW({ws_score:.1f}<{cfg.SME_WS_LOW_THRESHOLD})"
            )
        if data_health < cfg.SME_DATA_LOW_THRESHOLD:
            triggers.append(
                f"DATA_LOW({data_health:.1f}<{cfg.SME_DATA_LOW_THRESHOLD})"
            )
        if gate_allowed is False:
            triggers.append("GLOBAL_GATE_BLOCKED")

        triggered_now = False
        if triggers:
            reason = " | ".join(triggers)
            if not safe_mode_controller.is_active:
                triggered_now = True
                self._activations += 1
            safe_mode_controller.activate(f"ENFORCER: {reason}")
            gate_logger.log_safe_mode(
                reason=reason,
                enforcer="SafeModeEnforcer",
                detail=f"deploy={deploy_score:.1f} ws={ws_score:.1f} data={data_health:.1f}",
            )
        else:
            # All clear — check if safe mode can be auto-resumed
            if safe_mode_controller.is_active:
                resumed = safe_mode_controller.check_auto_resume(
                    current_score=deploy_score
                )
                if resumed:
                    logger.info(
                        f"[SAFE-MODE-ENFORCER] Safe mode auto-resumed "
                        f"(deploy={deploy_score:.1f})"
                    )

        reason_str = " | ".join(triggers) if triggers else "ALL_CLEAR"
        return EnforcerResult(
            safe_mode_active=safe_mode_controller.is_active,
            safe_mode_triggered=triggered_now,
            deploy_score=round(deploy_score, 1),
            ws_score=round(ws_score, 1),
            data_health=round(data_health, 1),
            triggers=triggers,
            reason=reason_str,
        )

    def is_system_safe(self) -> bool:
        """Quick check: True when safe mode is NOT active."""
        return not safe_mode_controller.is_active

    def summary(self) -> dict:
        return {
            "safe_mode_active": safe_mode_controller.is_active,
            "total_activations": self._activations,
            "last_eval_age_sec": round(time.time() - self._last_eval_ts, 1)
                                 if self._last_eval_ts else None,
            "thresholds": {
                "deploy": cfg.SME_DEPLOY_LOW_THRESHOLD,
                "ws":     cfg.SME_WS_LOW_THRESHOLD,
                "data":   cfg.SME_DATA_LOW_THRESHOLD,
            },
            "module": "SAFE_MODE_ENFORCER",
            "phase":  "6.6",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
safe_mode_enforcer = SafeModeEnforcer()

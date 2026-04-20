"""
EOW Quant Engine — core/profit/gate_aware_controller.py
Phase 7A: Gate-Aware Execution Controller

Central ON/OFF switch for the entire Phase 7A profit engine.
All profit modules query this controller before operating.

Three permission tiers (each is a strict subset of the previous):
    allow_profit_engine(gate_status) → full profit engine (ranking + concentration + competition)
    allow_scanning(gate_status)      → signal generation
    allow_amplification(gate_status) → edge amplification (most conservative)

Golden Rule:
    gate.can_trade == False → everything STOPS.
    gate.safe_mode == True  → scanning stops; amplification disabled.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from core.gating.gate_logger import gate_logger


@dataclass
class EnginePermission:
    profit_engine: bool   # full profit pipeline allowed
    scanning:      bool   # signal generation allowed
    amplification: bool   # edge amplification allowed
    reason:        str    # human-readable explanation


class GateAwareController:
    """
    Master permission authority for the Phase 7A profit engine.

    Accepts the gate_status dict from GlobalGateController.evaluate() and
    derives layered permissions for every profit subsystem.

    Usage (read-only — never mutate gate_status here):
        gac = GateAwareController()
        allowed = gac.allow_profit_engine(gate_status)
    """

    def __init__(self):
        logger.info("[GATE-AWARE-CTRL] Phase 7A activated — profit engine gated")

    # ── Permission queries ────────────────────────────────────────────────────

    def allow_profit_engine(self, gate_status: dict) -> bool:
        """
        Full profit engine (ranking + capital concentration + competition).
        Requires: can_trade=True AND safe_mode=False.
        """
        return bool(
            gate_status.get("can_trade", False)
            and not gate_status.get("safe_mode", True)
        )

    def allow_scanning(self, gate_status: dict) -> bool:
        """
        Signal generation / market scanning.
        Requires: can_trade=True AND safe_mode=False.
        Same as allow_profit_engine — no scanning in safe mode.
        """
        return self.allow_profit_engine(gate_status)

    def allow_amplification(self, gate_status: dict) -> bool:
        """
        Edge amplification (TP/trail boost).
        Disabled in safe mode or when trading is blocked.
        Most conservative permission — same conditions as profit engine.
        """
        if gate_status.get("safe_mode", True):
            return False
        return bool(gate_status.get("can_trade", False))

    def permissions(self, gate_status: dict) -> EnginePermission:
        """
        Return all three permission tiers at once with a reason string.
        Useful for logging and dashboard display.
        """
        can_trade = bool(gate_status.get("can_trade", False))
        safe_mode = bool(gate_status.get("safe_mode", True))
        gate_reason = gate_status.get("reason", "UNKNOWN")

        if not can_trade:
            reason = f"GATE_BLOCKED({gate_reason})"
            perm = EnginePermission(
                profit_engine=False, scanning=False,
                amplification=False, reason=reason,
            )
        elif safe_mode:
            reason = f"SAFE_MODE_ACTIVE — scanning+amplification disabled"
            perm = EnginePermission(
                profit_engine=False, scanning=False,
                amplification=False, reason=reason,
            )
        else:
            perm = EnginePermission(
                profit_engine=True, scanning=True,
                amplification=True, reason="ALL_CLEAR",
            )

        if not perm.profit_engine:
            gate_logger.blocked(reason=perm.reason, context="ProfitEngine")
        return perm

    def summary(self) -> dict:
        return {
            "module": "GATE_AWARE_CONTROLLER",
            "phase":  "7A",
            "description": "Central permission authority for profit engine",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
gate_aware_controller = GateAwareController()

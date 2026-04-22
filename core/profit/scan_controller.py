"""
EOW Quant Engine — core/profit/scan_controller.py
Phase 7A / qFTD-010: Scan Controller — Signal Generation Authority

Design principle (qFTD-010): Signal generation is ALWAYS ON.
Gate state controls EXECUTION only — never signal generation.

Interface:
    scan_controller.can_scan(gate_status: dict) -> ScanDecision
    → Always returns ScanDecision(allowed=True, reason="SCAN_OK")

    Execution gating is handled downstream in ExecutionOrchestrator.run_cycle()
    and in the _execution_allowed check in main.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from core.profit.gate_aware_controller import gate_aware_controller
from core.gating.gate_logger import gate_logger


@dataclass
class ScanDecision:
    allowed: bool
    reason:  str   # "SCAN_OK" or descriptive block reason


_NO_SCAN_SAFE_MODE = ScanDecision(allowed=False, reason="NO_SCAN:SAFE_MODE")
_NO_SCAN_GATE      = ScanDecision(allowed=False, reason="NO_SCAN:GATE_BLOCKED")
_SCAN_OK           = ScanDecision(allowed=True,  reason="SCAN_OK")


class ScanController:
    """
    Signal generation authority for the EOW Quant Engine.

    qFTD-010: can_scan() always permits signal generation regardless of gate state.
    Gate state is used only for execution control (ExecutionOrchestrator.run_cycle).
    """

    def __init__(self):
        logger.info("[SCAN-CTRL] Phase 7A activated — signal generation ALWAYS ON (qFTD-010)")
        self._total_blocked: int = 0
        self._total_allowed: int = 0

    def can_scan(self, gate_status: dict) -> ScanDecision:
        """
        Signal generation is always permitted — qFTD-010 architectural principle.

        Gate state (can_trade / safe_mode) controls EXECUTION only.
        Callers that need to block execution should check gate_status directly
        or use ExecutionOrchestrator.run_cycle().

        Args:
            gate_status: dict from GlobalGateController.evaluate() (informational)

        Returns:
            ScanDecision(allowed=True, reason="SCAN_OK") unconditionally.
        """
        self._total_allowed += 1
        logger.debug(
            f"[SCAN-CTRL] Heartbeat — scanning active "
            f"(can_trade={gate_status.get('can_trade')}, safe_mode={gate_status.get('safe_mode')})"
        )
        return _SCAN_OK

    def enforce_no_scan(self, gate_status: dict) -> None:
        """
        Hard enforcement guard — raises immediately if a scan is attempted
        while the system is in SAFE MODE or the gate is blocked.

        Call this at any scan entry-point where a silent bypass would be
        a critical error.  Unlike can_scan(), there is no return value —
        either the call is allowed (no exception) or the system crashes.

        Args:
            gate_status: dict from GlobalGateController.evaluate()

        Raises:
            RuntimeError: if can_trade is False or safe_mode is True
        """
        if not gate_status.get("can_trade", False) or gate_status.get("safe_mode", True):
            decision = _NO_SCAN_GATE if not gate_status.get("can_trade") else _NO_SCAN_SAFE_MODE
            raise RuntimeError(
                f"CRITICAL: Scan attempted in SAFE MODE — {decision.reason}"
            )

    def summary(self) -> dict:
        total = self._total_allowed + self._total_blocked
        return {
            "total_allowed": self._total_allowed,
            "total_blocked": self._total_blocked,
            "block_rate":    round(self._total_blocked / total, 4) if total else 0.0,
            "module": "SCAN_CONTROLLER",
            "phase":  "7A",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
scan_controller = ScanController()

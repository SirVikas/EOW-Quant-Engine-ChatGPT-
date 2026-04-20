"""
EOW Quant Engine — core/profit/scan_controller.py
Phase 7A: Scan Controller — Signal Generation Gate

First check in the profit pipeline. Stops ALL signal generation when the
system is in safe mode or when the gate has blocked trading.

Interface:
    scan_controller.can_scan(gate_status: dict) -> ScanDecision

    ScanDecision.allowed == False → return NO_SIGNALS immediately;
                                    skip the entire strategy evaluation path.

Design principle: cheap — called on every tick before any indicator work.
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
    Lightweight gate between the tick stream and the signal generation path.

    Checks gate_status on every call — no caching, no state.
    The GlobalGateController already caches its result for GGL_CACHE_TTL_SEC;
    we just consume it.
    """

    def __init__(self):
        logger.info("[SCAN-CTRL] Phase 7A activated — signal generation gated")
        self._total_blocked: int = 0
        self._total_allowed: int = 0

    def can_scan(self, gate_status: dict) -> ScanDecision:
        """
        Determine whether market scanning / signal generation is permitted.

        Args:
            gate_status: dict from GlobalGateController.evaluate()

        Returns:
            ScanDecision(allowed=True)  → proceed with signal generation
            ScanDecision(allowed=False) → abort; return NO_SIGNALS
        """
        if not gate_status.get("can_trade", False):
            self._total_blocked += 1
            gate_logger.blocked(
                reason=f"SCAN_BLOCKED:{gate_status.get('reason', 'GATE')}",
                context="ScanController",
            )
            return _NO_SCAN_GATE

        if gate_status.get("safe_mode", True):
            self._total_blocked += 1
            gate_logger.blocked(
                reason="SCAN_BLOCKED:SAFE_MODE",
                context="ScanController",
            )
            return _NO_SCAN_SAFE_MODE

        self._total_allowed += 1
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
        decision = self.can_scan(gate_status)
        if not decision.allowed:
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

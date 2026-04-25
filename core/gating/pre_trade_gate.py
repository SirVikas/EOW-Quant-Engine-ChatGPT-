"""
EOW Quant Engine — core/gating/pre_trade_gate.py
Phase 6.6: Pre-Trade Gate — Final per-trade permission check

Last line of defence before any order is placed.  Consumes the
gate_status dict produced by GlobalGateController.evaluate() and
applies additional per-trade checks.

Interface (spec-compliant):
    gate.check(gate_status: dict) -> {
        "allowed":  bool,
        "reason":   str,   — "OK" or first failure reason
        "managed":  bool,  — True if existing positions may be managed
    }

Four-step chain:
    1. gate_status["can_trade"]   — GlobalGate master permission
    2. safe_mode can_trade        — SafeModeEngine state
    3. indicator_ok               — PTG_REQUIRE_INDICATORS
    4. data_fresh                 — PTG_REQUIRE_DATA_FRESH

check_manage_only() always returns True (management never blocked at this layer).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger

from config import cfg
from core.gating.gate_logger import gate_logger
from core.gating.safe_mode_engine import safe_mode_engine as _default_sme, SafeModeEngine


@dataclass
class PreTradeResult:
    allowed: bool
    reason:  str
    managed: bool = True   # position management is always permitted


class PreTradeGate:
    """
    Per-trade gate that runs inline before every order attempt.

    Designed to be fast — all heavy evaluation has already occurred
    in GlobalGateController.evaluate(); this class just interprets the
    cached result and applies any extra per-trade requirements.
    """

    def __init__(self, safe_mode: Optional[SafeModeEngine] = None):
        self._sme = safe_mode if safe_mode is not None else _default_sme
        logger.info(
            f"[PRE-TRADE-GATE] Phase 6.6 activated | "
            f"require_indicators={cfg.PTG_REQUIRE_INDICATORS} "
            f"require_data_fresh={cfg.PTG_REQUIRE_DATA_FRESH}"
        )

    # ── Primary interface ─────────────────────────────────────────────────────

    def check(
        self,
        gate_status: dict,
        *,
        indicator_ok: bool = True,
        data_fresh:   bool = True,
        symbol:       str  = "",
        strategy:     str  = "",
    ) -> dict:
        """
        Validate that a new trade may be opened.

        Args:
            gate_status:   dict from GlobalGateController.evaluate()
            indicator_ok:  per-symbol indicator readiness (caller-supplied)
            data_fresh:    per-symbol data freshness (caller-supplied)
            symbol:        trading pair for log context
            strategy:      strategy name for log context

        Returns:
            {"allowed": bool, "reason": str, "managed": bool}
        """
        ctx = f"{symbol}/{strategy}" if symbol and strategy else (symbol or strategy)

        # Step 1 — GlobalGate master permission
        if not gate_status.get("can_trade", False):
            reason = gate_status.get("reason", "GATE_BLOCKED")
            gate_logger.blocked(reason=reason, context=ctx)
            return self._result(False, reason)

        # Step 2 — SafeModeEngine state
        if not self._sme.can_trade:
            reason = f"SAFE_MODE_ACTIVE({self._sme.mode.value})"
            gate_logger.blocked(reason=reason, context=ctx)
            return self._result(False, reason)

        # Step 3 — Indicator readiness
        # qFTD-032: use GlobalGate's own _ind_ready verdict rather than the
        # caller-supplied indicator_ok. During BOOT_GRACE GlobalGate sets
        # _ind_ready=True unconditionally; if we instead checked the caller's
        # guard.ok (actual per-symbol readiness = False at boot) we were
        # double-blocking trades that GlobalGate had already authorised.
        _ind_ok_effective = gate_status.get("_ind_ready", indicator_ok)
        if cfg.PTG_REQUIRE_INDICATORS and not _ind_ok_effective:
            reason = "INDICATORS_NOT_READY"
            gate_logger.blocked(reason=reason, context=ctx)
            return self._result(False, reason)

        # Step 4 — Data freshness
        if cfg.PTG_REQUIRE_DATA_FRESH and not data_fresh:
            reason = "DATA_NOT_FRESH"
            gate_logger.blocked(reason=reason, context=ctx)
            return self._result(False, reason)

        # All clear
        gate_logger.allowed(context=ctx)
        return self._result(True, "OK")

    def check_manage_only(self) -> dict:
        """
        Check whether existing positions may be managed (SL/TP moves etc.).
        Returns True unless SafeModeEngine is in BLOCKED state.
        """
        managed = self._sme.can_manage
        if not managed:
            logger.warning("[PRE-TRADE-GATE] Position management blocked — BLOCKED state")
        return {"allowed": False, "reason": "MANAGE_ONLY", "managed": managed}

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _result(allowed: bool, reason: str) -> dict:
        return {"allowed": allowed, "reason": reason, "managed": True}


# ── Module-level singleton ────────────────────────────────────────────────────
pre_trade_gate = PreTradeGate()

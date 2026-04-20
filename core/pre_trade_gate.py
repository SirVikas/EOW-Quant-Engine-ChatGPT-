"""
EOW Quant Engine — Phase 6.6: Pre-Trade Validation Gate
Final mandatory check immediately before every trade execution.

Position in the decision chain:
  ... → EdgeAmplifier → PRE-TRADE GATE → ExecutionEngine

This gate is the last line of defence. Even if all upstream checks
passed (ranker, competition, capital concentrator), this gate
re-validates current system state at the precise moment of execution.

Checks performed (in order):
  1. SafeModeController.can_open_new_trade()  — safe mode hard block
  2. GlobalGateController.can_trade()         — cached master gate
  3. Indicator freshness (if PTG_REQUIRE_INDICATORS)
  4. Data freshness     (if PTG_REQUIRE_DATA_FRESH)

On any failure:
  • Trade is rejected with structured reason
  • GateLogger records the block event
  • Execution engine never receives the order

On pass:
  • GateLogger records ALLOWED (only if PTG_LOG_ALLOWED=True)
  • ExecutionEngine may proceed

Non-negotiable:
  No bypass. No exceptions. No try/except that silently allows trades.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger

from config import cfg
from core.gate_logger import gate_logger
from core.global_gate import global_gate
from core.safe_mode import safe_mode_controller


@dataclass
class TradePermission:
    allowed:     bool
    reason:      str
    symbol:      str = ""
    strategy:    str = ""
    gate_source: str = ""   # which check rejected it


class PreTradeGate:
    """
    Final validation gate before trade execution.

    Integrates with GlobalGateController (master permission) and
    SafeModeController (runtime protection). Logs every decision
    through GateLogger for full audit trail.

    Usage (in execution path):
        perm = pre_trade_gate.check(
            symbol="BTCUSDT",
            strategy="TrendFollowing",
            indicator_ok=indicator_validator.is_ready(),
            data_fresh=dhm.last_result().ok if dhm.last_result() else False,
        )
        if not perm.allowed:
            return  # do NOT proceed to execution

        execution_engine.execute(...)
    """

    def __init__(self):
        self._total_checks: int = 0
        self._total_blocked: int = 0
        logger.info(
            f"[PRE-TRADE-GATE] Phase 6.6 activated | "
            f"require_indicators={cfg.PTG_REQUIRE_INDICATORS} "
            f"require_data_fresh={cfg.PTG_REQUIRE_DATA_FRESH} "
            f"log_allowed={cfg.PTG_LOG_ALLOWED}"
        )

    def check(
        self,
        symbol:          str   = "",
        strategy:        str   = "",
        indicator_ok:    Optional[bool] = None,
        data_fresh:      Optional[bool] = None,
    ) -> TradePermission:
        """
        Run all pre-trade checks and return a TradePermission.

        Args:
            symbol:        trading symbol (for logging context)
            strategy:      strategy name (for logging context)
            indicator_ok:  current IndicatorValidator result; if None and
                           PTG_REQUIRE_INDICATORS=True → treated as False
            data_fresh:    current DataHealthMonitor ok; if None and
                           PTG_REQUIRE_DATA_FRESH=True → treated as False

        Returns TradePermission; check allowed before calling executor.
        """
        self._total_checks += 1
        context = f"{symbol}/{strategy}" if symbol else strategy

        # ── Check 1: Safe mode hard block ─────────────────────────────────────
        if not safe_mode_controller.can_open_new_trade():
            return self._block(
                reason="SAFE_MODE_ACTIVE",
                gate_source="SafeModeController",
                context=context,
                symbol=symbol,
                strategy=strategy,
            )

        # ── Check 2: Global gate cached result ────────────────────────────────
        if not global_gate.can_trade():
            last = global_gate.last_result()
            reason = last.reason if last else "GLOBAL_GATE_BLOCKED"
            return self._block(
                reason=reason,
                gate_source="GlobalGateController",
                context=context,
                symbol=symbol,
                strategy=strategy,
            )

        # ── Check 3: Indicator freshness ──────────────────────────────────────
        if cfg.PTG_REQUIRE_INDICATORS:
            effective_ind = indicator_ok if indicator_ok is not None else False
            if not effective_ind:
                return self._block(
                    reason="INDICATOR_NOT_READY",
                    gate_source="IndicatorValidator",
                    context=context,
                    symbol=symbol,
                    strategy=strategy,
                )

        # ── Check 4: Data freshness ───────────────────────────────────────────
        if cfg.PTG_REQUIRE_DATA_FRESH:
            effective_data = data_fresh if data_fresh is not None else False
            if not effective_data:
                return self._block(
                    reason="DATA_NOT_FRESH",
                    gate_source="DataHealthMonitor",
                    context=context,
                    symbol=symbol,
                    strategy=strategy,
                )

        # ── All passed ────────────────────────────────────────────────────────
        gate_logger.log_allowed(context=context)
        logger.debug(f"[PRE-TRADE-GATE] ALLOWED | {context}")
        return TradePermission(
            allowed=True,
            reason="ALL_CHECKS_PASSED",
            symbol=symbol,
            strategy=strategy,
            gate_source="PreTradeGate",
        )

    def check_manage_only(self, symbol: str = "") -> bool:
        """
        For position management calls (SL/TP updates, partial closes).
        Always True — safe mode never blocks management of existing trades.
        """
        return safe_mode_controller.can_manage_existing()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _block(
        self,
        reason: str,
        gate_source: str,
        context: str,
        symbol: str,
        strategy: str,
    ) -> TradePermission:
        self._total_blocked += 1
        gate_logger.log_blocked(reason=reason, context=context, detail=gate_source)
        logger.warning(
            f"[PRE-TRADE-GATE] BLOCKED | reason={reason} "
            f"source={gate_source} context={context}"
        )
        return TradePermission(
            allowed=False,
            reason=reason,
            symbol=symbol,
            strategy=strategy,
            gate_source=gate_source,
        )

    def summary(self) -> dict:
        block_rate = (self._total_blocked / self._total_checks
                      if self._total_checks > 0 else 0.0)
        return {
            "total_checks":  self._total_checks,
            "total_blocked": self._total_blocked,
            "block_rate":    round(block_rate, 4),
            "require_indicators": cfg.PTG_REQUIRE_INDICATORS,
            "require_data_fresh": cfg.PTG_REQUIRE_DATA_FRESH,
            "module": "PRE_TRADE_GATE",
            "phase":  "6.6",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
pre_trade_gate = PreTradeGate()

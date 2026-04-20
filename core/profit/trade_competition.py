"""
EOW Quant Engine — core/profit/trade_competition.py
Phase 7A: Gate-Aware Trade Competition Engine

Thin gate-aware wrapper around core.trade_competition.TradeCompetitionEngine.

Rule:
    if not gate_controller.allow_profit_engine(gate_status):
        return CompetitionResult(winners=[], losers=candidates, ...)

All selection logic (top-N, tie-breaking) is delegated to the Phase 7
TradeCompetitionEngine singleton when the gate is clear.
"""
from __future__ import annotations

from typing import List

from loguru import logger

from core.trade_competition import (
    TradeCompetitionEngine,
    TradeCandidate,
    CompetitionResult,
    trade_competition_engine as _base_engine,
)
from core.profit.gate_aware_controller import gate_aware_controller
from core.gating.gate_logger import gate_logger


class GateAwareCompetitionEngine:
    """
    Gate-aware facade for TradeCompetitionEngine.

    Returns an empty winners list (all candidates moved to losers) when
    the profit engine is gated off — ensuring zero trades enter the
    execution path in that state.
    """

    def __init__(self, base: TradeCompetitionEngine = _base_engine):
        self._base = base
        logger.info("[PROFIT-COMPETITION] Phase 7A gate-aware competition engine activated")

    def select(
        self,
        gate_status: dict,
        candidates: List[TradeCandidate],
    ) -> CompetitionResult:
        """
        Gate-checked candidate selection.

        Returns:
            CompetitionResult(winners=[...])  when gate allows.
            CompetitionResult(winners=[])     when gate is blocked.
        """
        if not gate_aware_controller.allow_profit_engine(gate_status):
            reason = gate_status.get("reason", "GATE_BLOCKED")
            gate_logger.blocked(
                reason=f"COMPETITION_SKIP:{reason}",
                context="TradeCompetition",
            )
            logger.debug(
                f"[PROFIT-COMPETITION] Competition disabled — gate={reason} "
                f"candidates={len(candidates)}"
            )
            # Increment base cycle counter so cycle_id remains monotonic
            self._base._cycle += 1
            return CompetitionResult(
                winners=[],
                losers=list(candidates),
                cycle_id=self._base._cycle,
            )

        return self._base.select(candidates)

    def summary(self) -> dict:
        s = self._base.summary()
        s["gate_aware"] = True
        s["phase"] = "7A"
        return s


# ── Module-level singleton ────────────────────────────────────────────────────
trade_competition_engine = GateAwareCompetitionEngine()

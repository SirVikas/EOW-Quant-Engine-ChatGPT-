"""
EOW Quant Engine — core/profit/trade_ranker.py
Phase 7A: Gate-Aware Trade Ranker

Thin gate-aware wrapper around core.trade_ranker.TradeRanker.
Adds a mandatory gate check before every ranking call.

Rule:
    if not gate_controller.allow_profit_engine(gate_status):
        return None   # disable ranking entirely

When gate is clear, delegates to the underlying TradeRanker unchanged.
The existing Phase 7 RankResult dataclass and scoring logic are preserved.
"""
from __future__ import annotations

from typing import Optional

from loguru import logger

from core.trade_ranker import TradeRanker, RankResult, trade_ranker as _base_ranker
from core.profit.gate_aware_controller import gate_aware_controller
from core.gating.gate_logger import gate_logger


class GateAwareTradeRanker:
    """
    Gate-aware facade for TradeRanker.

    Delegates all ranking logic to the Phase 7 TradeRanker singleton.
    Returns None instead of a RankResult when the profit engine is gated off.

    Args (same as TradeRanker.rank):
        gate_status:   dict from GlobalGateController.evaluate()
        ev:            Expected Value (USDT / unit risk)
        trade_score:   Adaptive scorer composite (0–1)
        regime:        Market regime string
        strategy:      Strategy name
        history_score: Optional EdgeMemory override (0–1)
    """

    def __init__(self, base: TradeRanker = _base_ranker):
        self._base = base
        logger.info("[PROFIT-RANKER] Phase 7A gate-aware trade ranker activated")

    def rank(
        self,
        gate_status:   dict,
        ev:            float,
        trade_score:   float,
        regime:        str,
        strategy:      str,
        history_score: Optional[float] = None,
    ) -> Optional[RankResult]:
        """
        Gate-checked rank.

        Returns:
            RankResult  when gate allows and ranking proceeds normally.
            None        when gate is blocked or safe mode is active.
        """
        if not gate_aware_controller.allow_profit_engine(gate_status):
            reason = gate_status.get("reason", "GATE_BLOCKED")
            gate_logger.blocked(reason=f"RANK_SKIP:{reason}", context=f"{strategy}")
            logger.debug(f"[PROFIT-RANKER] Ranking disabled — gate={reason}")
            return None

        return self._base.rank(
            ev=ev,
            trade_score=trade_score,
            regime=regime,
            strategy=strategy,
            history_score=history_score,
        )

    def summary(self) -> dict:
        s = self._base.summary()
        s["gate_aware"] = True
        s["phase"] = "7A"
        return s


# ── Module-level singleton ────────────────────────────────────────────────────
trade_ranker = GateAwareTradeRanker()

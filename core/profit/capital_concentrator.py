"""
EOW Quant Engine — core/profit/capital_concentrator.py
Phase 7A: Gate-Aware Capital Concentrator

Thin gate-aware wrapper around core.capital_concentrator.CapitalConcentrator.

Rule:
    if not gate_controller.allow_profit_engine(gate_status):
        return base_allocation   ← safe fallback, no concentration boost

"Base allocation" means size_multiplier=1.0 (upstream_mult only, no band boost),
so positions are sized conservatively and the system stays within normal limits
without any concentration enhancement.
"""
from __future__ import annotations

from loguru import logger
from config import cfg

from core.capital_concentrator import (
    CapitalConcentrator,
    ConcentrationResult,
    capital_concentrator as _base_cc,
)
from core.profit.gate_aware_controller import gate_aware_controller
from core.gating.gate_logger import gate_logger


# Safe fallback returned when gate is blocked
def _safe_fallback(base_risk_usdt: float, upstream_mult: float) -> ConcentrationResult:
    """Return a neutral 1× result — no concentration, no rejection."""
    safe_risk = base_risk_usdt * upstream_mult
    return ConcentrationResult(
        ok=True,
        size_multiplier=round(upstream_mult, 4),
        band="SAFE_FALLBACK",
        capped=False,
        max_risk_usdt=round(safe_risk, 4),
        reason="CC_SAFE_FALLBACK(gate_blocked→base_allocation)",
    )


class GateAwareCapitalConcentrator:
    """
    Gate-aware facade for CapitalConcentrator.

    When gate is clear: delegates to Phase 7 CapitalConcentrator which
    applies band-based concentration boosts.

    When gate is blocked / safe mode: returns base allocation (upstream_mult
    only, band multiplier = 1.0) so trades are not oversized during degraded
    conditions.
    """

    def __init__(self, base: CapitalConcentrator = _base_cc):
        self._base = base
        logger.info(
            "[PROFIT-CONCENTRATOR] Phase 7A gate-aware capital concentrator activated"
        )

    def concentrate(
        self,
        gate_status:    dict,
        rank_score:     float,
        equity:         float,
        base_risk_usdt: float,
        upstream_mult:  float = 1.0,
        ev:             float = 0.0,   # Phase 7B: direct EV for secondary sizing
    ) -> ConcentrationResult:
        """
        Gate-checked capital concentration.

        Args:
            gate_status:    dict from GlobalGateController.evaluate()
            rank_score:     from TradeRanker.rank() (0–1)
            equity:         current account equity (USDT)
            base_risk_usdt: raw risk USDT before any multiplier
            upstream_mult:  combined multiplier from DD+LossCluster+CapAllocator
            ev:             Phase 7B — direct EV value passed to base concentrator

        Returns:
            ConcentrationResult with band boost when gate allows.
            ConcentrationResult with base_allocation (no boost) when gated off.
        """
        if not gate_aware_controller.allow_profit_engine(gate_status):
            reason = gate_status.get("reason", "GATE_BLOCKED")
            gate_logger.blocked(
                reason=f"CONCENTRATE_FALLBACK:{reason}",
                context="CapitalConcentrator",
            )
            logger.debug(
                f"[PROFIT-CONCENTRATOR] Concentration disabled — "
                f"returning base_allocation | gate={reason}"
            )
            return _safe_fallback(base_risk_usdt, upstream_mult)

        result = self._base.concentrate(
            rank_score=rank_score,
            equity=equity,
            base_risk_usdt=base_risk_usdt,
            upstream_mult=upstream_mult,
            ev=ev,
        )
        # PAPER_SPEED forensic fix:
        # In stress mode, low rank should not hard-stop execution flow.
        if (cfg.TRADE_MODE == "PAPER" and cfg.PAPER_SPEED_MODE and not result.ok):
            logger.debug(
                f"[PROFIT-CONCENTRATOR] PAPER_SPEED fallback — bypass reject: {result.reason}"
            )
            return _safe_fallback(base_risk_usdt, upstream_mult)
        return result

    def record_risk_used(self, risk_usdt: float) -> None:
        self._base.record_risk_used(risk_usdt)

    def summary(self) -> dict:
        s = self._base.summary()
        s["gate_aware"] = True
        s["phase"] = "7A"
        return s


# ── Module-level singleton ────────────────────────────────────────────────────
capital_concentrator = GateAwareCapitalConcentrator()

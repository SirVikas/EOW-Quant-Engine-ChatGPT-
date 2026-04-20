"""
EOW Quant Engine — core/profit/edge_amplifier.py
Phase 7A: Gate-Aware Edge Amplifier

Thin gate-aware wrapper around core.edge_amplifier.EdgeAmplifier.

Rule:
    if safe_mode OR not can_trade:
        disable_all_amplification()   → return AmplifyResult(amplified=False, tp×1.0, trail×1.0)

Amplification is the highest-risk profit enhancement — it widens TP targets
and increases trailing aggressiveness. It is therefore the first to be
disabled when system health degrades.
"""
from __future__ import annotations

from loguru import logger

from core.edge_amplifier import (
    EdgeAmplifier,
    AmplifyResult,
    edge_amplifier as _base_amp,
)
from core.profit.gate_aware_controller import gate_aware_controller
from core.gating.gate_logger import gate_logger


# Canonical no-amplification result returned in unsafe state
_NO_AMP = AmplifyResult(
    amplified=False,
    tp_multiplier=1.0,
    trail_multiplier=1.0,
    reason="NO_AMPLIFY:SAFE_MODE_OR_GATE_BLOCKED",
)


class GateAwareEdgeAmplifier:
    """
    Gate-aware facade for EdgeAmplifier.

    Disables all amplification when:
      • gate_status["safe_mode"] is True, OR
      • gate_status["can_trade"] is False.

    When the gate is fully clear, delegates to the Phase 7 EdgeAmplifier
    which checks its own four conditions (ev, rank, regime, volume).
    """

    def __init__(self, base: EdgeAmplifier = _base_amp):
        self._base = base
        logger.info(
            "[PROFIT-AMPLIFIER] Phase 7A gate-aware edge amplifier activated"
        )

    def evaluate(
        self,
        gate_status:  dict,
        ev:           float,
        rank_score:   float,
        regime:       str,
        volume_ratio: float,
    ) -> AmplifyResult:
        """
        Gate-checked amplification evaluation.

        Args:
            gate_status:  dict from GlobalGateController.evaluate()
            ev:           Expected value from EVEngine
            rank_score:   Composite rank from TradeRanker
            regime:       Current market regime string
            volume_ratio: current_volume / avg_volume

        Returns:
            AmplifyResult from EdgeAmplifier when gate allows.
            AmplifyResult(amplified=False, tp×1.0, trail×1.0) when gated off.
        """
        if not gate_aware_controller.allow_amplification(gate_status):
            reason = (
                "SAFE_MODE"
                if gate_status.get("safe_mode", True)
                else gate_status.get("reason", "GATE_BLOCKED")
            )
            gate_logger.blocked(
                reason=f"AMPLIFY_DISABLED:{reason}",
                context="EdgeAmplifier",
            )
            logger.debug(
                f"[PROFIT-AMPLIFIER] Amplification disabled — {reason}"
            )
            return _NO_AMP

        return self._base.evaluate(
            ev=ev,
            rank_score=rank_score,
            regime=regime,
            volume_ratio=volume_ratio,
        )

    def summary(self) -> dict:
        s = self._base.summary()
        s["gate_aware"] = True
        s["phase"] = "7A"
        return s


# ── Module-level singleton ────────────────────────────────────────────────────
edge_amplifier = GateAwareEdgeAmplifier()

"""
EOW Quant Engine — FTD-008: Cost Guard
Final pre-execution check that trade cost is proportionate to expected profit.

Rule:
  cost > expected_profit × MAX_COST_FRACTION  →  BLOCK TRADE

MAX_COST_FRACTION is set in config (currently 0.10 = 10%).
This prevents executing trades where fees erode the edge before the market moves.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class CostGuardResult:
    ok:              bool
    cost_fraction:   float  # cost / expected_profit (or 0 if expected_profit ≤ 0)
    reason:          str = ""


def is_cost_valid(expected_profit: float, cost: float) -> bool:
    """
    Returns True when cost is within the allowed fraction of expected profit.
    Always returns False when expected_profit ≤ 0 (no positive edge to trade against).
    """
    if expected_profit <= 0:
        logger.debug("[COST-GUARD] BLOCK — expected_profit ≤ 0")
        return False

    fraction = cost / expected_profit
    if fraction > cfg.MAX_COST_FRACTION:
        logger.debug(
            f"[COST-GUARD] BLOCK cost_fraction={fraction:.3f} "
            f"> max={cfg.MAX_COST_FRACTION}"
        )
        return False

    return True


def check_cost(expected_profit: float, cost: float) -> CostGuardResult:
    """
    Structured variant — returns CostGuardResult for gate-log compatibility.
    Prefer is_cost_valid() for simple boolean gates.
    """
    if expected_profit <= 0:
        return CostGuardResult(
            ok=False,
            cost_fraction=0.0,
            reason="EXPECTED_PROFIT_NON_POSITIVE",
        )

    fraction = round(cost / expected_profit, 4)
    if fraction > cfg.MAX_COST_FRACTION:
        return CostGuardResult(
            ok=False,
            cost_fraction=fraction,
            reason=f"COST_TOO_HIGH({fraction:.3f}>{cfg.MAX_COST_FRACTION})",
        )

    return CostGuardResult(ok=True, cost_fraction=fraction, reason="COST_PASS")

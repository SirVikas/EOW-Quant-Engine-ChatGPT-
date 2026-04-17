"""
EOW Quant Engine — Strategy Engine  (FTD-REF-026)
Tracks per-strategy usage distribution across all closed trades this session.

Reports:
  • Usage % per strategy type (TrendFollowing / MeanReversion / VolatilityExpansion)
  • Active strategies — those used in ≥ ACTIVE_THRESH (5%) of trades
  • Warning when only 1 strategy is active after MIN_TRADES_FOR_WARN trades

Wired in main.py:
  strategy_engine.record_trade(strategy_type)  — called on every trade close.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from loguru import logger


# ── Constants ─────────────────────────────────────────────────────────────────
ACTIVE_THRESH        = 0.05   # strategy is "active" if usage fraction ≥ this
MIN_TRADES_FOR_WARN  = 10     # need this many trades before single-strategy warning

MIN_SIGNAL_RR        = 1.2    # aligned with signal_filter RR gate (was 1.5)
MIN_SIGNAL_CONFIDENCE = 0.25  # aligned with regime_ai MIN_CONFIDENCE_TRADE (was 0.5)
BLOCKED_REGIMES      = {"UNSTABLE"}
REQUIRED_CANDLE_MIN  = 30     # sufficient for ATR+EMA indicators (was 50)

KNOWN_STRATEGIES: tuple = (
    "TrendFollowing",
    "MeanReversion",
    "VolatilityExpansion",
)


@dataclass
class StrategyDecision:
    ok: bool
    reason: str = ""


class StrategyEngine:
    """
    Stateful strategy usage tracker.
    Thread-safe for a single asyncio event loop.

    Usage:
      strategy_engine.record_trade("TrendFollowing")
      summary = strategy_engine.summary()
    """

    def __init__(self):
        self._counts: Dict[str, int] = {}
        self._total: int = 0

    # ── Public ────────────────────────────────────────────────────────────────

    def record_trade(self, strategy_type: str):
        """Call once for every closed trade with its strategy type."""
        key = strategy_type or "Unknown"
        self._counts[key] = self._counts.get(key, 0) + 1
        self._total += 1
        logger.debug(f"[STRAT-ENG] Recorded trade for {key} (total={self._total})")

    def usage(self) -> Dict[str, float]:
        """
        Return usage fraction (0.0–1.0) per known strategy type.
        Returns 0.0 for strategies not yet seen.
        """
        if self._total == 0:
            return {s: 0.0 for s in KNOWN_STRATEGIES}
        return {
            s: round(self._counts.get(s, 0) / self._total, 4)
            for s in KNOWN_STRATEGIES
        }

    def active_strategies(self) -> List[str]:
        """Return list of strategy names with usage fraction ≥ ACTIVE_THRESH."""
        return [s for s, u in self.usage().items() if u >= ACTIVE_THRESH]

    def evaluate_signal(self, rr: float, confidence: float, regime: str) -> StrategyDecision:
        """Hard quality gate used before order submission."""
        if (regime or "").upper() in BLOCKED_REGIMES:
            return StrategyDecision(False, f"REGIME_BLOCKED({regime})")
        if rr < MIN_SIGNAL_RR:
            return StrategyDecision(False, f"LOW_RR({rr:.2f}<{MIN_SIGNAL_RR:.2f})")
        if confidence < MIN_SIGNAL_CONFIDENCE:
            return StrategyDecision(False, f"LOW_CONFIDENCE({confidence:.2f}<{MIN_SIGNAL_CONFIDENCE:.2f})")
        return StrategyDecision(True, "")

    @staticmethod
    def evaluate_data_sufficiency(candle_buffer: int, required_min: int = REQUIRED_CANDLE_MIN) -> str:
        if candle_buffer < required_min:
            return "NO_TRADE_DATA_INSUFFICIENT"
        return "OK"

    def summary(self) -> dict:
        """Full summary dict suitable for the /api/strategy-usage endpoint."""
        u      = self.usage()
        active = self.active_strategies()
        warn   = (
            len(active) <= 1
            and self._total >= MIN_TRADES_FOR_WARN
        )
        if warn:
            label = active[0] if active else "none"
            logger.warning(
                f"[STRAT-ENG] ⚠ Only 1 strategy active: {label} "
                f"dominates after {self._total} trades."
            )
        return {
            "total_trades":      self._total,
            "strategy_usage":    {s: f"{v * 100:.1f}%" for s, v in u.items()},
            "usage_fractions":   u,
            "active_strategies": active,
            "warning":           f"⚠ Only 1 strategy active ({active[0] if active else 'none'} dominates)" if warn else "",
            "quality_gate": {
                "min_rr": MIN_SIGNAL_RR,
                "min_confidence": MIN_SIGNAL_CONFIDENCE,
                "blocked_regimes": sorted(BLOCKED_REGIMES),
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
strategy_engine = StrategyEngine()

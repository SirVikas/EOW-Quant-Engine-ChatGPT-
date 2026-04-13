"""
EOW Quant Engine — Indicator Guard
Validates indicator quality before a signal is acted upon.

Blocks trades when:
  - Not enough candles (< MIN_CANDLES) — insufficient history
  - ADX < ADX_UNSTABLE_BELOW — market is noise, no directional info
  - ATR% < ATR_PCT_MIN — near-zero volatility / illiquid bar

Silently clamps (does NOT block) when:
  - ADX > ADX_CLAMP_ABOVE — data artifact or extreme market; capped to 80
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from loguru import logger


# ── Thresholds ────────────────────────────────────────────────────────────────
MIN_CANDLES        = 30     # minimum history before any signal is valid
ADX_UNSTABLE_BELOW =  5.0  # ADX < 5 → randomwalk / noise regime
ADX_CLAMP_ABOVE    = 80.0  # ADX > 80 → clamp to 80 (data artefact)
ATR_PCT_MIN        =  0.05 # ATR% < 0.05% → effectively zero volatility


@dataclass
class GuardResult:
    ok:      bool
    reason:  str   = ""     # populated only when ok=False
    adx:     float = 0.0    # possibly clamped ADX
    atr_pct: float = 0.0


class IndicatorGuard:
    """
    Stateless validator — no per-symbol memory required.
    Call validate() before forwarding any signal to risk_ctrl.
    """

    def validate(
        self,
        symbol:    str,
        n_candles: int,
        adx:       float,
        atr_pct:   float,
        closes:    Optional[List[float]] = None,   # reserved for future checks
    ) -> GuardResult:
        """
        Returns GuardResult(ok=True) when safe to trade.
        Returns GuardResult(ok=False, reason=…) when the signal should be dropped.
        ADX is silently clamped to ADX_CLAMP_ABOVE if it exceeds that value.
        """
        # 1. Candle count guard
        if n_candles < MIN_CANDLES:
            return GuardResult(
                ok=False,
                reason=f"INSUFFICIENT_CANDLES({n_candles}<{MIN_CANDLES})",
                adx=adx, atr_pct=atr_pct,
            )

        # 2. ADX lower bound (unstable / noisy market)
        if 0 < adx < ADX_UNSTABLE_BELOW:
            return GuardResult(
                ok=False,
                reason=f"ADX_UNSTABLE({adx:.1f}<{ADX_UNSTABLE_BELOW})",
                adx=adx, atr_pct=atr_pct,
            )

        # 3. ADX upper clamp — normalise, don't block
        clamped_adx = adx
        if adx > ADX_CLAMP_ABOVE:
            clamped_adx = ADX_CLAMP_ABOVE
            logger.debug(
                f"[IND-GUARD] {symbol} ADX={adx:.1f} clamped → {ADX_CLAMP_ABOVE}"
            )

        # 4. ATR% floor — skip illiquid / stalled bars
        if atr_pct < ATR_PCT_MIN:
            return GuardResult(
                ok=False,
                reason=f"ATR_TOO_LOW({atr_pct:.4f}%<{ATR_PCT_MIN}%)",
                adx=clamped_adx, atr_pct=atr_pct,
            )

        return GuardResult(ok=True, adx=clamped_adx, atr_pct=atr_pct)

    def validate_from_state(self, symbol: str, n_candles: int, state) -> GuardResult:
        """
        Convenience wrapper that accepts a RegimeState dataclass directly.
        """
        return self.validate(
            symbol    = symbol,
            n_candles = n_candles,
            adx       = getattr(state, "adx", 0.0),
            atr_pct   = getattr(state, "atr_pct", 0.0),
        )


# ── Module-level singleton ────────────────────────────────────────────────────
indicator_guard = IndicatorGuard()

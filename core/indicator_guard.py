"""
EOW Quant Engine — Indicator Guard  (FTD-REF-MASTER-001 upgraded)
Validates indicator quality before a signal is acted upon.

Block conditions:
  - n_candles < MIN_CANDLES           → INSUFFICIENT_CANDLES
  - adx is None (no data yet)         → ADX_NOT_READY
  - adx < ADX_UNSTABLE_BELOW (< 5)   → ADX_UNSTABLE (noise / random walk)
  - atr_pct < ATR_PCT_MIN (< 0.015%) → ATR_TOO_LOW (illiquid bar)

Warn / degrade conditions (trade allowed but flagged):
  - adx < ADX_WEAK_BELOW (< 10)      → adx_quality = "WEAK"

Clamp (do NOT block, normalise):
  - adx > ADX_CLAMP_ABOVE (> 60)     → silently clamped to 60
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from loguru import logger


# ── Thresholds ────────────────────────────────────────────────────────────────
MIN_CANDLES        = 30     # minimum history before any signal is valid
ADX_UNSTABLE_BELOW =  5.0  # hard block — pure noise
ADX_WEAK_BELOW     = 10.0  # soft warning — low trend confidence
ADX_CLAMP_ABOVE    = 60.0  # clamp ceiling (was 80 — tightened per MASTER-001)
ATR_PCT_MIN        =  0.005 # qFTD-032-R4: 0.010→0.005% — BTCUSDT/BNBUSDT at 0.008-0.009% during quiet markets; strategy modules independently enforce volatility quality

AdxQuality = Literal["STRONG", "WEAK", "UNSTABLE", "NOT_READY"]


@dataclass
class GuardResult:
    ok:          bool
    reason:      str        = ""      # populated only when ok=False
    adx:         float      = 0.0     # possibly clamped ADX
    atr_pct:     float      = 0.0
    adx_quality: AdxQuality = "STRONG"


class IndicatorGuard:
    """
    Stateless validator — no per-symbol memory required.
    Call validate() before forwarding any signal to risk_ctrl.
    """

    def validate(
        self,
        symbol:    str,
        n_candles: int,
        adx:       Optional[float],   # None = ADX not computable yet
        atr_pct:   float,
        closes:    Optional[List[float]] = None,
    ) -> GuardResult:
        """
        Returns GuardResult(ok=True) when safe to trade.
        Returns GuardResult(ok=False, reason=…) to drop the signal.
        ADX is silently clamped to ADX_CLAMP_ABOVE if it exceeds that value.
        """
        # 1. Candle count guard
        if n_candles < MIN_CANDLES:
            return GuardResult(
                ok=False,
                reason=f"INSUFFICIENT_CANDLES({n_candles}<{MIN_CANDLES})",
                adx=adx or 0.0, atr_pct=atr_pct, adx_quality="NOT_READY",
            )

        # 2. ADX None guard (insufficient data to compute)
        if adx is None:
            return GuardResult(
                ok=False,
                reason="ADX_NOT_READY",
                adx=0.0, atr_pct=atr_pct, adx_quality="NOT_READY",
            )

        # 3. Hard ADX lower bound (unstable / noisy)
        if 0 < adx < ADX_UNSTABLE_BELOW:
            return GuardResult(
                ok=False,
                reason=f"ADX_UNSTABLE({adx:.1f}<{ADX_UNSTABLE_BELOW})",
                adx=adx, atr_pct=atr_pct, adx_quality="UNSTABLE",
            )

        # 4. ADX upper clamp — normalise, never block
        clamped_adx = adx
        if adx > ADX_CLAMP_ABOVE:
            clamped_adx = ADX_CLAMP_ABOVE
            logger.debug(
                f"[IND-GUARD] {symbol} ADX={adx:.1f} clamped → {ADX_CLAMP_ABOVE}"
            )

        # 5. Soft ADX warning (trade proceeds, quality flagged)
        adx_quality: AdxQuality = "STRONG"
        if 0 <= clamped_adx < ADX_WEAK_BELOW:
            adx_quality = "WEAK"
            logger.debug(
                f"[IND-GUARD] {symbol} ADX={clamped_adx:.1f} < {ADX_WEAK_BELOW} → WEAK"
            )

        # 6. ATR% floor — skip illiquid / stalled bars
        if atr_pct < ATR_PCT_MIN:
            return GuardResult(
                ok=False,
                reason=f"ATR_TOO_LOW({atr_pct:.4f}%<{ATR_PCT_MIN}%)",
                adx=clamped_adx, atr_pct=atr_pct, adx_quality=adx_quality,
            )

        return GuardResult(
            ok=True, adx=clamped_adx, atr_pct=atr_pct, adx_quality=adx_quality
        )

    def validate_from_state(self, symbol: str, n_candles: int, state) -> GuardResult:
        """
        Convenience wrapper that accepts a RegimeState dataclass directly.
        Passes None for ADX when the state has adx=0 AND n_candles < 2*14
        (the minimum for Wilder's ADX).
        """
        raw_adx = getattr(state, "adx", 0.0)
        # Treat adx=0.0 as None when candles are borderline — avoids false passes
        adx: Optional[float] = raw_adx if (raw_adx > 0 or n_candles >= 28) else None
        return self.validate(
            symbol    = symbol,
            n_candles = n_candles,
            adx       = adx,
            atr_pct   = getattr(state, "atr_pct", 0.0),
        )


# ── Module-level singleton ────────────────────────────────────────────────────
indicator_guard = IndicatorGuard()

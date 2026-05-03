"""
EOW Quant Engine — Adaptive Mode Engine
Tri-modal execution router. Eliminates NO_TRADE_SESSION.

The system is always in exactly one execution mode:

  TREND_FOLLOW  — ADX ≥ threshold: high-momentum breakout / pullback (alpha_engine)
  RANGE_SCALP   — ADX < threshold, market not crashing: BB + CVD range scalp
  SHORT_HUNT    — CVD slope strongly negative + selling imbalance: crash/dump short

Mode selection is stateless — recalculated every tick from live regime + CVD data,
so the system switches within milliseconds of market structure changing.

Integration:
  Call adaptive_mode_engine.decide() after every candle close with current
  regime state and CVD state.  Pass returned ExecMode to the signal router
  (main.py / orchestrator) to select which strategy generates the next signal.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger

from config import cfg
from core.cvd_tracker import CVDState


class ExecMode(str, Enum):
    TREND_FOLLOW = "TREND_FOLLOW"   # alpha_engine: TCB / PBE
    RANGE_SCALP  = "RANGE_SCALP"    # range_scalper: BB + CVD
    SHORT_HUNT   = "SHORT_HUNT"     # short-biased alpha: institutional sell detected


@dataclass
class ModeDecision:
    mode:        ExecMode
    reason:      str
    adx:         float  = 0.0
    cvd_slope:   float  = 0.0
    imbalance:   float  = 0.5


class AdaptiveModeEngine:
    """
    Stateless tri-modal router.
    decide() returns the correct ExecMode for the current market tick.
    No "no-trade" output exists — SHORT_HUNT fires instead of silence.
    """

    # SHORT_HUNT: CVD slope below this fraction of price → crash/dump signal
    _SHORT_HUNT_SLOPE_PCT  = -0.015   # CVD slope < -1.5% of price
    _SHORT_HUNT_IMBAL_MAX  = 0.38     # imbalance < 38% buy → sell pressure confirmed

    def decide(
        self,
        regime:    str,
        adx:       float,
        price:     float,
        cvd_state: Optional[CVDState],
    ) -> ModeDecision:
        """
        Returns an ExecMode every tick. Never returns None — system is always active.

        Priority order:
          1. SHORT_HUNT  — overrides regime when dump is detected
          2. TREND_FOLLOW — ADX confirms directional momentum
          3. RANGE_SCALP  — default for all other market states
        """
        slope     = cvd_state.cvd_slope  if cvd_state else 0.0
        imbalance = cvd_state.imbalance  if cvd_state else 0.5

        # ── 1. SHORT_HUNT: institutional sell pressure override ───────────────
        hunt_threshold = price * self._SHORT_HUNT_SLOPE_PCT if price > 0 else -1e9
        if slope < hunt_threshold and imbalance < self._SHORT_HUNT_IMBAL_MAX:
            decision = ModeDecision(
                mode=ExecMode.SHORT_HUNT,
                reason=(
                    f"DUMP: CVD_slope={slope:.4f}<{hunt_threshold:.4f} "
                    f"imbal={imbalance:.2f}<{self._SHORT_HUNT_IMBAL_MAX}"
                ),
                adx=adx, cvd_slope=slope, imbalance=imbalance,
            )
            logger.info(
                f"[ADAPTIVE-MODE] SHORT_HUNT activated | "
                f"slope={slope:.4f} imbal={imbalance:.2f} adx={adx:.1f}"
            )
            return decision

        # ── 2. TREND_FOLLOW: ADX confirms directional momentum ────────────────
        if adx >= cfg.REGIME_ADX_THRESHOLD:
            return ModeDecision(
                mode=ExecMode.TREND_FOLLOW,
                reason=f"TREND: ADX={adx:.1f}≥{cfg.REGIME_ADX_THRESHOLD} regime={regime}",
                adx=adx, cvd_slope=slope, imbalance=imbalance,
            )

        # ── 3. RANGE_SCALP: default for low-ADX, non-crash conditions ─────────
        return ModeDecision(
            mode=ExecMode.RANGE_SCALP,
            reason=f"RANGE: ADX={adx:.1f}<{cfg.REGIME_ADX_THRESHOLD} → BB+CVD scalp",
            adx=adx, cvd_slope=slope, imbalance=imbalance,
        )

    def summary(self) -> dict:
        return {
            "module": "ADAPTIVE_MODE_ENGINE",
            "modes":  [m.value for m in ExecMode],
            "short_hunt_slope_pct":  self._SHORT_HUNT_SLOPE_PCT,
            "short_hunt_imbal_max":  self._SHORT_HUNT_IMBAL_MAX,
        }


# ── Module-level singleton ─────────────────────────────────────────────────────
adaptive_mode_engine = AdaptiveModeEngine()

"""
EOW Quant Engine — Market Structure Detector  (FTD-REF-024)
Identifies the current market structure to prevent trading in hostile conditions.

Structures detected:
  TREND          — directional move: ADX strong + BB width expanding
  RANGE          — choppy market: ADX weak + BB width tight (mean-reversion)
  FAKE_BREAKOUT  — ADX in ambiguous range but BB contracting (failed move)
  LOW_VOL_TRAP   — near-zero ATR% → spread + fees dominate any theoretical edge
  UNKNOWN        — mixed signals; other gates will decide

Tradeable:   TREND, RANGE, UNKNOWN
Blocked:     FAKE_BREAKOUT, LOW_VOL_TRAP
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from loguru import logger


# ── Detection thresholds ───────────────────────────────────────────────────────
ADX_TREND_MIN     = 20.0    # ADX ≥ this + BB wide → TREND
ADX_RANGE_MAX     = 15.0    # ADX < this + BB tight → RANGE
BB_TREND_MIN      = 3.5     # BB width ≥ this in a trending market
BB_RANGE_MAX      = 2.5     # BB width < this in a ranging market
BB_FAKE_MAX       = 3.0     # ADX ambiguous + BB below this → FAKE_BREAKOUT
ATR_FAKE_MAX      = 0.15    # additionally ATR% must be low for fake-breakout
ATR_LOW_VOL_TRAP  = 0.08    # ATR% below this → trade costs eat all edge

# ── Status constants ───────────────────────────────────────────────────────────
STRUCTURE_TREND         = "TREND"
STRUCTURE_RANGE         = "RANGE"
STRUCTURE_FAKE_BREAKOUT = "FAKE_BREAKOUT"
STRUCTURE_LOW_VOL_TRAP  = "LOW_VOL_TRAP"
STRUCTURE_UNKNOWN       = "UNKNOWN"

TRADEABLE_STRUCTURES = frozenset({STRUCTURE_TREND, STRUCTURE_RANGE, STRUCTURE_UNKNOWN})


@dataclass
class MarketStructureResult:
    structure:    str
    confidence:   float       # 0.0 – 1.0
    tradeable:    bool
    block_reason: str         # non-empty when tradeable=False
    adx_val:      float
    bb_width_val: float
    atr_pct_val:  float
    notes:        str


class MarketStructureDetector:
    """
    Stateless market structure classifier.
    Call detect() on every tick / candle close.
    """

    def detect(
        self,
        adx:      float,
        bb_width: float,
        atr_pct:  float,
        closes:   Optional[List[float]] = None,   # reserved for future price-action checks
    ) -> MarketStructureResult:
        """
        Classify market structure from current indicator snapshot.
        Priority: LOW_VOL_TRAP → FAKE_BREAKOUT → TREND → RANGE → UNKNOWN
        """

        # ── 1. Low volatility trap (highest-priority block) ───────────────────
        if atr_pct < ATR_LOW_VOL_TRAP:
            return self._mk(
                STRUCTURE_LOW_VOL_TRAP,
                confidence=min(0.95, 1.0 - atr_pct / ATR_LOW_VOL_TRAP),
                tradeable=False,
                block_reason=(
                    f"LOW_VOL_TRAP(ATR%={atr_pct:.3f}<{ATR_LOW_VOL_TRAP})"
                ),
                adx=adx, bb_width=bb_width, atr_pct=atr_pct,
                notes="ATR% too low — fees/spread dominate any edge",
            )

        # ── 2. Fake breakout: ADX ambiguous + BB contracting + low ATR% ───────
        if (ADX_RANGE_MAX <= adx < ADX_TREND_MIN
                and bb_width < BB_FAKE_MAX
                and atr_pct < ATR_FAKE_MAX):
            return self._mk(
                STRUCTURE_FAKE_BREAKOUT,
                confidence=0.75,
                tradeable=False,
                block_reason=(
                    f"FAKE_BREAKOUT(ADX={adx:.1f} "
                    f"BB={bb_width:.2f}<{BB_FAKE_MAX} "
                    f"ATR%={atr_pct:.3f})"
                ),
                adx=adx, bb_width=bb_width, atr_pct=atr_pct,
                notes="ADX ambiguous + BB contracting → breakout likely failed",
            )

        # ── 3. Trend (ADX strong + BB wide) ───────────────────────────────────
        if adx >= ADX_TREND_MIN and bb_width >= BB_TREND_MIN:
            adx_score = min(1.0, adx / 50.0)
            bb_score  = min(1.0, bb_width / 8.0)
            conf      = min(0.95, 0.5 * adx_score + 0.5 * bb_score)
            return self._mk(
                STRUCTURE_TREND,
                confidence=conf,
                tradeable=True,
                block_reason="",
                adx=adx, bb_width=bb_width, atr_pct=atr_pct,
                notes=f"ADX={adx:.1f}≥{ADX_TREND_MIN} BB={bb_width:.2f}≥{BB_TREND_MIN}",
            )

        # ── 4. Range (ADX weak + BB tight) ────────────────────────────────────
        if adx < ADX_RANGE_MAX and bb_width < BB_RANGE_MAX:
            adx_score = 1.0 - adx / ADX_RANGE_MAX
            bb_score  = 1.0 - bb_width / BB_RANGE_MAX
            conf      = min(0.90, 0.5 * adx_score + 0.5 * bb_score)
            return self._mk(
                STRUCTURE_RANGE,
                confidence=conf,
                tradeable=True,
                block_reason="",
                adx=adx, bb_width=bb_width, atr_pct=atr_pct,
                notes=f"ADX={adx:.1f}<{ADX_RANGE_MAX} BB={bb_width:.2f}<{BB_RANGE_MAX}",
            )

        # ── 5. Unknown — mixed signals ─────────────────────────────────────────
        return self._mk(
            STRUCTURE_UNKNOWN,
            confidence=0.30,
            tradeable=True,
            block_reason="",
            adx=adx, bb_width=bb_width, atr_pct=atr_pct,
            notes=f"ADX={adx:.1f} BB={bb_width:.2f} — ambiguous; other gates apply",
        )

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _mk(
        structure: str,
        confidence: float,
        tradeable: bool,
        block_reason: str,
        adx: float,
        bb_width: float,
        atr_pct: float,
        notes: str,
    ) -> MarketStructureResult:
        logger.debug(
            f"[MKT-STRUCT] {structure} conf={confidence:.2f} "
            f"tradeable={tradeable} | {notes}"
        )
        return MarketStructureResult(
            structure=structure,
            confidence=round(confidence, 3),
            tradeable=tradeable,
            block_reason=block_reason,
            adx_val=adx,
            bb_width_val=bb_width,
            atr_pct_val=atr_pct,
            notes=notes,
        )


# ── Module-level singleton ────────────────────────────────────────────────────
market_structure_detector = MarketStructureDetector()

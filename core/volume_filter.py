"""
EOW Quant Engine — Volume Sleep Mode Filter  (Phase 3)

Blocks new entries when per-candle volume is significantly below the rolling
24-candle mean.  Dead/sideways markets have thin volume; fees dominate any
small price move → "quality trades only, not quantity".

Logic:
  • Maintain a 24-candle rolling volume deque per symbol (seeded at bootstrap).
  • Before signal execution: check current_volume / mean(last 24) ≥ threshold.
  • If below threshold → DORMANT → skip signal with SLEEP_MODE reason.
  • If not enough history (< VOLUME_LOOKBACK bars) → allow trading (cold-start safe).
"""
from __future__ import annotations

from collections import deque
from loguru import logger


VOLUME_THRESHOLD_PCT = 0.60   # current candle volume must be ≥ 60% of 24-candle rolling mean
VOLUME_LOOKBACK      = 24     # rolling window in candles (= 24 minutes)


class VolumeFilter:
    """
    Stateless sleep-mode gate.
    Accepts the symbol's candle_volume_buffer deque and checks the latest bar.
    """

    def is_active(self, symbol: str, volume_buffer: deque) -> tuple[bool, str]:
        """
        Returns (active, reason).
          active=True  → volume sufficient, safe to proceed with signal.
          active=False → market is dormant, skip signal.
        """
        vols = list(volume_buffer)
        if len(vols) < VOLUME_LOOKBACK:
            return True, ""   # insufficient history — do not block cold-start

        avg_vol = sum(vols[-VOLUME_LOOKBACK:]) / VOLUME_LOOKBACK
        current_vol = vols[-1]

        if avg_vol <= 0:
            return True, ""

        ratio = current_vol / avg_vol
        if ratio < VOLUME_THRESHOLD_PCT:
            reason = (
                f"SLEEP_MODE(vol={current_vol:.0f}"
                f"={ratio*100:.0f}%_of_avg={avg_vol:.0f},"
                f"min={VOLUME_THRESHOLD_PCT*100:.0f}%)"
            )
            logger.debug(f"[VOL-FILTER] {symbol} dormant — {reason}")
            return False, reason
        return True, ""


# ── Module-level singleton ─────────────────────────────────────────────────────
volume_filter = VolumeFilter()

"""
EOW Quant Engine — Volume Sleep Mode Filter  (Phase 3, updated Phase 5.2)

Blocks new entries when per-candle volume is significantly below the rolling
24-candle mean.  Dead/sideways markets have thin volume; fees dominate any
small price move → "quality trades only, not quantity".

Phase 5.2: is_active() now accepts an optional vol_multiplier from the
DynamicThresholdProvider, relaxing the threshold when the system has been
in a no-trade freeze. BASE_VOLUME_THRESHOLD_PCT is the cold-start baseline;
effective threshold = BASE * vol_multiplier (clamped to [0.10, 1.0]).
"""
from __future__ import annotations

from collections import deque
from loguru import logger


BASE_VOLUME_THRESHOLD_PCT = 0.60   # baseline: current ≥ 60% of 24-candle mean
VOLUME_LOOKBACK           = 24     # rolling window in candles (= 24 minutes)


class VolumeFilter:
    """
    Dynamic sleep-mode gate.
    Threshold is adjusted at runtime via vol_multiplier from DynamicThresholdProvider.
    """

    def is_active(
        self,
        symbol:        str,
        volume_buffer: deque,
        vol_multiplier: float = 1.0,
    ) -> tuple[bool, str]:
        """
        Returns (active, reason).
          active=True  → volume sufficient, safe to proceed with signal.
          active=False → market is dormant, skip signal.

        Args:
            vol_multiplier: from DynamicThresholdProvider (0.20–1.0).
                            1.0 = normal; <1.0 = relaxed (allows lower-volume signals).
        """
        vols = list(volume_buffer)
        if len(vols) < VOLUME_LOOKBACK:
            return True, ""   # insufficient history — do not block cold-start

        avg_vol     = sum(vols[-VOLUME_LOOKBACK:]) / VOLUME_LOOKBACK
        current_vol = vols[-1]

        if avg_vol <= 0:
            return True, ""

        # Effective threshold: BASE × multiplier, clamped to [0.10, 1.0]
        effective_threshold = max(0.10, min(1.0, BASE_VOLUME_THRESHOLD_PCT * vol_multiplier))
        ratio = current_vol / avg_vol

        if ratio < effective_threshold:
            reason = (
                f"SLEEP_MODE(vol={current_vol:.0f}"
                f"={ratio*100:.0f}%_of_avg={avg_vol:.0f},"
                f"min={effective_threshold*100:.0f}%"
                f"[base={BASE_VOLUME_THRESHOLD_PCT*100:.0f}%×{vol_multiplier:.2f}])"
            )
            logger.debug(f"[VOL-FILTER] {symbol} dormant — {reason}")
            return False, reason
        return True, ""


# ── Module-level singleton ─────────────────────────────────────────────────────
volume_filter = VolumeFilter()

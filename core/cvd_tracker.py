"""
EOW Quant Engine — CVD Tracker
Cumulative Volume Delta from OHLCV candle data.

CVD approximates order flow using the Tick Rule:
  signed_vol = volume × (close − open) / (high − low + ε)
  CVD = rolling Σ(signed_vol)

Positive CVD slope → buying pressure dominant  → confirms LONG entries
Negative CVD slope → selling pressure dominant → confirms SHORT entries / SHORT_HUNT mode

No exchange WebSocket required — computed entirely from public candle data
already present in the existing price buffers.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class CVDState:
    symbol:    str
    cvd:       float    # current cumulative delta
    cvd_slope: float    # CVD change over last SLOPE_WINDOW candles
    imbalance: float    # buy_vol / total_vol  (>0.5 = buy pressure; <0.5 = sell)
    candles_n: int      # effective window used for slope


class CVDTracker:
    """
    Per-symbol sliding CVD buffer. Feed closed candles via push(); query via get().
    Thread-safe for a single asyncio event loop.
    """
    SLOPE_WINDOW = 10    # candles used for CVD slope / imbalance
    MAX_BUFFER   = 200   # rolling history depth per symbol

    def __init__(self):
        self._signed_vol: Dict[str, deque] = {}
        self._cvd_series: Dict[str, deque] = {}
        self._states:     Dict[str, CVDState] = {}

    # ── Public ───────────────────────────────────────────────────────────────

    def push(
        self,
        symbol: str,
        open_:  float,
        high:   float,
        low:    float,
        close:  float,
        volume: float,
    ):
        """Feed one closed candle. Call on the same candle-close event as regime_detector.push()."""
        self._init(symbol)

        hl = high - low
        if hl > 0:
            signed = volume * (close - open_) / hl
        elif close >= open_:
            signed = volume
        else:
            signed = -volume

        self._signed_vol[symbol].append(signed)

        prev_cvd = self._cvd_series[symbol][-1] if self._cvd_series[symbol] else 0.0
        self._cvd_series[symbol].append(prev_cvd + signed)

        self._states[symbol] = self._compute(symbol)

    def get(self, symbol: str) -> Optional[CVDState]:
        return self._states.get(symbol)

    def all_states(self) -> Dict[str, CVDState]:
        return dict(self._states)

    # ── Private ──────────────────────────────────────────────────────────────

    def _init(self, symbol: str):
        if symbol not in self._signed_vol:
            self._signed_vol[symbol] = deque(maxlen=self.MAX_BUFFER)
            self._cvd_series[symbol] = deque(maxlen=self.MAX_BUFFER)

    def _compute(self, symbol: str) -> CVDState:
        cvd_hist = list(self._cvd_series[symbol])
        vol_hist = list(self._signed_vol[symbol])

        n      = min(self.SLOPE_WINDOW, len(cvd_hist))
        cvd    = cvd_hist[-1] if cvd_hist else 0.0
        slope  = (cvd_hist[-1] - cvd_hist[-n]) if len(cvd_hist) >= n and n > 1 else 0.0

        recent = vol_hist[-n:]
        buy_v  = sum(v for v in recent if v > 0)
        sell_v = sum(abs(v) for v in recent if v < 0)
        total  = buy_v + sell_v
        imbal  = buy_v / total if total > 0 else 0.5

        return CVDState(
            symbol=symbol,
            cvd=round(cvd, 6),
            cvd_slope=round(slope, 6),
            imbalance=round(imbal, 4),
            candles_n=n,
        )


# ── Module-level singleton ─────────────────────────────────────────────────────
cvd_tracker = CVDTracker()

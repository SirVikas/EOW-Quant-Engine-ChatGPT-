"""
EOW Quant Engine — Regime Detector
Autonomously classifies market as: TRENDING | MEAN_REVERTING | VOLATILITY_EXPANSION
Uses ADX, ATR, Bollinger Band Width, and autocorrelation.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import math
from loguru import logger

from config import cfg


class Regime(str, Enum):
    TRENDING           = "TRENDING"
    MEAN_REVERTING     = "MEAN_REVERTING"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    UNKNOWN            = "UNKNOWN"


@dataclass
class RegimeState:
    symbol:     str
    regime:     Regime
    adx:        float
    atr:        float
    atr_pct:    float      # ATR / price * 100
    bb_width:   float      # Bollinger Band width %
    confidence: float      # 0–1
    ts:         int


class RegimeDetector:
    """
    For each symbol, maintains a rolling window of prices and computes
    regime classification every time a new candle closes.
    """

    def __init__(self):
        self._price_buf:  Dict[str, deque] = {}
        self._high_buf:   Dict[str, deque] = {}
        self._low_buf:    Dict[str, deque] = {}
        self._states:     Dict[str, RegimeState] = {}
        self._period = max(cfg.ATR_PERIOD, cfg.BB_PERIOD, 28)  # enough for ADX
        self.safe_mode: bool = False  # Phase 7A.3: hard block set by gate controller

    # ── Public ──────────────────────────────────────────────────────────────

    def push(self, symbol: str, close: float, high: float, low: float, ts: int):
        """Feed a new closed candle into the detector."""
        if self.safe_mode:
            return  # hard block — gate is down or safe mode active
        self._init_bufs(symbol)
        self._price_buf[symbol].append(close)
        self._high_buf[symbol].append(high)
        self._low_buf[symbol].append(low)

        if len(self._price_buf[symbol]) < self._period:
            return   # not enough data yet

        state = self._classify(symbol, close, ts)
        self._states[symbol] = state
        logger.debug(f"[REGIME] {symbol} → {state.regime.value} "
                     f"(ADX={state.adx:.1f} ATR%={state.atr_pct:.2f})")

    def get(self, symbol: str) -> Regime:
        return self._states.get(symbol, RegimeState(
            symbol, Regime.UNKNOWN, 0, 0, 0, 0, 0, 0)).regime

    def state(self, symbol: str) -> Optional[RegimeState]:
        return self._states.get(symbol)

    def all_states(self) -> Dict[str, RegimeState]:
        return dict(self._states)

    # ── Private ─────────────────────────────────────────────────────────────

    def _init_bufs(self, symbol: str):
        if symbol not in self._price_buf:
            self._price_buf[symbol] = deque(maxlen=self._period + 5)
            self._high_buf[symbol]  = deque(maxlen=self._period + 5)
            self._low_buf[symbol]   = deque(maxlen=self._period + 5)

    def _classify(self, symbol: str, price: float, ts: int) -> RegimeState:
        closes = list(self._price_buf[symbol])
        highs  = list(self._high_buf[symbol])
        lows   = list(self._low_buf[symbol])
        n      = cfg.ATR_PERIOD

        atr       = self._atr(highs, lows, closes, n)
        atr_pct   = (atr / price * 100) if price else 0
        adx       = self._adx(highs, lows, closes, 14)
        bb_width  = self._bb_width(closes, cfg.BB_PERIOD, cfg.BB_STD)

        # Historical ATR percentile for volatility expansion
        # Simple approach: compare current ATR to 10-period rolling average ATR
        recent_atrs = [self._atr(highs[i:i+n+1], lows[i:i+n+1], closes[i:i+n+1], n)
                       for i in range(max(0, len(closes)-10-n), max(0, len(closes)-n))]
        avg_atr  = sum(recent_atrs) / len(recent_atrs) if recent_atrs else atr
        vol_ratio = atr / avg_atr if avg_atr else 1.0

        # ── Decision Logic ─────────────────────────────────────────────────
        if vol_ratio >= cfg.REGIME_ATR_MULT and bb_width > 4.0:
            regime     = Regime.VOLATILITY_EXPANSION
            confidence = min(0.95, (vol_ratio - 1.0) * 0.5)
        elif adx >= cfg.REGIME_ADX_THRESHOLD:
            regime     = Regime.TRENDING
            confidence = min(0.95, (adx - cfg.REGIME_ADX_THRESHOLD) / 25)
        else:
            regime     = Regime.MEAN_REVERTING
            confidence = min(0.95, (cfg.REGIME_ADX_THRESHOLD - adx) / cfg.REGIME_ADX_THRESHOLD)

        return RegimeState(
            symbol=symbol, regime=regime,
            adx=round(adx, 2), atr=round(atr, 6),
            atr_pct=round(atr_pct, 3), bb_width=round(bb_width, 3),
            confidence=round(confidence, 3), ts=ts,
        )

    # ── Indicators ──────────────────────────────────────────────────────────

    @staticmethod
    def _atr(highs: List[float], lows: List[float], closes: List[float], n: int) -> float:
        if len(highs) < n + 1:
            return 0.0
        trs = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i]  - closes[i-1]),
            )
            trs.append(tr)
        return sum(trs[-n:]) / n

    @staticmethod
    def _adx(highs: List[float], lows: List[float], closes: List[float], n: int = 14) -> float:
        """Wilder's ADX."""
        if len(highs) < n * 2:
            return 0.0

        dm_plus, dm_minus, trs = [], [], []
        for i in range(1, len(highs)):
            up   = highs[i]  - highs[i-1]
            down = lows[i-1] - lows[i]
            dm_plus.append(max(up, 0)   if up > down else 0)
            dm_minus.append(max(down, 0) if down > up  else 0)
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i]  - closes[i-1]),
            )
            trs.append(tr)

        def wilder_smooth(data, period):
            s = sum(data[:period])
            result = [s]
            for x in data[period:]:
                s = s - s / period + x
                result.append(s)
            return result

        atr14   = wilder_smooth(trs, n)
        dmp14   = wilder_smooth(dm_plus, n)
        dmm14   = wilder_smooth(dm_minus, n)

        di_values = []
        for a, p, m in zip(atr14, dmp14, dmm14):
            if a == 0:
                di_values.append(0)
                continue
            di_p = 100 * p / a
            di_m = 100 * m / a
            dx   = 100 * abs(di_p - di_m) / (di_p + di_m) if (di_p + di_m) else 0
            di_values.append(dx)

        if len(di_values) < n:
            return 0.0
        return sum(di_values[-n:]) / n

    @staticmethod
    def _bb_width(closes: List[float], period: int, std_mult: float) -> float:
        """Bollinger Band width as % of middle band."""
        if len(closes) < period:
            return 0.0
        window  = closes[-period:]
        mean    = sum(window) / period
        var     = sum((x - mean) ** 2 for x in window) / period
        std     = math.sqrt(var)
        upper   = mean + std_mult * std
        lower   = mean - std_mult * std
        return ((upper - lower) / mean * 100) if mean else 0.0

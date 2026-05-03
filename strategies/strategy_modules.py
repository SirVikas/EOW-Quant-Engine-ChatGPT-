"""
EOW Quant Engine — Strategy Modules
Three interchangeable modules selected by the Regime Detector.
Each exposes: generate_signal(symbol, price_buf, candle) → Signal | None
"""
from __future__ import annotations
import math
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from config import cfg


class Signal(str, Enum):
    LONG  = "LONG"
    SHORT = "SHORT"
    EXIT  = "EXIT"
    NONE  = "NONE"


@dataclass
class TradeSignal:
    symbol:      str
    signal:      Signal
    entry_price: float
    stop_loss:   float
    take_profit: float
    confidence:  float      # 0–1
    strategy_id: str
    reason:      str


# ── Safety Filters ───────────────────────────────────────────────────────────
# Minimum ATR% to even consider a trade.
# Stablecoins: ATR% ≈ 0.002–0.05%  → blocked
# Real coins:  ATR% ≈ 0.1%+        → allowed
MIN_ATR_PCT = 0.05   # raised 0.015→0.05: SL_dist = ATR*2.5; at 0.015% SL is only 0.04% — sub-tick noise on BTC/XRP

# ── Shared Indicator Helpers ─────────────────────────────────────────────────

def _ema(prices: List[float], period: int) -> float:
    if len(prices) < period:
        return prices[-1] if prices else 0
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1 - k)
    return e


def _rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, period + 1):
        d = prices[-(period + 1) + i] - prices[-(period + 1) + i - 1]
        (gains if d > 0 else losses).append(abs(d))
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def _atr(highs: List[float], lows: List[float], closes: List[float], n: int) -> float:
    if len(highs) < n + 1:
        return 0.0
    trs = [max(highs[i] - lows[i],
               abs(highs[i] - closes[i-1]),
               abs(lows[i]  - closes[i-1]))
           for i in range(1, len(highs))]
    return sum(trs[-n:]) / n


# ── 1. Trend Following ────────────────────────────────────────────────────────

class TrendFollowingStrategy:
    """
    EMA crossover + RSI momentum confirmation + macro trend direction filter.
    LONG  when fast EMA crosses above slow, price > EMA(trend), RSI in bullish zone.
    SHORT when fast EMA crosses below slow, price < EMA(trend), RSI in bearish zone.
    The EMA(trend) filter prevents counter-trend entries — the #1 source of losses.
    SL/TP set via ATR multiplier.
    """
    ID = "TF_EMA_RSI_v1"

    # RSI zones: only enter when momentum supports the direction
    RSI_LONG_MIN  = 40   # widened from 45 — allows more long signals
    RSI_SHORT_MAX = 60   # widened from 55 — allows more short signals

    def __init__(self, dna: dict = None):
        d = dna or {}
        self.ema_fast   = int(d.get("ema_fast",   cfg.EMA_FAST))
        self.ema_slow   = int(d.get("ema_slow",   cfg.EMA_SLOW))
        self.ema_trend  = int(d.get("ema_trend",  cfg.EMA_TREND))   # macro filter
        self.rsi_period = int(d.get("rsi_period", cfg.RSI_PERIOD))
        self.rsi_ob     = float(d.get("rsi_ob",   cfg.RSI_OVERBOUGHT))
        self.rsi_os     = float(d.get("rsi_os",   cfg.RSI_OVERSOLD))
        self.atr_period = int(d.get("atr_period", cfg.ATR_PERIOD))
        self.atr_sl     = float(d.get("atr_sl",   cfg.ATR_MULT_SL))
        self.atr_tp     = float(d.get("atr_tp",   cfg.ATR_MULT_TP))

    def generate_signal(
        self, symbol: str, closes: List[float],
        highs: List[float], lows: List[float],
    ) -> Optional[TradeSignal]:
        min_len = max(self.ema_trend + 2, self.ema_slow + 2,
                      self.rsi_period + 2, self.atr_period + 2)
        if len(closes) < min_len:
            return None

        fast_now   = _ema(closes, self.ema_fast)
        fast_prev  = _ema(closes[:-1], self.ema_fast)
        slow_now   = _ema(closes, self.ema_slow)
        slow_prev  = _ema(closes[:-1], self.ema_slow)
        trend_ema  = _ema(closes, self.ema_trend)   # macro trend anchor
        rsi        = _rsi(closes, self.rsi_period)
        rsi_prev   = _rsi(closes[:-1], self.rsi_period)   # RSI one candle ago
        atr        = _atr(highs, lows, closes, self.atr_period)
        price      = closes[-1]

        # ── Data quality guards ────────────────────────────────────────────
        atr_pct = (atr / price * 100) if price else 0
        if atr_pct < MIN_ATR_PCT:
            return None   # stablecoin / too low volatility

        if rsi == 50.0:
            return None   # RSI sentinel = insufficient candle data (<14 candles)

        # EMA crossover detection
        bullish_cross = fast_prev < slow_prev and fast_now > slow_now
        bearish_cross = fast_prev > slow_prev and fast_now < slow_now

        # LONG: crossover upward AND in macro uptrend AND RSI building momentum
        # RSI direction filter: RSI must be rising (momentum still building).
        # Root cause of actual_rr=0.43: crossover fires AFTER momentum peaked;
        # price reverses immediately. Requiring rsi > rsi_prev ensures we enter
        # while momentum is still expanding, not already dying.
        if (bullish_cross
                and price > trend_ema                      # macro uptrend filter
                and self.RSI_LONG_MIN <= rsi <= self.rsi_ob   # momentum zone
                and rsi > rsi_prev):                       # RSI still rising — not peaked
            return TradeSignal(
                symbol=symbol, signal=Signal.LONG, entry_price=price,
                stop_loss=price - atr * self.atr_sl,
                take_profit=price + atr * self.atr_tp,
                confidence=min(0.9, rsi / 100 + 0.3),
                strategy_id=self.ID,
                reason=f"EMA cross UP | trend↑ | RSI={rsi:.1f}↑ | ATR={atr:.4f}",
            )

        # SHORT: crossover downward AND in macro downtrend AND RSI fading
        # RSI direction filter: RSI must be falling (momentum still expanding short).
        if (bearish_cross
                and price < trend_ema                       # macro downtrend filter
                and self.rsi_os <= rsi <= self.RSI_SHORT_MAX   # fading zone
                and rsi < rsi_prev):                        # RSI still falling — not bottomed
            return TradeSignal(
                symbol=symbol, signal=Signal.SHORT, entry_price=price,
                stop_loss=price + atr * self.atr_sl,
                take_profit=price - atr * self.atr_tp,
                confidence=min(0.9, (100 - rsi) / 100 + 0.3),
                strategy_id=self.ID,
                reason=f"EMA cross DOWN | trend↓ | RSI={rsi:.1f}↓ | ATR={atr:.4f}",
            )
        return None

    def to_dna(self) -> dict:
        return {
            "strategy": self.ID,
            "ema_fast": self.ema_fast, "ema_slow": self.ema_slow,
            "ema_trend": self.ema_trend,
            "rsi_period": self.rsi_period, "rsi_ob": self.rsi_ob,
            "rsi_os": self.rsi_os, "atr_period": self.atr_period,
            "atr_sl": self.atr_sl, "atr_tp": self.atr_tp,
        }


# ── 2. Mean Reversion ─────────────────────────────────────────────────────────

class MeanReversionStrategy:
    """
    Bollinger Band + RSI extremes.
    LONG when price touches lower BB and RSI < oversold threshold.
    SHORT when price touches upper BB and RSI > overbought threshold.
    """
    ID = "MR_BB_RSI_v1"

    def __init__(self, dna: dict = None):
        d = dna or {}
        self.bb_period  = int(d.get("bb_period",  cfg.BB_PERIOD))
        self.bb_std     = float(d.get("bb_std",   cfg.BB_STD))
        self.rsi_period = int(d.get("rsi_period", cfg.RSI_PERIOD))
        self.rsi_ob     = float(d.get("rsi_ob",   cfg.RSI_OVERBOUGHT))
        self.rsi_os     = float(d.get("rsi_os",   cfg.RSI_OVERSOLD))
        self.atr_period = int(d.get("atr_period", cfg.ATR_PERIOD))
        self.atr_sl     = float(d.get("atr_sl",   cfg.ATR_MULT_SL))
        self.atr_tp     = float(d.get("atr_tp",   cfg.ATR_MULT_TP * 0.7))  # tighter TP

    def generate_signal(
        self, symbol: str, closes: List[float],
        highs: List[float], lows: List[float],
    ) -> Optional[TradeSignal]:
        if len(closes) < max(self.bb_period, self.rsi_period) + 2:
            return None

        window  = closes[-self.bb_period:]
        mean    = sum(window) / self.bb_period
        std     = math.sqrt(sum((x - mean) ** 2 for x in window) / self.bb_period)
        upper   = mean + self.bb_std * std
        lower   = mean - self.bb_std * std
        price   = closes[-1]
        rsi     = _rsi(closes, self.rsi_period)
        atr     = _atr(highs, lows, closes, self.atr_period)

        # Volatility guard
        atr_pct = (atr / price * 100) if price else 0
        if atr_pct < MIN_ATR_PCT:
            return None

        if price <= lower and rsi < self.rsi_os:
            # TP = BB mean, but at least atr_tp×ATR away to guarantee positive RR.
            # When BB is tight the mean can be less than 1×ATR, killing the RR ratio.
            tp = max(mean, price + atr * self.atr_tp)
            sl = price - atr * self.atr_sl
            if (tp - price) / price < 0.001:   # sanity: skip if still < 0.1% gross
                return None
            return TradeSignal(
                symbol=symbol, signal=Signal.LONG, entry_price=price,
                stop_loss=sl,
                take_profit=tp,
                confidence=min(0.85, (self.rsi_os - rsi) / self.rsi_os + 0.4),
                strategy_id=self.ID,
                reason=f"BB lower touch | RSI={rsi:.1f} | Mean={mean:.4f} | TP={tp:.4f}",
            )
        if price >= upper and rsi > self.rsi_ob:
            # TP = BB mean, but at least atr_tp×ATR away to guarantee positive RR.
            tp = min(mean, price - atr * self.atr_tp)
            sl = price + atr * self.atr_sl
            if (price - tp) / price < 0.001:
                return None
            return TradeSignal(
                symbol=symbol, signal=Signal.SHORT, entry_price=price,
                stop_loss=sl,
                take_profit=tp,
                confidence=min(0.85, (rsi - self.rsi_ob) / (100 - self.rsi_ob) + 0.4),
                strategy_id=self.ID,
                reason=f"BB upper touch | RSI={rsi:.1f} | Mean={mean:.4f} | TP={tp:.4f}",
            )
        return None

    def to_dna(self) -> dict:
        return {
            "strategy": self.ID,
            "bb_period": self.bb_period, "bb_std": self.bb_std,
            "rsi_period": self.rsi_period, "rsi_ob": self.rsi_ob,
            "rsi_os": self.rsi_os, "atr_period": self.atr_period,
            "atr_sl": self.atr_sl, "atr_tp": self.atr_tp,
        }


# ── 3. Volatility Expansion ───────────────────────────────────────────────────

class VolatilityExpansionStrategy:
    """
    Breakout strategy activated during high-volatility regimes.
    LONG on breakout above N-period high with ATR confirmation.
    SHORT on breakdown below N-period low.
    Wider SL/TP to accommodate volatility.
    """
    ID = "VE_BREAKOUT_ATR_v1"

    def __init__(self, dna: dict = None):
        d = dna or {}
        self.lookback   = int(d.get("lookback",   20))
        self.atr_period = int(d.get("atr_period", cfg.ATR_PERIOD))
        self.atr_sl     = float(d.get("atr_sl",   cfg.ATR_MULT_SL * 1.5))  # wider
        self.atr_tp     = float(d.get("atr_tp",   cfg.ATR_MULT_TP * 1.5))
        self.vol_filter = float(d.get("vol_filter", 1.2))  # ATR must be > avg * this

    def generate_signal(
        self, symbol: str, closes: List[float],
        highs: List[float], lows: List[float],
    ) -> Optional[TradeSignal]:
        # Forensics 2026-05-03: 2 trades, 0% WR, avg loss $4.86/trade.
        # Breakout entries trigger at price extremes which are already exhausted.
        # Disabled until a confirmed-breakout + retrace entry is designed.
        return None
        atr            = _atr(highs, lows, closes, self.atr_period)

        # Volatility guard — VE strategy needs even more movement
        atr_pct = (atr / price * 100) if price else 0
        if atr_pct < MIN_ATR_PCT * 2:   # stricter: 0.20% minimum for breakouts
            return None

        # ATR average over lookback
        avg_atr        = sum(
            _atr(highs[i:i+self.atr_period+1], lows[i:i+self.atr_period+1],
                 closes[i:i+self.atr_period+1], self.atr_period)
            for i in range(max(0, len(closes) - self.lookback), len(closes) - self.atr_period)
        ) / max(1, self.lookback - self.atr_period)

        # Volume/volatility filter
        if atr < avg_atr * self.vol_filter:
            return None   # not enough volatility for breakout trade

        if price > period_high:
            return TradeSignal(
                symbol=symbol, signal=Signal.LONG, entry_price=price,
                stop_loss=price - atr * self.atr_sl,
                take_profit=price + atr * self.atr_tp,
                confidence=min(0.8, (price - period_high) / atr + 0.4),
                strategy_id=self.ID,
                reason=f"Breakout HIGH={period_high:.4f} | ATR={atr:.4f}",
            )
        if price < period_low:
            return TradeSignal(
                symbol=symbol, signal=Signal.SHORT, entry_price=price,
                stop_loss=price + atr * self.atr_sl,
                take_profit=price - atr * self.atr_tp,
                confidence=min(0.8, (period_low - price) / atr + 0.4),
                strategy_id=self.ID,
                reason=f"Breakdown LOW={period_low:.4f} | ATR={atr:.4f}",
            )
        return None

    def to_dna(self) -> dict:
        return {
            "strategy": self.ID,
            "lookback": self.lookback, "atr_period": self.atr_period,
            "atr_sl": self.atr_sl, "atr_tp": self.atr_tp,
            "vol_filter": self.vol_filter,
        }


# ── Strategy Router ───────────────────────────────────────────────────────────

def get_strategy(regime: str, dna: dict = None):
    """Return the appropriate strategy instance for the given regime."""
    from core.regime_detector import Regime
    mapping = {
        Regime.TRENDING:             TrendFollowingStrategy,
        Regime.MEAN_REVERTING:       MeanReversionStrategy,
        Regime.VOLATILITY_EXPANSION: VolatilityExpansionStrategy,
        Regime.UNKNOWN:              TrendFollowingStrategy,   # safe default
    }
    cls = mapping.get(regime, TrendFollowingStrategy)
    return cls(dna)

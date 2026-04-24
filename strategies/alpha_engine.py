"""
EOW Quant Engine — Phase 4: Alpha Entry Engine (Core Edge Layer)
Replaces weak entry logic with three high-probability signal types.

Every signal is internally gated by RR_ENGINE and TRADE_SCORER before
being returned — only genuinely high-quality setups reach execution.

Strategy types:
  A. TrendContinuationBreakout — ADX > 25, price breaks recent high/low, volume spike
  B. PullbackEntryInTrend      — trend confirmed, price retraces to EMA zone, RSI resets
  C. VolatilitySqueezeEntry    — Bollinger Band squeeze followed by expansion breakout

Integration: call alpha_engine.generate() after existing strategy signal fails,
or as a parallel signal source that provides the strongest available setup.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger

from config import cfg
from strategies.strategy_modules import Signal, TradeSignal, _ema, _rsi, _atr
from core.rr_engine import rr_engine
from core.trade_scorer import trade_scorer


@dataclass
class AlphaSignal:
    trade_signal: TradeSignal
    score:        float
    rr:           float
    score_detail: dict
    alpha_type:   str


# ── A. Trend Continuation Breakout ───────────────────────────────────────────

class TrendContinuationBreakout:
    """
    Fires when a strong trend (ADX > threshold) breaks to a new high/low
    with above-average volume confirming institutional participation.
    Highest-confidence setup — only in confirmed directional markets.
    """
    ID = "ALPHA_TCB_v1"

    def __init__(self, dna: dict = None):
        d = dna or {}
        self.adx_min    = float(d.get("adx_min",    25.0))
        self.lookback   = int(d.get("lookback",     20))
        self.vol_spike  = float(d.get("vol_spike",  1.2))  # 1-min candles: 1.5 was too rare; 1.2 still confirms participation
        self.atr_period = int(d.get("atr_period",   cfg.ATR_PERIOD))
        self.atr_sl     = float(d.get("atr_sl",     cfg.ATR_MULT_SL))
        self.atr_tp     = float(d.get("atr_tp",     cfg.ATR_MULT_TP))

    def generate(
        self,
        symbol:      str,
        closes:      List[float],
        highs:       List[float],
        lows:        List[float],
        volumes:     List[float],
        adx:         float,
        atr_pct:     float,
        avg_atr_pct: float,
        regime:      str,
    ) -> Optional[AlphaSignal]:
        if len(closes) < self.lookback + self.atr_period + 2:
            return None
        if adx < self.adx_min:
            return None

        price = closes[-1]
        atr   = _atr(highs, lows, closes, self.atr_period)
        if atr <= 0 or price <= 0:
            return None

        recent_high = max(highs[-self.lookback - 1:-1])
        recent_low  = min(lows[-self.lookback - 1:-1])

        # Volume spike confirmation
        vol_window = volumes[-self.lookback:] if len(volumes) >= self.lookback else volumes
        avg_vol  = sum(vol_window) / len(vol_window) if vol_window else 0.0
        cur_vol  = volumes[-1] if volumes else 0.0
        vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1.0
        if vol_ratio < self.vol_spike:
            return None

        rsi      = _rsi(closes, cfg.RSI_PERIOD)
        rsi_prev = _rsi(closes[:-1], cfg.RSI_PERIOD) if len(closes) > cfg.RSI_PERIOD + 1 else rsi

        if price > recent_high:
            side = "LONG"
            sl   = price - atr * self.atr_sl
            tp   = price + atr * self.atr_tp
        elif price < recent_low:
            side = "SHORT"
            sl   = price + atr * self.atr_sl
            tp   = price - atr * self.atr_tp
        else:
            return None

        rr_res = rr_engine.evaluate(side, price, sl, tp, atr, atr_pct)
        if not rr_res.ok:
            return None

        tp_dist = abs(rr_res.adjusted_tp - price)
        cost_frac = (cfg.TAKER_FEE * 2 * price) / tp_dist if tp_dist > 0 else 1.0
        score_res = trade_scorer.score(
            regime=regime, adx=adx, rsi=rsi, rsi_prev=rsi_prev,
            atr_pct=atr_pct, avg_atr_pct=avg_atr_pct,
            vol_ratio=vol_ratio, cost_fraction=cost_frac, signal_side=side,
        )
        if not score_res.ok:
            return None

        return AlphaSignal(
            trade_signal=TradeSignal(
                symbol=symbol, signal=Signal(side), entry_price=price,
                stop_loss=rr_res.adjusted_sl, take_profit=rr_res.adjusted_tp,
                confidence=min(0.95, score_res.score),
                strategy_id=self.ID,
                reason=(f"TCB: ADX={adx:.1f} VOL={vol_ratio:.1f}x "
                        f"RR={rr_res.rr:.2f} SCORE={score_res.score:.3f}"),
            ),
            score=score_res.score, rr=rr_res.rr,
            score_detail=score_res.breakdown, alpha_type="TrendBreakout",
        )


# ── B. Pullback Entry in Trend ────────────────────────────────────────────────

class PullbackEntryInTrend:
    """
    Enters during a retracement within a confirmed trend.
    Better fill price than breakout entries; RSI reset confirms exhaustion
    of the counter-trend move before resumption.
    """
    ID = "ALPHA_PBE_v1"

    def __init__(self, dna: dict = None):
        d = dna or {}
        self.ema_period      = int(d.get("ema_period",      21))
        self.ema_trend       = int(d.get("ema_trend",       cfg.EMA_TREND))
        self.rsi_period      = int(d.get("rsi_period",      cfg.RSI_PERIOD))
        self.rsi_reset_long  = float(d.get("rsi_reset_long",  45.0))  # RSI must be below here for LONG reset
        self.rsi_reset_short = float(d.get("rsi_reset_short", 55.0))  # RSI must be above here for SHORT reset
        self.ema_zone_pct    = float(d.get("ema_zone_pct",    1.0))   # price within 1.0% of EMA (was 0.5% — too tight for 1-min candles)
        self.atr_period      = int(d.get("atr_period",      cfg.ATR_PERIOD))
        self.atr_sl          = float(d.get("atr_sl",         cfg.ATR_MULT_SL))
        self.atr_tp          = float(d.get("atr_tp",         cfg.ATR_MULT_TP))

    def generate(
        self,
        symbol:      str,
        closes:      List[float],
        highs:       List[float],
        lows:        List[float],
        volumes:     List[float],
        adx:         float,
        atr_pct:     float,
        avg_atr_pct: float,
        regime:      str,
    ) -> Optional[AlphaSignal]:
        min_len = max(self.ema_trend + 2, self.rsi_period + 2, self.atr_period + 2)
        if len(closes) < min_len:
            return None

        price      = closes[-1]
        ema_fast   = _ema(closes, self.ema_period)
        ema_trend  = _ema(closes, self.ema_trend)
        rsi        = _rsi(closes, self.rsi_period)
        rsi_prev   = _rsi(closes[:-1], self.rsi_period) if len(closes) > self.rsi_period + 1 else rsi
        atr        = _atr(highs, lows, closes, self.atr_period)
        if atr <= 0 or ema_fast <= 0 or price <= 0:
            return None

        ema_dist_pct = abs(price - ema_fast) / ema_fast * 100

        vol_window = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_vol   = sum(vol_window) / len(vol_window) if vol_window else 0.0
        cur_vol   = volumes[-1] if volumes else 0.0
        vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1.0

        side = None
        if (price > ema_trend
                and ema_dist_pct <= self.ema_zone_pct
                and 30 < rsi < self.rsi_reset_long):
            side = "LONG"
        elif (price < ema_trend
                and ema_dist_pct <= self.ema_zone_pct
                and self.rsi_reset_short < rsi < 70):
            side = "SHORT"

        if side is None:
            return None

        sl = price - atr * self.atr_sl if side == "LONG" else price + atr * self.atr_sl
        tp = price + atr * self.atr_tp if side == "LONG" else price - atr * self.atr_tp

        rr_res = rr_engine.evaluate(side, price, sl, tp, atr, atr_pct)
        if not rr_res.ok:
            return None

        tp_dist   = abs(rr_res.adjusted_tp - price)
        cost_frac = (cfg.TAKER_FEE * 2 * price) / tp_dist if tp_dist > 0 else 1.0
        score_res = trade_scorer.score(
            regime=regime, adx=adx, rsi=rsi, rsi_prev=rsi_prev,
            atr_pct=atr_pct, avg_atr_pct=avg_atr_pct,
            vol_ratio=vol_ratio, cost_fraction=cost_frac, signal_side=side,
        )
        if not score_res.ok:
            return None

        return AlphaSignal(
            trade_signal=TradeSignal(
                symbol=symbol, signal=Signal(side), entry_price=price,
                stop_loss=rr_res.adjusted_sl, take_profit=rr_res.adjusted_tp,
                confidence=min(0.90, score_res.score),
                strategy_id=self.ID,
                reason=(f"PBE: EMA_DIST={ema_dist_pct:.2f}% RSI={rsi:.1f} "
                        f"RR={rr_res.rr:.2f} SCORE={score_res.score:.3f}"),
            ),
            score=score_res.score, rr=rr_res.rr,
            score_detail=score_res.breakdown, alpha_type="PullbackEntry",
        )


# ── C. Volatility Squeeze Entry ───────────────────────────────────────────────

class VolatilitySqueezeEntry:
    """
    Bollinger Band squeeze → expansion breakout.
    Identifies periods of low volatility (compression) followed by an
    expansion impulse — historically one of the strongest momentum setups.
    """
    ID = "ALPHA_VSE_v1"

    def __init__(self, dna: dict = None):
        d = dna or {}
        self.bb_period   = int(d.get("bb_period",    cfg.BB_PERIOD))
        self.bb_std      = float(d.get("bb_std",     cfg.BB_STD))
        self.squeeze_pct = float(d.get("squeeze_pct", 0.5))  # BB width < 0.5% = squeeze
        self.expand_mult = float(d.get("expand_mult", 1.2))   # width must grow 20%
        self.atr_period  = int(d.get("atr_period",  cfg.ATR_PERIOD))
        self.atr_sl      = float(d.get("atr_sl",    cfg.ATR_MULT_SL))
        self.atr_tp      = float(d.get("atr_tp",    cfg.ATR_MULT_TP * 1.2))  # wider for volatility moves

    def generate(
        self,
        symbol:      str,
        closes:      List[float],
        highs:       List[float],
        lows:        List[float],
        volumes:     List[float],
        adx:         float,
        atr_pct:     float,
        avg_atr_pct: float,
        regime:      str,
    ) -> Optional[AlphaSignal]:
        lookback_needed = self.bb_period * 2 + 20 + self.atr_period + 2
        if len(closes) < lookback_needed:
            return None

        price = closes[-1]
        atr   = _atr(highs, lows, closes, self.atr_period)
        if atr <= 0 or price <= 0:
            return None

        def _bb_width(price_slice: List[float]) -> float:
            if len(price_slice) < self.bb_period:
                return 99.0
            w = price_slice[-self.bb_period:]
            m = sum(w) / self.bb_period
            s = math.sqrt(sum((x - m) ** 2 for x in w) / self.bb_period)
            return (2 * self.bb_std * s) / m * 100 if m > 0 else 99.0

        def _bb_bands(price_slice: List[float]):
            w = price_slice[-self.bb_period:]
            m = sum(w) / self.bb_period
            s = math.sqrt(sum((x - m) ** 2 for x in w) / self.bb_period)
            return m + self.bb_std * s, m - self.bb_std * s

        cur_width  = _bb_width(closes)
        prior_width = _bb_width(closes[:-20])
        upper, lower = _bb_bands(closes)

        was_squeezed = prior_width < self.squeeze_pct
        is_expanding = cur_width > prior_width * self.expand_mult

        if not (was_squeezed and is_expanding):
            return None

        rsi      = _rsi(closes, cfg.RSI_PERIOD)
        rsi_prev = _rsi(closes[:-1], cfg.RSI_PERIOD) if len(closes) > cfg.RSI_PERIOD + 1 else rsi

        vol_window = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_vol   = sum(vol_window) / len(vol_window) if vol_window else 0.0
        cur_vol   = volumes[-1] if volumes else 0.0
        vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1.0

        if price > upper:
            side = "LONG"
        elif price < lower:
            side = "SHORT"
        else:
            return None

        sl = price - atr * self.atr_sl if side == "LONG" else price + atr * self.atr_sl
        tp = price + atr * self.atr_tp if side == "LONG" else price - atr * self.atr_tp

        rr_res = rr_engine.evaluate(side, price, sl, tp, atr, atr_pct)
        if not rr_res.ok:
            return None

        tp_dist   = abs(rr_res.adjusted_tp - price)
        cost_frac = (cfg.TAKER_FEE * 2 * price) / tp_dist if tp_dist > 0 else 1.0
        score_res = trade_scorer.score(
            regime=regime, adx=adx, rsi=rsi, rsi_prev=rsi_prev,
            atr_pct=atr_pct, avg_atr_pct=avg_atr_pct,
            vol_ratio=vol_ratio, cost_fraction=cost_frac, signal_side=side,
        )
        if not score_res.ok:
            return None

        return AlphaSignal(
            trade_signal=TradeSignal(
                symbol=symbol, signal=Signal(side), entry_price=price,
                stop_loss=rr_res.adjusted_sl, take_profit=rr_res.adjusted_tp,
                confidence=min(0.92, score_res.score),
                strategy_id=self.ID,
                reason=(f"VSE: BB_WIDTH={cur_width:.2f}% SQUEEZE→EXPAND "
                        f"RR={rr_res.rr:.2f} SCORE={score_res.score:.3f}"),
            ),
            score=score_res.score, rr=rr_res.rr,
            score_detail=score_res.breakdown, alpha_type="VolatilitySqueeze",
        )


# ── Alpha Entry Engine — orchestrator ────────────────────────────────────────

class AlphaEntryEngine:
    """
    Runs all three alpha strategies and returns the highest-scoring
    valid signal. Each strategy already enforces RR + Trade Scorer.
    Returns None if no strategy qualifies.
    """

    def __init__(self):
        self._breakout = TrendContinuationBreakout()
        self._pullback = PullbackEntryInTrend()
        self._squeeze  = VolatilitySqueezeEntry()
        logger.info("[ALPHA-ENGINE] Phase 4 Alpha Entry Engine activated | strategies=3")

    def generate(
        self,
        symbol:      str,
        closes:      List[float],
        highs:       List[float],
        lows:        List[float],
        volumes:     List[float],
        adx:         float,
        atr_pct:     float,
        avg_atr_pct: float,
        regime:      str,
    ) -> Optional[AlphaSignal]:
        """Returns the highest-scoring alpha signal across all three strategies."""
        candidates: List[AlphaSignal] = []
        for strat in (self._breakout, self._pullback, self._squeeze):
            try:
                result = strat.generate(
                    symbol=symbol, closes=closes, highs=highs, lows=lows,
                    volumes=volumes, adx=adx, atr_pct=atr_pct,
                    avg_atr_pct=avg_atr_pct, regime=regime,
                )
                if result is not None:
                    candidates.append(result)
            except Exception as exc:
                logger.debug(f"[ALPHA-ENGINE] {type(strat).__name__} error for {symbol}: {exc}")

        if not candidates:
            return None

        best = max(candidates, key=lambda c: c.score)
        logger.debug(
            f"[ALPHA-ENGINE] {symbol} best={best.alpha_type} "
            f"score={best.score:.3f} rr={best.rr:.2f}"
        )
        return best

    def summary(self) -> dict:
        return {
            "strategies": ["TrendBreakout", "PullbackEntry", "VolatilitySqueeze"],
            "module":     "ALPHA_ENGINE",
            "phase":      4,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
alpha_engine = AlphaEntryEngine()

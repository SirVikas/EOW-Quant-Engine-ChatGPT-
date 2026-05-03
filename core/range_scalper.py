"""
EOW Quant Engine — Range Scalper  (Adaptive Mode 2: RANGE_SCALP)
Generates signals in MEAN_REVERTING regimes — eliminates NO_TRADE_SESSION.

Why this exists:
  The existing MeanReversionStrategy fires only on BB extreme + RSI extreme,
  which in shallow ranges almost never coincides.  This module adds a CVD
  imbalance gate so entries are confirmed by actual order-flow, not just
  indicator geometry.

Signal logic:
  1. BB identifies range boundaries (upper/lower band touch)
  2. CVD imbalance confirms institutional direction (≥60% buy for LONG,
     ≥60% sell for SHORT)
  3. RSI extreme confirms exhaustion AND RSI must be turning (momentum flip)
  4. Tight SL (ATR_MULT_SL × 0.8) and TP at BB midpoint for fast exits
  5. Full RR + Trade Scorer quality gate — same as alpha_engine signals

Integration: called by adaptive_mode_engine when mode == RANGE_SCALP.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger

from config import cfg
from strategies.strategy_modules import Signal, TradeSignal, _rsi, _atr, MIN_ATR_PCT
from core.rr_engine import rr_engine
from core.trade_scorer import trade_scorer
from core.cvd_tracker import CVDState


RANGE_SCALP_ID = "RS_CVD_BB_v1"


@dataclass
class RangeSignal:
    trade_signal:  TradeSignal
    score:         float
    rr:            float
    cvd_imbalance: float
    alpha_type:    str = "RangeScalp"


class RangeScalper:
    """
    BB + CVD range-bound scalping strategy.
    Lower RR target than trend strategies but fires in any non-trending market.
    """
    ID = RANGE_SCALP_ID

    def __init__(self):
        self.bb_period         = cfg.BB_PERIOD         # 20
        self.bb_std            = cfg.BB_STD             # 2.0
        self.rsi_period        = cfg.RSI_PERIOD         # 14
        self.rsi_os            = cfg.RSI_OVERSOLD       # 35
        self.rsi_ob            = cfg.RSI_OVERBOUGHT     # 65
        self.atr_period        = cfg.ATR_PERIOD         # 14
        self.atr_sl            = cfg.ATR_MULT_SL * 0.8  # tighter SL in range context
        self.cvd_imbal_min     = cfg.RS_CVD_IMBAL_MIN   # 0.60 — 60% buy/sell concentration
        self.min_bb_width_pct  = cfg.RS_MIN_BB_WIDTH    # 0.10 — skip near-flat markets
        self.tp_atr_mult       = cfg.ATR_MULT_TP * 0.40 # range TP ≈ 40% of trend TP

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
        cvd_state:   Optional[CVDState] = None,
    ) -> Optional[RangeSignal]:
        min_len = max(self.bb_period, self.rsi_period, self.atr_period) + 2
        if len(closes) < min_len:
            return None

        price = closes[-1]
        atr   = _atr(highs, lows, closes, self.atr_period)
        if atr <= 0 or price <= 0 or atr / price * 100 < MIN_ATR_PCT:
            return None

        # Bollinger Bands
        window    = closes[-self.bb_period:]
        mean      = sum(window) / self.bb_period
        variance  = sum((x - mean) ** 2 for x in window) / self.bb_period
        std       = math.sqrt(variance)
        upper     = mean + self.bb_std * std
        lower     = mean - self.bb_std * std
        bb_w_pct  = ((upper - lower) / mean * 100) if mean > 0 else 0.0

        if bb_w_pct < self.min_bb_width_pct:
            return None  # market too flat — no exploitable range

        rsi      = _rsi(closes, self.rsi_period)
        rsi_prev = _rsi(closes[:-1], self.rsi_period) if len(closes) > self.rsi_period + 1 else rsi

        # CVD imbalance gate
        imbalance   = cvd_state.imbalance  if cvd_state else 0.5
        buy_dominant  = imbalance >= self.cvd_imbal_min
        sell_dominant = imbalance <= (1.0 - self.cvd_imbal_min)

        vol_window = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_vol    = sum(vol_window) / len(vol_window) if vol_window else 0.0
        cur_vol    = volumes[-1] if volumes else 0.0
        vol_ratio  = cur_vol / avg_vol if avg_vol > 0 else 1.0

        # Entry conditions: BB touch + RSI extreme + RSI turning + CVD confirms
        side = None
        if price <= lower and rsi < self.rsi_os and rsi > rsi_prev and buy_dominant:
            side = "LONG"
        elif price >= upper and rsi > self.rsi_ob and rsi < rsi_prev and sell_dominant:
            side = "SHORT"

        if side is None:
            return None

        if side == "LONG":
            sl = price - atr * self.atr_sl
            # TP at BB midpoint or ATR-based floor, whichever is further
            tp = max(mean, price + atr * self.tp_atr_mult)
        else:
            sl = price + atr * self.atr_sl
            tp = min(mean, price - atr * self.tp_atr_mult)

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

        logger.debug(
            f"[RANGE-SCALPER] {symbol} {side} "
            f"BB_w={bb_w_pct:.2f}% CVD_imbal={imbalance:.2f} "
            f"RSI={rsi:.1f} RR={rr_res.rr:.2f} SCORE={score_res.score:.3f}"
        )
        return RangeSignal(
            trade_signal=TradeSignal(
                symbol=symbol, signal=Signal(side), entry_price=price,
                stop_loss=rr_res.adjusted_sl, take_profit=rr_res.adjusted_tp,
                confidence=min(0.78, score_res.score),
                strategy_id=self.ID,
                reason=(
                    f"RS_CVD: BB={'lower' if side == 'LONG' else 'upper'} "
                    f"CVD={imbalance:.2f} RSI={rsi:.1f} "
                    f"RR={rr_res.rr:.2f} SCORE={score_res.score:.3f}"
                ),
            ),
            score=score_res.score,
            rr=rr_res.rr,
            cvd_imbalance=imbalance,
        )

    def summary(self) -> dict:
        return {
            "module":        "RANGE_SCALPER",
            "strategy_id":   self.ID,
            "cvd_imbal_min": self.cvd_imbal_min,
            "bb_period":     self.bb_period,
            "atr_sl_mult":   self.atr_sl,
        }


# ── Module-level singleton ─────────────────────────────────────────────────────
range_scalper = RangeScalper()

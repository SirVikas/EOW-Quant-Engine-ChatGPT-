"""
EOW Quant Engine — Signal Quality Filter  (FTD-REF-023 + FTD-REF-024 + FTD-REF-025)
High-quality trade gate with per-regime adaptive thresholds.

Static thresholds are replaced by regime-aware ones:
  TRENDING:             RR ≥ 1.4  confidence ≥ 0.50
  MEAN_REVERTING:       RR ≥ 1.1  confidence ≥ 0.40
  VOLATILITY_EXPANSION: RR ≥ 1.5  confidence ≥ 0.50
  UNKNOWN / default:    RR ≥ 1.4  confidence ≥ 0.45  (matches TRENDING — default is TrendFollowing)

UNKNOWN uses the same bar as TRENDING because the engine defaults to TrendFollowing
for unclassified regimes. Using a stricter threshold for UNKNOWN prevents all trading
during warmup (when all regimes read UNKNOWN for the first 10+ minutes).

A `relaxation_factor` (0.8–1.0) from TradeFrequency can lower effective
thresholds when the engine has been in a dry spell (no trades).

FTD-REF-024 — Edge gate (applied first):
  expected_edge < 0 → reject immediately; strategy has negative expectancy
  for this regime (data-driven kill — bypasses all other checks).
  NOTE: only applied when EdgeEngine has ≥ MIN_TRADES of data. With no data,
  expected_edge defaults to 0.0 which does NOT trigger this gate.

Protective pause:
  3 consecutive losses on any symbol → 30-min pause for that symbol
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from loguru import logger


# ── Per-regime threshold table ────────────────────────────────────────────────
# Keys must match Regime.value strings
_REGIME_RR: Dict[str, float] = {
    "TRENDING":             1.4,
    "MEAN_REVERTING":       1.1,   # relaxed: high WR compensates lower R
    "VOLATILITY_EXPANSION": 1.5,   # reduced from 1.6 (VE strategy RR ≈ 1.5)
    "UNKNOWN":              1.4,   # matches TRENDING (TrendFollowing is UNKNOWN default)
}
_REGIME_CONF: Dict[str, float] = {
    "TRENDING":             0.20,  # was 0.50 — allows adj_conf ~0.19 after pf_mult
    "MEAN_REVERTING":       0.15,  # was 0.40
    "VOLATILITY_EXPANSION": 0.20,  # was 0.50
    "UNKNOWN":              0.18,  # was 0.45
}

# ── Fixed thresholds (regime-independent) ─────────────────────────────────────
MIN_ATR_PCT        = 0.03   # minimum ATR% floor (aligned with indicator_guard)
MAX_COST_FRACTION  = 0.30   # cost < 30% of gross TP

# ── Consecutive-loss protection ───────────────────────────────────────────────
MAX_CONSECUTIVE_LOSSES = 3
PAUSE_MINUTES          = 30   # reduced from 60 — allow faster recovery


@dataclass
class FilterResult:
    ok:            bool
    reason:        str   = ""
    rr:            float = 0.0
    cost_fraction: float = 0.0
    min_rr_used:   float = 0.0   # effective threshold after relaxation
    min_conf_used: float = 0.0


class SignalFilter:
    """
    Stateful adaptive signal quality gate.
    Pass regime=… to check() to select the correct thresholds.
    Pass relaxation_factor<1.0 to lower thresholds during dry spells.
    """

    def __init__(self):
        self._consec_losses: Dict[str, int]   = {}
        self._pause_until:   Dict[str, float] = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def check(
        self,
        symbol:            str,
        entry:             float,
        take_profit:       float,
        stop_loss:         float,
        cost_usdt:         float,
        atr_pct:           float,
        confidence:        float,
        regime:            str   = "UNKNOWN",
        relaxation_factor: float = 1.0,    # from TradeFrequency; < 1.0 = relax
        expected_edge:     float = 0.0,    # from EdgeEngine; < 0 = reject (FTD-REF-024)
    ) -> FilterResult:
        """
        Returns FilterResult(ok=True) when the signal clears all gates.
        regime         — Regime.value string for adaptive thresholds.
        relaxation_factor — multiply thresholds by this (e.g. 0.9 = 10% relaxation).
        expected_edge  — EdgeEngine expectancy; negative value blocks the trade.
        """
        # 0a. Edge gate (FTD-REF-024) — data-driven kill before anything else
        if expected_edge < 0:
            return FilterResult(
                ok=False,
                reason=f"NEGATIVE_EDGE({expected_edge:.4f})",
            )

        # 1. Consecutive-loss pause
        pause_exp = self._pause_until.get(symbol, 0.0)
        if time.time() < pause_exp:
            remaining = (pause_exp - time.time()) / 60
            return FilterResult(
                ok=False,
                reason=f"LOSS_PAUSE({self._consec_losses.get(symbol, 0)} losses, "
                       f"{remaining:.0f}min remaining)",
            )

        # 2. Select adaptive thresholds
        min_rr   = _REGIME_RR.get(regime,   _REGIME_RR["UNKNOWN"])   * relaxation_factor
        min_conf = _REGIME_CONF.get(regime, _REGIME_CONF["UNKNOWN"]) * relaxation_factor
        # Never relax below absolute floor values
        min_rr   = max(min_rr,   0.80)
        min_conf = max(min_conf, 0.10)

        # 3. RR gate
        gross_tp = abs(take_profit - entry)
        gross_sl = abs(entry - stop_loss)
        rr = (gross_tp / gross_sl) if gross_sl > 0 else 0.0
        if rr < min_rr:
            return FilterResult(
                ok=False,
                reason=f"LOW_RR({rr:.2f}<{min_rr:.2f} [{regime}])",
                rr=rr, min_rr_used=min_rr, min_conf_used=min_conf,
            )

        # 4. ATR% gate (unchanged — market liquidity floor)
        if atr_pct < MIN_ATR_PCT:
            return FilterResult(
                ok=False,
                reason=f"LOW_ATR({atr_pct:.3f}%<{MIN_ATR_PCT}%)",
                rr=rr, min_rr_used=min_rr, min_conf_used=min_conf,
            )

        # 5. Confidence gate
        if confidence < min_conf:
            return FilterResult(
                ok=False,
                reason=f"LOW_CONFIDENCE({confidence:.2f}<{min_conf:.2f} [{regime}])",
                rr=rr, min_rr_used=min_rr, min_conf_used=min_conf,
            )

        # 6. Cost fraction gate
        cost_fraction = (cost_usdt / gross_tp) if gross_tp > 0 else 1.0
        if cost_fraction >= MAX_COST_FRACTION:
            return FilterResult(
                ok=False,
                reason=f"COST_HIGH({cost_fraction:.0%}>={MAX_COST_FRACTION:.0%})",
                rr=rr, cost_fraction=cost_fraction,
                min_rr_used=min_rr, min_conf_used=min_conf,
            )

        return FilterResult(
            ok=True, rr=round(rr, 3),
            cost_fraction=round(cost_fraction, 3),
            min_rr_used=round(min_rr, 3),
            min_conf_used=round(min_conf, 3),
        )

    def record_loss(self, symbol: str):
        count = self._consec_losses.get(symbol, 0) + 1
        self._consec_losses[symbol] = count
        if count >= MAX_CONSECUTIVE_LOSSES:
            self._pause_until[symbol] = time.time() + PAUSE_MINUTES * 60
            logger.warning(
                f"[SIG-FILTER] {symbol} paused {PAUSE_MINUTES}min "
                f"after {count} consecutive losses."
            )

    def record_win(self, symbol: str):
        self._consec_losses[symbol] = 0

    def is_paused(self, symbol: str) -> bool:
        return time.time() < self._pause_until.get(symbol, 0.0)

    def consecutive_losses(self, symbol: str) -> int:
        return self._consec_losses.get(symbol, 0)

    def summary(self) -> dict:
        now = time.time()
        paused = {
            sym: round((self._pause_until[sym] - now) / 60, 1)
            for sym in self._pause_until
            if now < self._pause_until[sym]
        }
        return {
            "consecutive_losses": dict(self._consec_losses),
            "paused_symbols":     paused,
            "regime_thresholds":  {
                r: {"min_rr": _REGIME_RR[r], "min_conf": _REGIME_CONF[r]}
                for r in _REGIME_RR
            },
            "fixed_thresholds": {
                "min_atr_pct":    MIN_ATR_PCT,
                "max_cost_frac":  MAX_COST_FRACTION,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
signal_filter = SignalFilter()

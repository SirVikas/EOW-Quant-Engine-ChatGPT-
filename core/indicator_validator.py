"""
EOW Quant Engine — Phase 6.5: Indicator Validator (Pre-Boot Gate)
Ensures all technical indicators are properly initialized before any
trading decision is made. Acts as a hard gate at engine startup.

Checks:
  candle_count      ≥ IV_MIN_CANDLES (30)         — enough history
  rsi_candles       ≥ IV_RSI_MIN_CANDLES (15)      — RSI period warmup
  adx_candles       ≥ IV_ADX_MIN_CANDLES (28)      — ADX double-period warmup
  atr_candles       ≥ IV_ATR_MIN_CANDLES (15)      — ATR period warmup
  volume_candles    ≥ IV_VOLUME_MIN_CANDLES (20)   — volume average baseline
  no NaN values     in any indicator output

Rule:
  IF any check fails → ok=False, prevent_trade=True

The validator is stateless — it re-validates on every call so it
always reflects the current buffer state, not a cached snapshot.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from config import cfg


@dataclass
class IndicatorValidationResult:
    ok:              bool          # True → all indicators warm and valid
    prevent_trade:   bool          # True → engine must not place new trades
    passed:          List[str]     # checks that passed
    failed:          List[str]     # checks that failed
    score:           float         # fraction of checks passed (0–1), for deployability
    reason:          str = ""


class IndicatorValidator:
    """
    Per-symbol indicator readiness validator.

    Validates a set of candle counts and optional indicator float values
    (NaN check). Designed to be called at boot and on every signal cycle.

    Usage:
        result = indicator_validator.validate(
            candle_count=35,
            rsi_candles=35, adx_candles=30, atr_candles=35, volume_candles=30,
            indicator_values={"rsi": 52.3, "adx": 24.1, "atr": 0.0025},
        )
        if not result.ok:
            prevent_engine_start()
    """

    def __init__(self):
        self._last_result: Optional[IndicatorValidationResult] = None
        logger.info(
            f"[INDICATOR-VALIDATOR] Phase 6.5 activated | "
            f"min_candles={cfg.IV_MIN_CANDLES} "
            f"rsi≥{cfg.IV_RSI_MIN_CANDLES} adx≥{cfg.IV_ADX_MIN_CANDLES} "
            f"atr≥{cfg.IV_ATR_MIN_CANDLES} vol≥{cfg.IV_VOLUME_MIN_CANDLES}"
        )

    def validate(
        self,
        candle_count:    int,
        rsi_candles:     int,
        adx_candles:     int,
        atr_candles:     int,
        volume_candles:  int,
        indicator_values: Optional[Dict[str, float]] = None,
    ) -> IndicatorValidationResult:
        """
        Validate that all indicators have sufficient data and no NaN values.

        Args:
            candle_count:      total candles in the primary buffer
            rsi_candles:       candles available for RSI computation
            adx_candles:       candles available for ADX computation
            atr_candles:       candles available for ATR computation
            volume_candles:    candles available for volume average
            indicator_values:  optional {name: value} dict — any NaN → fail

        Returns IndicatorValidationResult; ok=False → block all new trades.
        """
        passed: List[str] = []
        failed: List[str] = []

        def _check(name: str, actual: int, required: int):
            if actual >= required:
                passed.append(f"{name}({actual}≥{required})")
            else:
                failed.append(f"{name}({actual}<{required})")

        _check("candle_count",   candle_count,   cfg.IV_MIN_CANDLES)
        _check("rsi_warmup",     rsi_candles,    cfg.IV_RSI_MIN_CANDLES)
        _check("adx_warmup",     adx_candles,    cfg.IV_ADX_MIN_CANDLES)
        _check("atr_warmup",     atr_candles,    cfg.IV_ATR_MIN_CANDLES)
        _check("volume_warmup",  volume_candles, cfg.IV_VOLUME_MIN_CANDLES)

        # NaN / invalid value check
        if indicator_values:
            for name, value in indicator_values.items():
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    failed.append(f"{name}=NaN")
                elif isinstance(value, float) and math.isinf(value):
                    failed.append(f"{name}=Inf")
                else:
                    passed.append(f"{name}=valid({value:.4g})")

        total = len(passed) + len(failed)
        score = round(len(passed) / total, 4) if total > 0 else 0.0
        ok = len(failed) == 0
        prevent_trade = not ok
        reason = "INDICATORS_READY" if ok else f"MISSING: {', '.join(failed)}"

        result = IndicatorValidationResult(
            ok=ok,
            prevent_trade=prevent_trade,
            passed=passed,
            failed=failed,
            score=score,
            reason=reason,
        )

        if ok:
            logger.debug(f"[INDICATOR-VALIDATOR] OK — {len(passed)} checks passed")
        else:
            logger.warning(
                f"[INDICATOR-VALIDATOR] BLOCK — failed: {failed} "
                f"({len(passed)}/{total} checks passed)"
            )

        self._last_result = result
        return result

    def validate_symbol_buffers(
        self,
        candle_close_buf: list,
        candle_volume_buf: list,
        indicator_values: Optional[Dict[str, float]] = None,
    ) -> IndicatorValidationResult:
        """
        Convenience wrapper: derive candle counts from raw buffer lengths.
        Use this when you have MarketData buffer references directly.
        """
        n = len(candle_close_buf)
        n_vol = len(candle_volume_buf)
        return self.validate(
            candle_count=n,
            rsi_candles=n,
            adx_candles=n,
            atr_candles=n,
            volume_candles=n_vol,
            indicator_values=indicator_values,
        )

    def last_result(self) -> Optional[IndicatorValidationResult]:
        return self._last_result

    def is_ready(self) -> bool:
        """Quick check: True if last validation passed."""
        return self._last_result.ok if self._last_result else False

    def summary(self) -> dict:
        r = self._last_result
        return {
            "last_ok":          r.ok if r else False,
            "last_score":       r.score if r else 0.0,
            "last_failed":      r.failed if r else [],
            "thresholds": {
                "min_candles":    cfg.IV_MIN_CANDLES,
                "rsi_min":        cfg.IV_RSI_MIN_CANDLES,
                "adx_min":        cfg.IV_ADX_MIN_CANDLES,
                "atr_min":        cfg.IV_ATR_MIN_CANDLES,
                "volume_min":     cfg.IV_VOLUME_MIN_CANDLES,
            },
            "module": "INDICATOR_VALIDATOR",
            "phase":  "6.5",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
indicator_validator = IndicatorValidator()

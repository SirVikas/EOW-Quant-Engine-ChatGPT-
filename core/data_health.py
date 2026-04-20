"""
EOW Quant Engine — Phase 6.5: Data Health Monitor
Continuously monitors data quality and blocks trading on stale or incomplete data.

Checks performed:
  tick_freshness    — age of the most recent tick vs DHM_STALE_TICK_SEC
  candle_coverage   — ratio of symbols with recent candles vs all tracked
  indicator_ready   — pass-through from IndicatorValidator
  ws_latency        — milliseconds since last tick arrival

Score formula (0–100):
  0.35 × tick_freshness_score
  0.25 × candle_coverage_score
  0.25 × indicator_score
  0.15 × latency_score

Rule:
  score < DHM_MIN_HEALTH_SCORE (60)  → block_trading = True
  tick age > DHM_STALE_TICK_SEC      → block_trading = True (hard override)
  latency > DHM_LATENCY_BLOCK_MS     → block_trading = True (hard override)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from config import cfg


@dataclass
class DataHealthResult:
    ok:                    bool      # True → trading allowed
    block_trading:         bool      # True → hard block (stale/missing data)
    health_score:          float     # 0–100
    tick_age_sec:          float     # seconds since last tick
    candle_coverage:       float     # fraction of symbols with fresh candles (0–1)
    indicator_ready:       bool
    latency_ms:            float     # estimated latency
    tick_freshness_score:  float
    candle_score:          float
    indicator_score:       float
    latency_score:         float
    reason:                str = ""


class DataHealthMonitor:
    """
    Evaluates data pipeline health from tick timestamps and candle coverage.

    Usage:
        result = data_health_monitor.check(
            last_tick_ts=time.time() - 5,
            symbol_tick_ages={"BTCUSDT": 3.0, "ETHUSDT": 8.0},
            indicator_ready=True,
        )
        if result.block_trading:
            skip_signal()
    """

    def __init__(self):
        self._last_check_ts: float = 0.0
        self._last_result: Optional[DataHealthResult] = None
        logger.info(
            f"[DATA-HEALTH] Phase 6.5 activated | "
            f"stale_after={cfg.DHM_STALE_TICK_SEC}s "
            f"min_score={cfg.DHM_MIN_HEALTH_SCORE} "
            f"latency_block={cfg.DHM_LATENCY_BLOCK_MS}ms"
        )

    def check(
        self,
        last_tick_ts:       float,
        symbol_tick_ages:   Dict[str, float],   # {symbol: age_seconds}
        indicator_ready:    bool,
        latency_ms:         float = 0.0,
    ) -> DataHealthResult:
        """
        Assess data pipeline health.

        Args:
            last_tick_ts:     epoch-seconds of the most recent tick received
            symbol_tick_ages: per-symbol tick age in seconds; used for candle coverage
            indicator_ready:  True when IndicatorValidator confirms all indicators warm
            latency_ms:       estimated WS latency in milliseconds (0 = unknown)

        Returns DataHealthResult; block_trading=True → reject all new signals.
        """
        now = time.time()
        tick_age = now - last_tick_ts

        # ── 1. Tick freshness ────────────────────────────────────────────────
        stale_hard = tick_age > cfg.DHM_STALE_TICK_SEC
        if tick_age <= 0:
            tick_freshness_score = 1.0
        elif tick_age >= cfg.DHM_STALE_TICK_SEC:
            tick_freshness_score = 0.0
        else:
            tick_freshness_score = 1.0 - (tick_age / cfg.DHM_STALE_TICK_SEC)

        # ── 2. Candle coverage ───────────────────────────────────────────────
        if symbol_tick_ages:
            fresh_count = sum(
                1 for age in symbol_tick_ages.values()
                if age <= cfg.DHM_STALE_TICK_SEC
            )
            coverage = fresh_count / len(symbol_tick_ages)
        else:
            coverage = 0.0
        missing_pct = 1.0 - coverage
        candle_block = missing_pct > cfg.DHM_MAX_MISSING_CANDLE_PCT
        candle_score = max(0.0, 1.0 - missing_pct / cfg.DHM_MAX_MISSING_CANDLE_PCT
                          if cfg.DHM_MAX_MISSING_CANDLE_PCT > 0 else 0.0)
        candle_score = min(1.0, candle_score)

        # ── 3. Indicator readiness ───────────────────────────────────────────
        indicator_score = 1.0 if indicator_ready else 0.0

        # ── 4. Latency ──────────────────────────────────────────────────────
        latency_hard = latency_ms > cfg.DHM_LATENCY_BLOCK_MS
        if latency_ms <= 0 or cfg.DHM_LATENCY_BLOCK_MS <= 0:
            latency_score = 1.0
        elif latency_ms >= cfg.DHM_LATENCY_BLOCK_MS:
            latency_score = 0.0
        else:
            latency_score = 1.0 - (latency_ms / cfg.DHM_LATENCY_BLOCK_MS)

        # ── Composite score ──────────────────────────────────────────────────
        raw = (
            0.35 * tick_freshness_score
            + 0.25 * candle_score
            + 0.25 * indicator_score
            + 0.15 * latency_score
        )
        health_score = round(raw * 100, 1)

        # ── Determine block ─────────────────────────────────────────────────
        block_reasons: List[str] = []
        if stale_hard:
            block_reasons.append(f"STALE_TICK({tick_age:.1f}s>{cfg.DHM_STALE_TICK_SEC}s)")
        if latency_hard:
            block_reasons.append(f"HIGH_LATENCY({latency_ms:.0f}ms>{cfg.DHM_LATENCY_BLOCK_MS:.0f}ms)")
        if health_score < cfg.DHM_MIN_HEALTH_SCORE:
            block_reasons.append(f"LOW_HEALTH({health_score:.1f}<{cfg.DHM_MIN_HEALTH_SCORE})")
        if not indicator_ready:
            block_reasons.append("INDICATORS_NOT_READY")

        block_trading = bool(block_reasons)
        ok = not block_trading
        reason = " | ".join(block_reasons) if block_reasons else ""

        if block_trading:
            logger.warning(f"[DATA-HEALTH] BLOCK: {reason}")
        else:
            logger.debug(
                f"[DATA-HEALTH] OK score={health_score:.1f} "
                f"tick_age={tick_age:.1f}s coverage={coverage:.0%} "
                f"latency={latency_ms:.0f}ms"
            )

        result = DataHealthResult(
            ok=ok,
            block_trading=block_trading,
            health_score=health_score,
            tick_age_sec=round(tick_age, 2),
            candle_coverage=round(coverage, 3),
            indicator_ready=indicator_ready,
            latency_ms=round(latency_ms, 1),
            tick_freshness_score=round(tick_freshness_score, 3),
            candle_score=round(candle_score, 3),
            indicator_score=indicator_score,
            latency_score=round(latency_score, 3),
            reason=reason,
        )
        self._last_result = result
        self._last_check_ts = now
        return result

    def last_result(self) -> Optional[DataHealthResult]:
        return self._last_result

    def summary(self) -> dict:
        r = self._last_result
        return {
            "last_check_age_sec": round(time.time() - self._last_check_ts, 1)
                                  if self._last_check_ts else None,
            "health_score":       r.health_score if r else None,
            "block_trading":      r.block_trading if r else True,
            "stale_threshold_sec": cfg.DHM_STALE_TICK_SEC,
            "min_health_score":   cfg.DHM_MIN_HEALTH_SCORE,
            "module": "DATA_HEALTH_MONITOR",
            "phase":  "6.5",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
data_health_monitor = DataHealthMonitor()

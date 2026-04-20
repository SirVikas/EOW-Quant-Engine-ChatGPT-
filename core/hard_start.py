"""
EOW Quant Engine — Phase 6.6: Hard Start Validator (Pre-Boot Stop)
Prevents the trading engine from starting when critical conditions are not met.

This is the FIRST gate in the boot sequence. It runs before any market data
connection, before any signal processing, and before any WebSocket session.

Checks performed (all must pass):
  1. indicator_candles   ≥ HSV_MIN_CANDLES_BOOT      — enough history to compute indicators
  2. indicator_validator — IndicatorValidator result must be ok
  3. ws_connectivity     — initial WebSocket reachable (soft check, not ping)
  4. config_sanity       — critical config values are within safe bounds

On failure:
  • HSV_EXIT_ON_FAIL = True  → sys.exit(1)  (production mode)
  • HSV_EXIT_ON_FAIL = False → returns HardStartResult(ok=False) and logs BOOT_FAIL
                               (test / development mode — lets tests inspect result)

Non-negotiable: NO fallback, NO soft warning mode, NO partial start.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger

from config import cfg
from core.gate_logger import gate_logger


@dataclass
class HardStartResult:
    ok:      bool
    passed:  List[str]
    failed:  List[str]
    reason:  str = ""


class HardStartValidator:
    """
    Pre-boot gate that enforces hard requirements before the engine starts.

    Usage at engine startup:
        result = hard_start_validator.validate(
            candle_count=len(market_data.candle_close_buffers.get("BTCUSDT", [])),
            indicator_ok=indicator_validator.is_ready(),
            ws_reachable=True,
        )
        hard_start_validator.enforce(result)   # exits or raises if not ok
    """

    def __init__(self):
        logger.info(
            f"[HARD-START] Phase 6.6 activated | "
            f"min_candles={cfg.HSV_MIN_CANDLES_BOOT} "
            f"exit_on_fail={cfg.HSV_EXIT_ON_FAIL}"
        )

    def validate(
        self,
        candle_count:    int,
        indicator_ok:    bool,
        ws_reachable:    bool   = True,
        extra_checks:    Optional[dict] = None,
    ) -> HardStartResult:
        """
        Run all pre-boot checks and return a HardStartResult.

        Args:
            candle_count:   total candles in primary buffer at boot
            indicator_ok:   True when IndicatorValidator.validate() passed
            ws_reachable:   True when WS endpoint is responding (default True
                            when called before WS is up — treated as soft)
            extra_checks:   optional {label: bool} map for caller-defined checks

        Returns HardStartResult; ok=False → call enforce() to halt engine.
        """
        passed: List[str] = []
        failed: List[str] = []

        # 1. Candle history floor
        if candle_count >= cfg.HSV_MIN_CANDLES_BOOT:
            passed.append(f"candle_count({candle_count}≥{cfg.HSV_MIN_CANDLES_BOOT})")
        else:
            failed.append(
                f"candle_count({candle_count}<{cfg.HSV_MIN_CANDLES_BOOT})"
            )

        # 2. Indicator readiness
        if indicator_ok:
            passed.append("indicator_validator=READY")
        else:
            failed.append("indicator_validator=NOT_READY")

        # 3. WebSocket reachability (soft — does not fail boot by itself)
        if ws_reachable:
            passed.append("ws_reachable=OK")
        else:
            # Logged as warning but not a hard failure at cold boot;
            # WsStabilityEngine will handle reconnect after engine starts.
            logger.warning("[HARD-START] WS not yet reachable — will attempt reconnect after start")
            passed.append("ws_reachable=PENDING(soft)")

        # 4. Config sanity: critical values must be in safe ranges
        config_issues = self._check_config_sanity()
        if config_issues:
            for issue in config_issues:
                failed.append(f"config:{issue}")
        else:
            passed.append("config_sanity=OK")

        # 5. Caller-provided extra checks
        if extra_checks:
            for label, result in extra_checks.items():
                if result:
                    passed.append(f"{label}=OK")
                else:
                    failed.append(f"{label}=FAIL")

        ok = len(failed) == 0
        reason = (
            "BOOT_READY"
            if ok
            else f"BOOT_BLOCKED: {', '.join(failed)}"
        )

        gate_logger.log_boot(ok=ok, stage="HARD_START", detail=reason)

        if ok:
            logger.info(
                f"[HARD-START] BOOT_OK — {len(passed)} checks passed: {passed}"
            )
        else:
            logger.critical(
                f"[HARD-START] BOOT_FAIL — {len(failed)} checks failed: {failed}"
            )

        return HardStartResult(ok=ok, passed=passed, failed=failed, reason=reason)

    def enforce(self, result: HardStartResult) -> None:
        """
        If result.ok is False:
          - HSV_EXIT_ON_FAIL=True  → sys.exit(1)
          - HSV_EXIT_ON_FAIL=False → raises RuntimeError (safe for tests)

        If result.ok is True → no-op.
        """
        if result.ok:
            return

        if cfg.HSV_EXIT_ON_FAIL:
            logger.critical(
                f"[HARD-START] FATAL — engine cannot start. "
                f"Reason: {result.reason}"
            )
            sys.exit(1)
        else:
            raise RuntimeError(
                f"[HARD-START] Engine start blocked: {result.reason}"
            )

    def validate_and_enforce(
        self,
        candle_count: int,
        indicator_ok: bool,
        ws_reachable: bool = True,
        extra_checks: Optional[dict] = None,
    ) -> HardStartResult:
        """Convenience: validate then enforce in one call."""
        result = self.validate(candle_count, indicator_ok, ws_reachable, extra_checks)
        self.enforce(result)
        return result

    # ── Config sanity sub-checks ──────────────────────────────────────────────

    @staticmethod
    def _check_config_sanity() -> List[str]:
        """Return list of config problems; empty list = all sane."""
        issues: List[str] = []

        # Risk per trade must never exceed 10% (sanity floor)
        if cfg.MAX_RISK_PER_TRADE > 0.10:
            issues.append(
                f"MAX_RISK_PER_TRADE={cfg.MAX_RISK_PER_TRADE:.0%} > 10% safety ceiling"
            )
        # Drawdown halt must be set below 30%
        if cfg.MAX_DRAWDOWN_HALT > 0.30:
            issues.append(
                f"MAX_DRAWDOWN_HALT={cfg.MAX_DRAWDOWN_HALT:.0%} > 30% safety ceiling"
            )
        # Daily risk cap must be lower than max drawdown halt
        if cfg.DAILY_RISK_CAP >= cfg.MAX_DRAWDOWN_HALT:
            issues.append(
                f"DAILY_RISK_CAP({cfg.DAILY_RISK_CAP:.0%}) ≥ MAX_DRAWDOWN_HALT "
                f"({cfg.MAX_DRAWDOWN_HALT:.0%})"
            )
        return issues

    def summary(self) -> dict:
        return {
            "min_candles_boot": cfg.HSV_MIN_CANDLES_BOOT,
            "exit_on_fail":     cfg.HSV_EXIT_ON_FAIL,
            "module": "HARD_START_VALIDATOR",
            "phase":  "6.6",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
hard_start_validator = HardStartValidator()

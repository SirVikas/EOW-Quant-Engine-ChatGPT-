"""
EOW Quant Engine — core/gating/hard_start_validator.py
Phase 6.6: Hard Start Validator — Boot-time safety enforcement

Runs once at startup. If any mandatory condition fails the engine is
prevented from starting. Two failure modes (controlled by config):

    HSV_EXIT_ON_FAIL = False  → raise RuntimeError  (dev / test)
    HSV_EXIT_ON_FAIL = True   → sys.exit(1)          (production)

Usage:
    hard_start_validator.run()   ← call once in FastAPI lifespan

Checks performed (in order):
    1. Minimum candle count        (HSV_MIN_CANDLES_BOOT)
    2. Indicator readiness         (passed in or queried from singleton)
    3. WebSocket reachability      (passed in or queried from singleton)
    4. Config sanity               (risk params always checked)
    5. Any extra caller-supplied checks
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from config import cfg
from core.gating.gate_logger import gate_logger


@dataclass
class HardStartResult:
    ok:       bool
    failures: List[str]
    warnings: List[str] = field(default_factory=list)


class HardStartValidator:
    """
    Boot-gate that prevents the engine from starting in a bad state.

    All checks are run even when the first check fails so the operator
    sees every problem in a single boot attempt.
    """

    def __init__(self):
        logger.info(
            f"[HARD-START] Phase 6.6 initialised | "
            f"exit_on_fail={cfg.HSV_EXIT_ON_FAIL} "
            f"min_candles={cfg.HSV_MIN_CANDLES_BOOT}"
        )

    # ── Primary interface ─────────────────────────────────────────────────────

    def run(
        self,
        candle_count: int = 0,
        indicator_ok: Optional[bool] = None,
        ws_reachable: Optional[bool] = None,
        extra_checks: Optional[Dict[str, bool]] = None,
    ) -> HardStartResult:
        """
        Execute all boot checks.

        Args:
            candle_count:  Number of candles loaded (0 = use config default).
            indicator_ok:  Override indicator readiness; None = auto-query.
            ws_reachable:  Override WS reachability; None = auto-query.
            extra_checks:  Dict of {label: bool} for caller-supplied checks.

        Returns:
            HardStartResult with ok=True iff all checks pass.

        Side effects:
            • Logs every check via gate_logger.boot_ok / boot_fail
            • On failure: calls self.enforce(result) which may sys.exit
        """
        failures: List[str] = []
        warnings: List[str] = []

        # 1. Minimum candle count
        min_c = cfg.HSV_MIN_CANDLES_BOOT
        if candle_count < min_c:
            failures.append(f"CANDLES_INSUFFICIENT({candle_count}<{min_c})")
            gate_logger.boot_fail(
                stage="CANDLE_CHECK",
                detail=f"count={candle_count} required={min_c}",
            )
        else:
            gate_logger.boot_ok(stage="CANDLE_CHECK", detail=f"count={candle_count}")

        # 2. Indicator readiness
        ind_ready = indicator_ok if indicator_ok is not None else self._query_indicators()
        if not ind_ready:
            failures.append("INDICATORS_NOT_READY")
            gate_logger.boot_fail(stage="INDICATOR_CHECK", detail="indicators not ready")
        else:
            gate_logger.boot_ok(stage="INDICATOR_CHECK")

        # 3. WebSocket reachability
        ws_ok = ws_reachable if ws_reachable is not None else self._query_ws()
        if not ws_ok:
            failures.append("WS_NOT_REACHABLE")
            gate_logger.boot_fail(stage="WS_CHECK", detail="websocket unreachable")
        else:
            gate_logger.boot_ok(stage="WS_CHECK")

        # 4. Config sanity (always checked)
        cfg_failures = self._check_config()
        failures.extend(cfg_failures)

        # 5. Extra caller-supplied checks
        if extra_checks:
            for label, passed in extra_checks.items():
                if not passed:
                    failures.append(f"EXTRA_FAIL:{label}")
                    gate_logger.boot_fail(stage=label, detail="caller-supplied check failed")
                else:
                    gate_logger.boot_ok(stage=label)

        ok = len(failures) == 0
        result = HardStartResult(ok=ok, failures=failures, warnings=warnings)

        if ok:
            logger.info("[HARD-START] All boot checks passed — engine cleared for start")
        else:
            logger.critical(
                f"[HARD-START] Boot checks FAILED: {' | '.join(failures)}"
            )
            self.enforce(result)

        return result

    def enforce(self, result: HardStartResult) -> None:
        """Halt the process on boot failure. Mode controlled by HSV_EXIT_ON_FAIL."""
        msg = f"HARD BLOCK — boot checks failed: {' | '.join(result.failures)}"
        if cfg.HSV_EXIT_ON_FAIL:
            logger.critical(f"[HARD-START] sys.exit(1) | {msg}")
            sys.exit(1)
        else:
            raise RuntimeError(msg)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _query_indicators(self) -> bool:
        try:
            from core.indicator_validator import indicator_validator
            return indicator_validator.is_ready()
        except Exception:
            return False

    def _query_ws(self) -> bool:
        try:
            from core.ws_stability import ws_stability_engine
            return ws_stability_engine.stability_score() > 0.0
        except Exception:
            return False

    def _check_config(self) -> List[str]:
        failures: List[str] = []

        if cfg.MAX_RISK_PER_TRADE > 0.10:
            failures.append(
                f"CONFIG_RISK_HIGH(MAX_RISK_PER_TRADE={cfg.MAX_RISK_PER_TRADE:.1%}>10%)"
            )
            gate_logger.boot_fail(
                stage="CONFIG_CHECK",
                detail=f"MAX_RISK_PER_TRADE={cfg.MAX_RISK_PER_TRADE:.1%} exceeds 10% safety cap",
            )

        if cfg.MAX_DRAWDOWN_HALT > 0.30:
            failures.append(
                f"CONFIG_DD_HIGH(MAX_DRAWDOWN_HALT={cfg.MAX_DRAWDOWN_HALT:.1%}>30%)"
            )
            gate_logger.boot_fail(
                stage="CONFIG_CHECK",
                detail=f"MAX_DRAWDOWN_HALT={cfg.MAX_DRAWDOWN_HALT:.1%} exceeds 30% safety cap",
            )

        daily_risk_cap = getattr(cfg, "DAILY_RISK_CAP", None)
        if daily_risk_cap is not None and daily_risk_cap >= cfg.MAX_DRAWDOWN_HALT:
            failures.append(
                f"CONFIG_DAILY_RISK_GE_DD(daily={daily_risk_cap:.1%}≥dd={cfg.MAX_DRAWDOWN_HALT:.1%})"
            )
            gate_logger.boot_fail(
                stage="CONFIG_CHECK",
                detail="DAILY_RISK_CAP must be < MAX_DRAWDOWN_HALT",
            )

        if not failures:
            gate_logger.boot_ok(stage="CONFIG_CHECK")

        return failures


# ── Module-level singleton ────────────────────────────────────────────────────
hard_start_validator = HardStartValidator()

"""
FTD-028 Part 4 — Risk Validator (SPAG)

Validates:
  - Risk-of-ruin calculation sanity
  - Exposure compliance within limits
  - Kill switch (halt) correctness
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


MAX_ROR_THRESHOLD  = 0.60   # risk-of-ruin > 60% is dangerous
MAX_EXPOSURE_PCT   = 1.0    # total exposure must be ≤ 100% of equity
MAX_DRAWDOWN_LIMIT = 0.15   # max allowed drawdown before halt required


class RiskValidator:
    """
    Validates risk state against SPAG safety rules.
    """

    MODULE = "RISK_VALIDATOR"
    PHASE  = "028"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[Dict[str, Any]] = []

        ror          = state.get("risk_of_ruin", 0.0) or 0.0
        exposure_pct = state.get("exposure_pct", 0.0) or 0.0
        drawdown     = state.get("current_drawdown_pct", 0.0) or 0.0
        halted       = state.get("halted", False)
        kill_switch  = state.get("kill_switch_active", False)
        trades_active = state.get("trades_active", False)

        # RoR sanity
        if not (0.0 <= ror <= 1.0):
            errors.append(self._mk("ROR_OUT_OF_RANGE",
                f"risk_of_ruin={ror:.4f} is outside [0, 1] — calculation error"))

        if ror > MAX_ROR_THRESHOLD and trades_active:
            errors.append(self._mk("HIGH_ROR_TRADING",
                f"risk_of_ruin={ror:.2%} exceeds threshold {MAX_ROR_THRESHOLD:.0%} but trades are active"))

        # Exposure compliance
        if exposure_pct > MAX_EXPOSURE_PCT:
            errors.append(self._mk("OVER_EXPOSED",
                f"exposure={exposure_pct:.2%} exceeds max {MAX_EXPOSURE_PCT:.0%}"))

        # Kill switch correctness
        if drawdown > MAX_DRAWDOWN_LIMIT and not halted and not kill_switch:
            errors.append(self._mk("KILL_SWITCH_MISSING",
                f"drawdown={drawdown:.2%} exceeds limit {MAX_DRAWDOWN_LIMIT:.0%} but kill switch not activated"))

        if kill_switch and trades_active:
            errors.append(self._mk("KILL_SWITCH_BYPASSED",
                "kill switch is active but trades are still being placed"))

        passed = len(errors) == 0
        return {
            "module":      self.MODULE,
            "phase":       self.PHASE,
            "errors":      errors,
            "error_count": len(errors),
            "ror":         round(ror, 4),
            "exposure_pct": round(exposure_pct, 4),
            "drawdown":    round(drawdown, 4),
            "passed":      passed,
            "snapshot_ts": int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

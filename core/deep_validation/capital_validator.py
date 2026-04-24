"""
FTD-028 Part 7 — Capital Validator

Validates:
  - Scaling correctness (growth tracks equity curve)
  - Drawdown-adjusted scaling applied properly
  - Over-leverage prevention
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


MAX_LEVERAGE_RATIO     = 3.0    # total exposure must not exceed 3× equity
MAX_SCALE_UP_AT_DD_PCT = 0.05   # must NOT scale up when DD > 5%
SCALE_FLOOR_PCT        = 0.50   # minimum scale factor under DD protection


class CapitalValidator:
    """
    Validates capital allocation and scaling decisions.
    """

    MODULE = "CAPITAL_VALIDATOR"
    PHASE  = "028"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []

        equity         = state.get("equity", 1.0) or 1.0
        total_exposure = state.get("total_exposure", 0.0) or 0.0
        scale_factor   = state.get("scale_factor", 1.0) or 1.0
        drawdown_pct   = state.get("current_drawdown_pct", 0.0) or 0.0
        initial_capital = state.get("initial_capital", equity) or equity

        # Leverage check
        if equity > 0:
            leverage = total_exposure / equity
            if leverage > MAX_LEVERAGE_RATIO:
                issues.append(self._mk("OVER_LEVERAGED",
                    f"leverage={leverage:.2f}× exceeds max {MAX_LEVERAGE_RATIO}× (exposure={total_exposure:.2f}, equity={equity:.2f})"))
        else:
            issues.append(self._mk("ZERO_EQUITY", "equity is zero or negative — capital validation impossible"))

        # Drawdown-adjusted scaling: must not scale UP during drawdown
        if drawdown_pct > MAX_SCALE_UP_AT_DD_PCT and scale_factor > 1.0:
            issues.append(self._mk("SCALING_UP_DURING_DD",
                f"scale_factor={scale_factor:.2f} > 1.0 while drawdown={drawdown_pct:.2%} — forbidden"))

        # Scale floor check
        if drawdown_pct > 0.10 and scale_factor > SCALE_FLOOR_PCT * 1.5:
            issues.append(self._mk("INSUFFICIENT_DD_PROTECTION",
                f"drawdown={drawdown_pct:.2%} but scale_factor={scale_factor:.2f} is not adequately reduced"))

        # Growth sanity: equity should not be negative
        if equity < 0:
            issues.append(self._mk("NEGATIVE_EQUITY", f"equity={equity:.4f} is negative"))

        passed = len(issues) == 0
        return {
            "module":         self.MODULE,
            "phase":          self.PHASE,
            "equity":         round(equity, 2),
            "leverage":       round(total_exposure / equity if equity > 0 else 0.0, 2),
            "scale_factor":   round(scale_factor, 4),
            "drawdown_pct":   round(drawdown_pct, 4),
            "issues":         issues,
            "issue_count":    len(issues),
            "passed":         passed,
            "verdict":        "PASS" if passed else "FAIL",
            "snapshot_ts":    int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

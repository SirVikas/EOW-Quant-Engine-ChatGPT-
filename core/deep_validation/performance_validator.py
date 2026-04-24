"""
FTD-028 Part 10 — Performance Validator

Validates:
  - Expected vs actual performance within tolerance
  - PnL deviation from expected range
  - Anomaly detection in key metrics
"""
from __future__ import annotations
import math
import time
from typing import Any, Dict, List


PNL_DEVIATION_THRESHOLD    = 0.30   # >30% deviation from expected PnL → anomaly
WIN_RATE_DEVIATION_LIMIT   = 0.20   # >20pp deviation from expected win rate
SHARPE_MIN_ACCEPTABLE      = -1.0   # Sharpe < -1 → performance failure


class PerformanceValidator:
    """
    Compares actual vs expected performance and detects anomalies.
    """

    MODULE = "PERFORMANCE_VALIDATOR"
    PHASE  = "028"

    def run(self, state: Dict[str, Any], expected: Dict[str, Any] = None) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []
        exp = expected or {}

        actual_pnl      = state.get("total_pnl", 0.0) or 0.0
        actual_win_rate = state.get("win_rate", 0.0) or 0.0
        sharpe          = state.get("sharpe_ratio", None)
        total_trades    = state.get("total_trades", 0) or 0

        expected_pnl      = exp.get("pnl", None)
        expected_win_rate = exp.get("win_rate", None)

        # PnL deviation check
        if expected_pnl is not None and expected_pnl != 0:
            deviation = abs(actual_pnl - expected_pnl) / abs(expected_pnl)
            if deviation > PNL_DEVIATION_THRESHOLD:
                issues.append(self._mk("PNL_DEVIATION",
                    f"actual_pnl={actual_pnl:.4f} deviates {deviation:.2%} from expected {expected_pnl:.4f}"))

        # Win rate deviation
        if expected_win_rate is not None:
            wr_deviation = abs(actual_win_rate - expected_win_rate)
            if wr_deviation > WIN_RATE_DEVIATION_LIMIT:
                issues.append(self._mk("WIN_RATE_DEVIATION",
                    f"actual_win_rate={actual_win_rate:.2%} deviates {wr_deviation:.2%} from expected {expected_win_rate:.2%}"))

        # Sharpe anomaly
        if sharpe is not None:
            if math.isnan(sharpe) or math.isinf(sharpe):
                issues.append(self._mk("SHARPE_INVALID", f"sharpe_ratio={sharpe} is NaN or Inf"))
            elif sharpe < SHARPE_MIN_ACCEPTABLE:
                issues.append(self._mk("SHARPE_BELOW_MINIMUM",
                    f"sharpe_ratio={sharpe:.4f} < minimum {SHARPE_MIN_ACCEPTABLE}"))

        # Trade count sanity
        if total_trades < 0:
            issues.append(self._mk("NEGATIVE_TRADE_COUNT", f"total_trades={total_trades} is negative"))

        passed = len(issues) == 0
        return {
            "module":        self.MODULE,
            "phase":         self.PHASE,
            "actual_pnl":    round(actual_pnl, 4),
            "actual_win_rate": round(actual_win_rate, 4),
            "sharpe":        sharpe,
            "total_trades":  total_trades,
            "issues":        issues,
            "issue_count":   len(issues),
            "passed":        passed,
            "verdict":       "PASS" if passed else "FAIL",
            "snapshot_ts":   int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

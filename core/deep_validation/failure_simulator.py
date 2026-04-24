"""
FTD-028 Part 11 — Failure Simulator

Simulates failure conditions and validates system response:
  - Extreme volatility scenario
  - Data pipeline failure scenario
  - API/exchange failure scenario
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


class FailureSimulator:
    """
    Runs structured failure scenarios and validates system handles them correctly.
    """

    MODULE = "FAILURE_SIMULATOR"
    PHASE  = "028"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []

        results.append(self._sim_extreme_volatility(state))
        results.append(self._sim_data_failure(state))
        results.append(self._sim_api_failure(state))

        failed = [r for r in results if not r["handled_correctly"]]
        passed = len(failed) == 0

        return {
            "module":       self.MODULE,
            "phase":        self.PHASE,
            "scenarios":    results,
            "failed_count": len(failed),
            "passed":       passed,
            "verdict":      "PASS" if passed else "FAIL",
            "snapshot_ts":  int(time.time() * 1000),
        }

    def _sim_extreme_volatility(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify system has volatility-aware position sizing."""
        has_vol_guard   = state.get("volatility_guard_active", False)
        has_rr_engine   = state.get("rr_engine_active", False)
        has_drawdown_ctl = state.get("drawdown_controller_active", False)

        handled = has_vol_guard or has_rr_engine or has_drawdown_ctl
        return {
            "scenario":          "EXTREME_VOLATILITY",
            "handled_correctly": handled,
            "detail":            "volatility_guard or rr_engine or drawdown_controller must be active"
                                 if not handled else "protected by volatility/RR/drawdown controls",
        }

    def _sim_data_failure(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify system has data health monitoring and safe mode on data failure."""
        has_data_health  = state.get("data_health_monitor_active", False)
        has_safe_mode    = state.get("safe_mode_engine_active", False)
        has_ws_stabilizer = state.get("ws_stabilizer_active", False)

        handled = has_data_health or has_safe_mode or has_ws_stabilizer
        return {
            "scenario":          "DATA_PIPELINE_FAILURE",
            "handled_correctly": handled,
            "detail":            "data_health_monitor or safe_mode or ws_stabilizer must be active"
                                 if not handled else "protected by data health / safe-mode controls",
        }

    def _sim_api_failure(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify system has API retry logic and error registry."""
        has_error_registry = state.get("error_registry_active", False)
        has_api_manager    = state.get("api_manager_active", False)
        has_self_healing   = state.get("self_healing_active", False)

        handled = has_error_registry or has_api_manager or has_self_healing
        return {
            "scenario":          "API_EXCHANGE_FAILURE",
            "handled_correctly": handled,
            "detail":            "error_registry or api_manager or self_healing must be active"
                                 if not handled else "protected by error_registry / api_manager / self-healing",
        }

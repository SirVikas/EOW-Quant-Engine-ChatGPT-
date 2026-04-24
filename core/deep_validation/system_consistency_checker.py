"""
FTD-028 Part 12 — System Consistency Checker

Validates:
  - Cross-module state synchronization
  - That all modules agree on key state (equity, halt, mode)
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


_EQUITY_TOLERANCE = 0.01   # 1% tolerance for equity disagreement between modules


class SystemConsistencyChecker:
    """
    Ensures all system modules report consistent state.
    """

    MODULE = "SYSTEM_CONSISTENCY_CHECKER"
    PHASE  = "028"

    def run(self, module_states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        module_states: dict of module_name → state_dict, each with optional keys:
            equity, halted, mode, risk_active
        """
        issues: List[Dict[str, Any]] = []

        # Collect equity values across modules
        equities = {
            name: s["equity"]
            for name, s in module_states.items()
            if "equity" in s and s["equity"] is not None
        }
        if len(equities) > 1:
            min_eq = min(equities.values())
            max_eq = max(equities.values())
            if min_eq > 0 and (max_eq - min_eq) / min_eq > _EQUITY_TOLERANCE:
                issues.append(self._mk("EQUITY_DESYNC",
                    f"equity mismatch across modules: min={min_eq:.4f}, max={max_eq:.4f} "
                    f"(delta={(max_eq - min_eq) / min_eq:.2%})"))

        # Halt state consistency
        halt_states = {
            name: s["halted"]
            for name, s in module_states.items()
            if "halted" in s
        }
        if len(set(halt_states.values())) > 1:
            issues.append(self._mk("HALT_STATE_DESYNC",
                f"modules disagree on halt state: {halt_states}"))

        # Mode consistency
        modes = {
            name: s["mode"]
            for name, s in module_states.items()
            if "mode" in s
        }
        if len(set(modes.values())) > 1:
            issues.append(self._mk("MODE_DESYNC",
                f"modules disagree on operating mode: {modes}"))

        passed = len(issues) == 0
        return {
            "module":         self.MODULE,
            "phase":          self.PHASE,
            "modules_checked": list(module_states.keys()),
            "issues":         issues,
            "issue_count":    len(issues),
            "passed":         passed,
            "verdict":        "PASS" if passed else "FAIL",
            "snapshot_ts":    int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, message: str) -> Dict[str, Any]:
        return {"code": code, "message": message}

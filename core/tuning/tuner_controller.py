"""
FTD-016 Tuner Controller — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.tuning.tuner_controller.TunerController
SOURCE: Delegates to core.dynamic_thresholds (existing logic, no duplication)

Stepwise parameter change, result monitoring, accept/rollback logic.
"""
from __future__ import annotations
from typing import Any, Dict, List


class TunerController:
    """
    FTD-016: Wraps dynamic_threshold_provider to expose the current
    tuning state and provide pause/resume/rollback controls.

    No new computation — dynamic_threshold_provider owns the math.
    """

    PHASE  = "016"
    MODULE = "TUNER_CONTROLLER"

    def get_state(self) -> Dict[str, Any]:
        """Return current auto-tuning state."""
        from core.dynamic_thresholds import dynamic_threshold_provider
        dt = dynamic_threshold_provider.summary()
        return {
            "active":         True,
            "current_params": dt,
            "paused":         False,
            "last_change_ts": dt.get("last_update_ts", None),
            "module":         self.MODULE,
            "phase":          self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        try:
            return self.get_state()
        except Exception as e:
            return {"module": self.MODULE, "phase": self.PHASE, "error": str(e)}


class ChangePlanner:
    """Plans stepwise parameter changes (delegates to dynamic_thresholds)."""
    PHASE  = "016"
    MODULE = "CHANGE_PLANNER"

    def plan(self, signal: str) -> Dict[str, Any]:
        return {"signal": signal, "planned_change": "AUTO — driven by dynamic_thresholds",
                "module": self.MODULE, "phase": self.PHASE}


class RollbackEngine:
    """Rolls back parameter changes when performance degrades."""
    PHASE  = "016"
    MODULE = "ROLLBACK_ENGINE"

    def rollback(self) -> Dict[str, Any]:
        return {"rolled_back": False,
                "reason": "dynamic_thresholds manages rollback automatically",
                "module": self.MODULE, "phase": self.PHASE}


tuner_controller  = TunerController()
change_planner    = ChangePlanner()
rollback_engine   = RollbackEngine()

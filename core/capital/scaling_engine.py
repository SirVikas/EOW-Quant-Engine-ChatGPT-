"""
FTD-024 Capital Scaling Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.capital.scaling_engine.ScalingEngine
SOURCE: Delegates to core.capital_allocator + core.capital_concentrator
        (existing logic, no duplication)

Capital growth tracking, scaling state, rollback on failure.
"""
from __future__ import annotations
from typing import Any, Dict


class ScalingEngine:
    """
    FTD-024: Aggregates capital_allocator and capital_concentrator
    to expose a unified capital scaling state.
    """

    PHASE  = "024"
    MODULE = "SCALING_ENGINE"

    def get_state(self, equity: float = 0.0, initial_capital: float = 0.0) -> Dict[str, Any]:
        """Return capital scaling state."""
        from core.capital_allocator   import capital_allocator
        from core.capital_concentrator import capital_concentrator

        alloc = capital_allocator.summary()
        conc  = capital_concentrator.summary() if hasattr(capital_concentrator, "summary") else {}

        growth_pct = (
            ((equity - initial_capital) / initial_capital * 100)
            if initial_capital > 0 else 0.0
        )

        return {
            "equity":          round(equity, 2),
            "initial_capital": round(initial_capital, 2),
            "growth_pct":      round(growth_pct, 2),
            "allocator":       alloc,
            "concentrator":    conc,
            "scaling_active":  alloc.get("active", False),
            "module":          self.MODULE,
            "phase":           self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        try:
            return self.get_state()
        except Exception as e:
            return {"module": self.MODULE, "phase": self.PHASE, "error": str(e)}


scaling_engine = ScalingEngine()

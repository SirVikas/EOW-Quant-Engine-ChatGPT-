"""
FTD-020 Portfolio Allocation Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.portfolio.allocation_engine.AllocationEngine
SOURCE: Delegates to core.capital_allocator (existing logic, no duplication)

Capital allocation, exposure management, portfolio rebalancing view.
"""
from __future__ import annotations
from typing import Any, Dict, List


class AllocationEngine:
    """
    FTD-020: Wraps capital_allocator + risk_controller to expose
    allocation state, exposure per position, and rebalance signals.
    """

    PHASE  = "020"
    MODULE = "ALLOCATION_ENGINE"

    def get_state(
        self,
        positions: List[Dict[str, Any]] = None,
        equity: float = 0.0,
    ) -> Dict[str, Any]:
        """Return portfolio allocation view."""
        from core.capital_allocator import capital_allocator
        alloc_summary = capital_allocator.summary()

        positions = positions or []
        total_exposed = sum(
            abs(float(p.get("qty", 0)) * float(p.get("entry_px", 0)))
            for p in positions
        )
        exposure_pct = (total_exposed / equity * 100) if equity > 0 else 0.0

        return {
            "open_positions":   len(positions),
            "total_exposure":   round(total_exposed, 2),
            "exposure_pct":     round(exposure_pct, 2),
            "allocator":        alloc_summary,
            "positions":        positions,
            "module":           self.MODULE,
            "phase":            self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        try:
            return self.get_state()
        except Exception as e:
            return {"module": self.MODULE, "phase": self.PHASE, "error": str(e)}


allocation_engine = AllocationEngine()

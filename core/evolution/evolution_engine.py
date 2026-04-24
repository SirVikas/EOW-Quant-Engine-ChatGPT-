"""
FTD-019 Strategy Evolution Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.evolution.evolution_engine.EvolutionEngine
SOURCE: Delegates to core.genome_engine (existing logic, no duplication)

Champion vs challenger logic, strategy variant generation, validation.
"""
from __future__ import annotations
from typing import Any, Dict, List


class EvolutionEngine:
    """
    FTD-019: Wraps genome_engine to expose champion/challenger view,
    active DNA summary, and variant counts.
    """

    PHASE  = "019"
    MODULE = "EVOLUTION_ENGINE"

    def get_state(self) -> Dict[str, Any]:
        """Return evolution state from genome_engine."""
        from core.genome_engine import GenomeEngine as _GE
        # genome singleton lives in main; fall back to a fresh instance for tests
        try:
            import main as _m
            _genome = _m.genome
        except Exception:
            _genome = _GE()
        state = _genome.export_state()
        dna   = state.get("active_dna") or {}

        strategies = []
        for name, params in dna.items():
            strategies.append({
                "name":       name,
                "param_count": len(params) if isinstance(params, dict) else 0,
                "role":       "CHAMPION",   # genome maintains one champion per strategy
            })

        return {
            "generation":    state.get("generation", 0),
            "fitness":       state.get("fitness", 0.0),
            "strategies":    strategies,
            "champion_count": len(strategies),
            "challenger_count": 0,   # challengers are generated during mutation cycle
            "last_mutation": state.get("last_mutation_ts", None),
            "module":        self.MODULE,
            "phase":         self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        try:
            return self.get_state()
        except Exception as e:
            return {"module": self.MODULE, "phase": self.PHASE, "error": str(e)}


evolution_engine = EvolutionEngine()

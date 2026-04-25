"""
FTD-030B — Learning Memory Layer

Upgrades the system from self-correcting → self-learning.
Pipeline: Remember → Generalize → Apply → Forget → Improve

Integrates with:
  FTD-028 (Deep Validation) — meta_score + contradiction flags
  FTD-029 (Self-Correction) — memory_applier → change_planner injection
                             — memory_store.update() after resolve_cycle()
  FTD-025A (Export)         — learning memory section in system report
"""
from core.learning_memory.learning_memory_orchestrator import (
    learning_memory_orchestrator,
    LearningMemoryOrchestrator,
)

__all__ = ["learning_memory_orchestrator", "LearningMemoryOrchestrator"]

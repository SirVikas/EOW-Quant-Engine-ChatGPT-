"""
PHOENIX CORTEX — Meta-Governance Layer  [CX-1 through CX-5]

CORTEX governs the PHOENIX module ecosystem.  It does not replace any
module — it acts as Governor, Arbitrator, Coordinator, and Supervisor.

Architecture:
  CX-1  module_registry.py    Canonical catalog of every PHOENIX module
  CX-2  dependency_mapper.py  Full dependency graph + boot order
  CX-3  conflict_engine.py    Conflict detection + Constitutional Rules
  CX-4  influence_matrix.py   Dynamic influence weights (advisory)
  CX-5  blame_engine.py       Loss blame attribution — "who caused it?"

PHOENIX Institutional Stack:
  Layer 2  NEXUS          (Connectivity + Intelligence)
  Layer 3  OBSERVATORY-X  (Observation)
  Layer 4  CORTEX         (Governance)     ← THIS PACKAGE
  Layer 5  PCAO           (Future COO)     pending

Boot log: [PHOENIX CORTEX Active] Registry | Dependencies | Conflict | Influence | Blame
"""
from core.cortex.module_registry  import cortex_module_registry
from core.cortex.dependency_mapper import cortex_dependency_mapper
from core.cortex.conflict_engine  import conflict_engine
from core.cortex.influence_matrix import influence_matrix
from core.cortex.blame_engine     import blame_engine

__all__ = [
    "cortex_module_registry",
    "cortex_dependency_mapper",
    "conflict_engine",
    "influence_matrix",
    "blame_engine",
]

"""
EOW Quant Engine — core/orchestrator
Phase 7A Integration: Execution Orchestrator Package

Central runtime controller that routes every new-trade attempt through the
full gate-aware profit pipeline.

Usage:
    from core.orchestrator import execution_orchestrator, TickContext, CycleResult, GateCheckResult
"""
from core.orchestrator.execution_orchestrator import (
    ExecutionOrchestrator,
    execution_orchestrator,
    TickContext,
    CycleResult,
    GateCheckResult,
    _EXECUTION_AUTHORITY,
)
from core.orchestrator.execution_lock import ExecutionLock

__all__ = [
    "ExecutionOrchestrator",
    "execution_orchestrator",
    "TickContext",
    "CycleResult",
    "GateCheckResult",
    "_EXECUTION_AUTHORITY",
    "ExecutionLock",
]

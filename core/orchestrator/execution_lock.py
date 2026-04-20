"""
EOW Quant Engine — core/orchestrator/execution_lock.py
Phase 7A.2: Execution Lock — Hard Guard Against Parallel Execution Loops

Guarantees that only ONE execution loop can be active at any time.
If a second loop attempts to acquire the lock, the system CRASHES immediately.
"""
from __future__ import annotations


class ExecutionLock:
    """
    Process-level execution lock.

    Only one call to run_cycle() may be active at any instant.
    A second acquire() while the lock is held raises RuntimeError —
    the system does NOT recover silently, it crashes intentionally.
    """

    _active: bool = False

    @classmethod
    def acquire(cls) -> None:
        if cls._active:
            raise RuntimeError(
                "CRITICAL: Multiple execution loops detected"
            )
        cls._active = True

    @classmethod
    def release(cls) -> None:
        cls._active = False

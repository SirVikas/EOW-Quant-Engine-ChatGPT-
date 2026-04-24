"""
FTD-029 Part 7 — Cooldown Manager

Rules (Q6):
  - ≤3 correction cycles per session
  - 4-hour cooldown between cycles

Critical Bypass (Part 7 spec):
  - Risk violation detected, OR
  - Contradiction marked critical, OR
  - system_score < 50
  → bypass cooldown
"""
from __future__ import annotations
import time
from typing import Any, Dict


MAX_CYCLES_PER_SESSION = 3
COOLDOWN_SECONDS       = 4 * 3600   # 4 hours
CRITICAL_SCORE_FLOOR   = 50.0


class CooldownManager:
    """
    Tracks correction cycle count and cooldown window.
    Exposes bypass logic for critical situations.
    """

    MODULE = "COOLDOWN_MANAGER"
    PHASE  = "029"

    def __init__(self):
        self._session_cycles: int   = 0
        self._last_cycle_ts:  float = 0.0

    def can_run(
        self,
        risk_violated:          bool  = False,
        contradiction_critical: bool  = False,
        system_score:           float = 100.0,
    ) -> Dict[str, Any]:
        """
        Returns: allowed, bypass_active, blocking_reason, cooldown_remaining_s
        """
        now = time.time()

        # Session limit
        if self._session_cycles >= MAX_CYCLES_PER_SESSION:
            return {
                "allowed": False,
                "bypass_active": False,
                "blocking_reason": f"SESSION_LIMIT: {self._session_cycles}/{MAX_CYCLES_PER_SESSION} cycles used",
                "cooldown_remaining_s": 0,
            }

        # Cooldown check
        elapsed          = now - self._last_cycle_ts
        in_cooldown      = self._last_cycle_ts > 0 and elapsed < COOLDOWN_SECONDS
        remaining        = max(0, int(COOLDOWN_SECONDS - elapsed)) if in_cooldown else 0

        # Critical bypass
        critical_bypass = (
            risk_violated
            or contradiction_critical
            or system_score < CRITICAL_SCORE_FLOOR
        )

        if in_cooldown and not critical_bypass:
            return {
                "allowed": False,
                "bypass_active": False,
                "blocking_reason": f"COOLDOWN: {remaining}s remaining",
                "cooldown_remaining_s": remaining,
            }

        bypass_msg = " (CRITICAL_BYPASS)" if in_cooldown and critical_bypass else ""
        return {
            "allowed": True,
            "bypass_active": in_cooldown and critical_bypass,
            "blocking_reason": None,
            "cooldown_remaining_s": 0,
            "detail": f"cycle {self._session_cycles + 1}/{MAX_CYCLES_PER_SESSION}{bypass_msg}",
        }

    def record_cycle(self) -> None:
        """Call after a successful correction cycle is executed."""
        self._session_cycles += 1
        self._last_cycle_ts   = time.time()

    def reset(self) -> None:
        """Human override (Q8): reset session counter and cooldown."""
        self._session_cycles = 0
        self._last_cycle_ts  = 0.0

    def summary(self) -> Dict[str, Any]:
        now     = time.time()
        elapsed = now - self._last_cycle_ts
        remaining = max(0, int(COOLDOWN_SECONDS - elapsed)) if self._last_cycle_ts > 0 else 0
        return {
            "module":              self.MODULE,
            "phase":               self.PHASE,
            "session_cycles":      self._session_cycles,
            "max_cycles":          MAX_CYCLES_PER_SESSION,
            "cooldown_hours":      COOLDOWN_SECONDS // 3600,
            "cooldown_remaining_s": remaining,
            "last_cycle_ts":       int(self._last_cycle_ts * 1000) if self._last_cycle_ts else None,
            "snapshot_ts":         int(now * 1000),
        }

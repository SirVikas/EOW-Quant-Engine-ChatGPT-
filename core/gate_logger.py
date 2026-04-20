"""
EOW Quant Engine — Phase 6.6: Gate Logger
Mandatory visibility layer for all gating decisions.

Every gate decision — ALLOWED, BLOCKED, or SAFE_MODE — is recorded here
with a structured log line and stored in a rolling in-memory history.

Log format:
  [GATE] BLOCKED    | reason=INDICATOR_NOT_READY | detail=...
  [GATE] ALLOWED    | context=BTCUSDT/TrendFollowing
  [GATE] SAFE_MODE  | reason=WS_UNSTABLE | enforcer=SafeModeEnforcer

Statistics exposed:
  total_allowed, total_blocked, block_reason_counts, last_event
"""
from __future__ import annotations

import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

from loguru import logger

from config import cfg


# ── Event types ───────────────────────────────────────────────────────────────
GATE_ALLOWED   = "ALLOWED"
GATE_BLOCKED   = "BLOCKED"
GATE_SAFE_MODE = "SAFE_MODE"
GATE_BOOT_FAIL = "BOOT_FAIL"
GATE_BOOT_OK   = "BOOT_OK"


@dataclass
class GateEvent:
    ts:       float
    event:    str       # ALLOWED | BLOCKED | SAFE_MODE | BOOT_FAIL | BOOT_OK
    reason:   str
    context:  str = ""  # symbol/strategy or boot stage label
    detail:   str = ""  # extra diagnostic info


class GateLogger:
    """
    Structured, queryable gate decision log.

    Call log_blocked(), log_allowed(), log_safe_mode(), or log_boot() from
    any gate module. All calls emit a formatted loguru line AND append to
    the rolling in-memory history.

    No other module should use loguru directly for gate decisions — all
    gate log output must flow through this class for consistency.
    """

    def __init__(self):
        self._history: Deque[GateEvent] = deque(maxlen=cfg.GL_HISTORY_SIZE)
        self._total_allowed: int = 0
        self._total_blocked: int = 0
        self._block_counts: Dict[str, int] = defaultdict(int)
        self._safe_mode_activations: int = 0
        logger.info(
            f"[GATE-LOGGER] Phase 6.6 activated | history_size={cfg.GL_HISTORY_SIZE}"
        )

    # ── Public logging API ────────────────────────────────────────────────────

    def log_blocked(self, reason: str, context: str = "", detail: str = "") -> None:
        """Record and emit a BLOCKED gate decision."""
        msg = f"[GATE] BLOCKED | reason={reason}"
        if context:
            msg += f" | context={context}"
        if detail:
            msg += f" | detail={detail}"
        logger.warning(msg)
        self._record(GATE_BLOCKED, reason, context, detail)
        self._total_blocked += 1
        self._block_counts[reason] += 1

    def log_allowed(self, context: str = "", detail: str = "") -> None:
        """Record and emit an ALLOWED gate decision (only when PTG_LOG_ALLOWED)."""
        if cfg.PTG_LOG_ALLOWED:
            msg = "[GATE] ALLOWED"
            if context:
                msg += f" | context={context}"
            logger.debug(msg)
        self._record(GATE_ALLOWED, "", context, detail)
        self._total_allowed += 1

    def log_safe_mode(self, reason: str, enforcer: str = "", detail: str = "") -> None:
        """Record and emit a SAFE_MODE gate event."""
        msg = f"[GATE] SAFE_MODE_ACTIVE | reason={reason}"
        if enforcer:
            msg += f" | enforcer={enforcer}"
        if detail:
            msg += f" | detail={detail}"
        logger.error(msg)
        self._record(GATE_SAFE_MODE, reason, enforcer, detail)
        self._safe_mode_activations += 1

    def log_boot(self, ok: bool, stage: str, detail: str = "") -> None:
        """Record a boot validation event (BOOT_OK or BOOT_FAIL)."""
        event = GATE_BOOT_OK if ok else GATE_BOOT_FAIL
        if ok:
            logger.info(f"[GATE] BOOT_OK | stage={stage}")
        else:
            logger.critical(f"[GATE] BOOT_FAIL | stage={stage} | detail={detail}")
        self._record(event, stage, "", detail)

    # ── Query API ─────────────────────────────────────────────────────────────

    def recent_events(self, n: int = 20) -> List[GateEvent]:
        events = list(self._history)
        return events[-n:]

    def recent_blocks(self, n: int = 10) -> List[GateEvent]:
        return [e for e in self._history if e.event == GATE_BLOCKED][-n:]

    def stats(self) -> dict:
        total = self._total_allowed + self._total_blocked
        block_rate = (self._total_blocked / total) if total > 0 else 0.0
        top_reason = (
            max(self._block_counts, key=self._block_counts.get)
            if self._block_counts else ""
        )
        return {
            "total_allowed":         self._total_allowed,
            "total_blocked":         self._total_blocked,
            "block_rate":            round(block_rate, 4),
            "safe_mode_activations": self._safe_mode_activations,
            "top_block_reason":      top_reason,
            "block_reason_counts":   dict(self._block_counts),
        }

    def last_event(self) -> Optional[GateEvent]:
        return self._history[-1] if self._history else None

    def summary(self) -> dict:
        return {
            **self.stats(),
            "history_size":   cfg.GL_HISTORY_SIZE,
            "events_stored":  len(self._history),
            "module": "GATE_LOGGER",
            "phase":  "6.6",
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _record(self, event: str, reason: str, context: str, detail: str) -> None:
        self._history.append(GateEvent(
            ts=time.time(), event=event,
            reason=reason, context=context, detail=detail,
        ))


# ── Module-level singleton ────────────────────────────────────────────────────
gate_logger = GateLogger()

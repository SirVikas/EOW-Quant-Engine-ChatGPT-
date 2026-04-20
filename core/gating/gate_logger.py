"""
EOW Quant Engine — core/gating/gate_logger.py
Phase 6.6: Centralized Gate Decision Logger

Every gate decision — ALLOWED, BLOCKED, or SAFE_MODE — emits a structured
log line through loguru and is stored in a rolling in-memory history.

Required log formats:
    [GATE] BLOCKED    | reason=INDICATOR_NOT_READY
    [GATE] SAFE_MODE  | reason=WS_UNSTABLE
    [GATE] ALLOWED    | context=BTCUSDT/TrendFollowing
    [GATE] BOOT_FAIL  | stage=HARD_START | detail=...
    [GATE] BOOT_OK    | stage=HARD_START

This is the ONLY place gate decisions should be logged.
"""
from __future__ import annotations

import time
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional

from loguru import logger

from config import cfg


GATE_ALLOWED   = "ALLOWED"
GATE_BLOCKED   = "BLOCKED"
GATE_SAFE_MODE = "SAFE_MODE"
GATE_BOOT_FAIL = "BOOT_FAIL"
GATE_BOOT_OK   = "BOOT_OK"


@dataclass
class GateEvent:
    ts:      float
    event:   str
    reason:  str
    context: str = ""
    detail:  str = ""


class GatingLogger:
    """
    Structured, queryable audit log for all gate decisions.
    Thread-safe for read queries; append-only writes are GIL-protected.
    """

    def __init__(self):
        self._history: Deque[GateEvent] = deque(maxlen=cfg.GL_HISTORY_SIZE)
        self._total_allowed: int = 0
        self._total_blocked: int = 0
        self._block_counts: Dict[str, int] = defaultdict(int)
        self._safe_mode_count: int = 0
        logger.info(
            f"[GATE] Gate logger online | history={cfg.GL_HISTORY_SIZE}"
        )

    # ── Logging API ───────────────────────────────────────────────────────────

    def blocked(self, reason: str, context: str = "", detail: str = "") -> None:
        msg = f"[GATE] BLOCKED | reason={reason}"
        if context:
            msg += f" | context={context}"
        if detail:
            msg += f" | detail={detail}"
        logger.warning(msg)
        self._append(GATE_BLOCKED, reason, context, detail)
        self._total_blocked += 1
        self._block_counts[reason] += 1

    def allowed(self, context: str = "") -> None:
        if cfg.PTG_LOG_ALLOWED:
            msg = f"[GATE] ALLOWED"
            if context:
                msg += f" | context={context}"
            logger.debug(msg)
        self._append(GATE_ALLOWED, "", context, "")
        self._total_allowed += 1

    def safe_mode(self, reason: str, detail: str = "") -> None:
        logger.error(f"[GATE] SAFE_MODE | reason={reason}" + (f" | {detail}" if detail else ""))
        self._append(GATE_SAFE_MODE, reason, "", detail)
        self._safe_mode_count += 1

    def boot_ok(self, stage: str, detail: str = "") -> None:
        logger.info(f"[GATE] BOOT_OK | stage={stage}" + (f" | {detail}" if detail else ""))
        self._append(GATE_BOOT_OK, stage, "", detail)

    def boot_fail(self, stage: str, detail: str) -> None:
        logger.critical(f"[GATE] BOOT_FAIL | stage={stage} | detail={detail}")
        self._append(GATE_BOOT_FAIL, stage, "", detail)

    # ── Query API ─────────────────────────────────────────────────────────────

    def recent(self, n: int = 20) -> List[GateEvent]:
        return list(self._history)[-n:]

    def recent_blocks(self, n: int = 10) -> List[GateEvent]:
        return [e for e in self._history if e.event == GATE_BLOCKED][-n:]

    def stats(self) -> dict:
        total = self._total_allowed + self._total_blocked
        return {
            "total_allowed":   self._total_allowed,
            "total_blocked":   self._total_blocked,
            "block_rate":      round(self._total_blocked / total, 4) if total else 0.0,
            "safe_mode_count": self._safe_mode_count,
            "top_reason":      max(self._block_counts, key=self._block_counts.get, default=""),
            "by_reason":       dict(self._block_counts),
        }

    def summary(self) -> dict:
        return {**self.stats(), "events_stored": len(self._history),
                "module": "GATING_LOGGER", "phase": "6.6"}

    def _append(self, event: str, reason: str, context: str, detail: str) -> None:
        self._history.append(
            GateEvent(ts=time.time(), event=event,
                      reason=reason, context=context, detail=detail)
        )


# ── Module-level singleton ────────────────────────────────────────────────────
gate_logger = GatingLogger()

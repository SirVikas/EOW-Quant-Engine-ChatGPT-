"""
EOW Quant Engine — WebSocket Truth Engine  (FTD-REF-025)
Single source of truth for WebSocket connection state reported to the UI.

Decouples the actual reconnect mechanism (WsStabilizer) from what the UI
displays. The truth engine derives a human-readable state from elapsed time
since the last tick and the number of reconnect attempts already made.

State model:
  WS_CONNECTED    — last tick < CONNECTED_THRESH (20 s) — all good
  WS_RECONNECTING — last tick < STALE_THRESH     (60 s) — trying to reconnect
  WS_STALE        — tick gap ≥ 60 s + reconnect_attempts < MAX_ATTEMPTS
  WS_DOWN         — tick gap ≥ 60 s + reconnect_attempts ≥ MAX_ATTEMPTS

UI label mapping:
  CONNECTED     → "🟢 LIVE"
  RECONNECTING  → "🟡 RECONNECTING"
  STALE         → "🟠 DELAYED"
  DOWN          → "🔴 DISCONNECTED"
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from loguru import logger


# ── Thresholds (seconds) ──────────────────────────────────────────────────────
CONNECTED_THRESH  = 20     # gap < 20 s → CONNECTED
RECONNECTING_THRESH = 60   # gap < 60 s → RECONNECTING (was just trying to reconnect)
MAX_ATTEMPTS_FOR_STALE = 3  # if ≥ this many reconnect attempts without recovery → DOWN

# ── State constants ───────────────────────────────────────────────────────────
WS_CONNECTED    = "WS_CONNECTED"
WS_RECONNECTING = "WS_RECONNECTING"
WS_STALE        = "WS_STALE"
WS_DOWN         = "WS_DOWN"

# UI labels
_UI_LABELS = {
    WS_CONNECTED:    "🟢 LIVE",
    WS_RECONNECTING: "🟡 RECONNECTING",
    WS_STALE:        "🟠 DELAYED",
    WS_DOWN:         "🔴 DISCONNECTED",
}


@dataclass
class WsTruthSnapshot:
    state:              str
    ui_label:           str
    gap_seconds:        float
    reconnect_attempts: int
    last_tick_ts:       float
    last_updated_ts:    float


class WsTruthEngine:
    """
    Stateful WebSocket truth reporter.
    Call record_tick() on every incoming tick.
    Call record_reconnect_attempt() whenever the stabilizer tries to reconnect.
    Call record_reconnect_success() on successful recovery.
    Call get_state() / snapshot() to get current truth for the UI.
    """

    def __init__(self):
        self._last_tick_ts:       float = time.time()   # default: start healthy
        self._reconnect_attempts: int   = 0
        self._last_state:         str   = WS_CONNECTED

    # ── Public ────────────────────────────────────────────────────────────────

    def record_tick(self):
        """Call whenever a live tick arrives — marks the connection as healthy."""
        self._last_tick_ts       = time.time()
        self._reconnect_attempts = 0   # reset on successful data flow
        if self._last_state != WS_CONNECTED:
            logger.info("[WS-TRUTH] Stream recovered → WS_CONNECTED")
        self._last_state = WS_CONNECTED

    def record_reconnect_attempt(self):
        """Call when the stabilizer is about to attempt a reconnect."""
        self._reconnect_attempts += 1
        logger.debug(
            f"[WS-TRUTH] Reconnect attempt #{self._reconnect_attempts}"
        )

    def record_reconnect_success(self):
        """Call after a successful reconnect (connection re-established)."""
        self._reconnect_attempts = 0
        self._last_tick_ts       = time.time()

    def get_state(self) -> str:
        """Return the current WS truth state string."""
        gap = time.time() - self._last_tick_ts

        if gap < CONNECTED_THRESH:
            return WS_CONNECTED

        if gap < RECONNECTING_THRESH:
            return WS_RECONNECTING

        # Gap ≥ 60 s: distinguish STALE vs DOWN by attempts
        if self._reconnect_attempts < MAX_ATTEMPTS_FOR_STALE:
            return WS_STALE

        return WS_DOWN

    def get_ui_label(self) -> str:
        """Return the human-readable UI label for the current state."""
        return _UI_LABELS.get(self.get_state(), "🔴 DISCONNECTED")

    def snapshot(self) -> WsTruthSnapshot:
        state = self.get_state()
        now   = time.time()
        if state != self._last_state:
            logger.info(f"[WS-TRUTH] State changed: {self._last_state} → {state}")
            self._last_state = state
        return WsTruthSnapshot(
            state=state,
            ui_label=_UI_LABELS.get(state, "🔴 DISCONNECTED"),
            gap_seconds=round(now - self._last_tick_ts, 1),
            reconnect_attempts=self._reconnect_attempts,
            last_tick_ts=self._last_tick_ts,
            last_updated_ts=now,
        )

    def to_dict(self) -> dict:
        s = self.snapshot()
        return {
            "state":              s.state,
            "ui_label":           s.ui_label,
            "gap_seconds":        s.gap_seconds,
            "reconnect_attempts": s.reconnect_attempts,
            "thresholds": {
                "connected_thresh_sec":    CONNECTED_THRESH,
                "reconnecting_thresh_sec": RECONNECTING_THRESH,
                "max_attempts_for_stale":  MAX_ATTEMPTS_FOR_STALE,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
ws_truth_engine = WsTruthEngine()

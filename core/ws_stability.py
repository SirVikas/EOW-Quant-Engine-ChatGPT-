"""
EOW Quant Engine — Phase 6.5: WS Stability Engine
Higher-level WebSocket stability coordinator that sits above the low-level
WsStabilizer (ws_stabilizer.py) and WsTruthEngine.

Responsibilities:
  • Track cumulative reconnect count across the session
  • Detect unhealthy connection patterns (rapid reconnects, sustained stale)
  • Trigger safe mode when reconnects exceed WSS_MAX_RECONNECTS_SAFE_MODE (3)
  • Provide a stability_score (0–100) for BootDeployabilityEngine
  • Track heartbeat intervals and latency estimates

Stability score formula:
  Base 100, deductions:
    −20 per reconnect (capped at −60)
    −30 if currently disconnected / stale
    −20 if latency > WSS_LATENCY_WARN_MS
    −30 if latency > WSS_LATENCY_BLOCK_MS

Rule:
  reconnect_count > WSS_MAX_RECONNECTS_SAFE_MODE → trigger_safe_mode()
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from config import cfg


@dataclass
class WsStabilitySnapshot:
    stability_score:    float     # 0–100
    reconnect_count:    int
    is_connected:       bool
    latency_ms:         float
    safe_mode_triggered: bool
    state:              str       # "HEALTHY" | "DEGRADED" | "UNSTABLE" | "SAFE_MODE"
    reason:             str = ""


class WsStabilityEngine:
    """
    Session-level WebSocket stability tracker.

    Integrates with SafeModeController (lazy import to avoid circular deps).
    Can be fed tick timestamps and reconnect events from WsStabilizer or
    directly from MarketDataProvider callbacks.

    Usage:
        ws_stability.record_tick(latency_ms=12.0)
        ws_stability.record_reconnect()
        snapshot = ws_stability.snapshot()
    """

    def __init__(self):
        self._reconnect_count: int = 0
        self._last_tick_ts: float = time.time()
        self._last_latency_ms: float = 0.0
        self._session_start: float = time.time()
        self._safe_mode_triggered: bool = False
        self._heartbeat_count: int = 0
        self._consecutive_healthy: int = 0
        logger.info(
            f"[WS-STABILITY] Phase 6.5 activated | "
            f"safe_mode_at={cfg.WSS_MAX_RECONNECTS_SAFE_MODE} reconnects "
            f"latency_warn={cfg.WSS_LATENCY_WARN_MS}ms "
            f"latency_block={cfg.WSS_LATENCY_BLOCK_MS}ms"
        )

    # ── Event recording ───────────────────────────────────────────────────────

    def record_tick(self, latency_ms: float = 0.0) -> None:
        """Call on every incoming tick from the data feed."""
        now = time.time()
        self._last_tick_ts = now
        self._last_latency_ms = latency_ms
        self._consecutive_healthy += 1

        if latency_ms > cfg.WSS_LATENCY_WARN_MS:
            logger.debug(
                f"[WS-STABILITY] High latency: {latency_ms:.0f}ms "
                f"(warn>{cfg.WSS_LATENCY_WARN_MS:.0f}ms)"
            )

    def record_reconnect(self) -> None:
        """Call each time a reconnect attempt is made."""
        self._reconnect_count += 1
        self._consecutive_healthy = 0
        logger.warning(
            f"[WS-STABILITY] Reconnect #{self._reconnect_count} recorded "
            f"(safe_mode_threshold={cfg.WSS_MAX_RECONNECTS_SAFE_MODE})"
        )

        if self._reconnect_count > cfg.WSS_MAX_RECONNECTS_SAFE_MODE:
            self._trigger_safe_mode(
                f"RECONNECT_LIMIT({self._reconnect_count}>{cfg.WSS_MAX_RECONNECTS_SAFE_MODE})"
            )

    def record_recovery(self) -> None:
        """Call when connection is successfully restored."""
        self._consecutive_healthy = 0
        logger.info("[WS-STABILITY] Connection recovered")

    def reset_reconnects(self) -> None:
        """Reset reconnect counter (call after a clean recovery period)."""
        self._reconnect_count = 0
        self._safe_mode_triggered = False
        logger.info("[WS-STABILITY] Reconnect counter reset")

    # ── Scoring ───────────────────────────────────────────────────────────────

    def stability_score(self) -> float:
        """
        Calculate current WS stability score 0–100.
        Used by BootDeployabilityEngine.
        """
        now = time.time()
        tick_age = now - self._last_tick_ts
        is_connected = tick_age < cfg.DHM_STALE_TICK_SEC

        score = 100.0

        # Reconnect penalty
        reconnect_penalty = min(self._reconnect_count * 20.0, 60.0)
        score -= reconnect_penalty

        # Connection state penalty
        if not is_connected:
            score -= 30.0

        # Latency penalty
        if self._last_latency_ms > cfg.WSS_LATENCY_BLOCK_MS:
            score -= 30.0
        elif self._last_latency_ms > cfg.WSS_LATENCY_WARN_MS:
            score -= 10.0

        # Safe mode hard floor
        if self._safe_mode_triggered:
            score = min(score, 20.0)

        return round(max(0.0, min(100.0, score)), 1)

    def snapshot(self) -> WsStabilitySnapshot:
        now = time.time()
        tick_age = now - self._last_tick_ts
        is_connected = tick_age < cfg.DHM_STALE_TICK_SEC
        score = self.stability_score()

        if self._safe_mode_triggered:
            state = "SAFE_MODE"
        elif score >= 80:
            state = "HEALTHY"
        elif score >= 50:
            state = "DEGRADED"
        else:
            state = "UNSTABLE"

        reasons = []
        if self._reconnect_count > 0:
            reasons.append(f"reconnects={self._reconnect_count}")
        if not is_connected:
            reasons.append(f"stale({tick_age:.1f}s)")
        if self._last_latency_ms > cfg.WSS_LATENCY_WARN_MS:
            reasons.append(f"latency={self._last_latency_ms:.0f}ms")

        return WsStabilitySnapshot(
            stability_score=score,
            reconnect_count=self._reconnect_count,
            is_connected=is_connected,
            latency_ms=self._last_latency_ms,
            safe_mode_triggered=self._safe_mode_triggered,
            state=state,
            reason=" | ".join(reasons) if reasons else "",
        )

    def is_healthy(self) -> bool:
        return self.stability_score() >= 70.0 and not self._safe_mode_triggered

    # ── Safe mode ─────────────────────────────────────────────────────────────

    def _trigger_safe_mode(self, reason: str) -> None:
        if self._safe_mode_triggered:
            return
        self._safe_mode_triggered = True
        logger.error(f"[WS-STABILITY] SAFE MODE triggered: {reason}")
        try:
            from core.safe_mode import safe_mode_controller
            safe_mode_controller.activate(f"WS_STABILITY: {reason}")
        except Exception as exc:
            logger.debug(f"[WS-STABILITY] safe_mode import failed: {exc}")

    def summary(self) -> dict:
        snap = self.snapshot()
        return {
            "stability_score":    snap.stability_score,
            "state":              snap.state,
            "reconnect_count":    snap.reconnect_count,
            "is_connected":       snap.is_connected,
            "latency_ms":         snap.latency_ms,
            "safe_mode_triggered": snap.safe_mode_triggered,
            "thresholds": {
                "max_reconnects_safe_mode": cfg.WSS_MAX_RECONNECTS_SAFE_MODE,
                "latency_warn_ms":          cfg.WSS_LATENCY_WARN_MS,
                "latency_block_ms":         cfg.WSS_LATENCY_BLOCK_MS,
            },
            "module": "WS_STABILITY_ENGINE",
            "phase":  "6.5",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
ws_stability_engine = WsStabilityEngine()

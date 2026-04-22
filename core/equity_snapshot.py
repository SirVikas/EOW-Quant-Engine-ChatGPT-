"""
EOW Quant Engine — qFTD-009 FINAL: Equity Snapshot Manager
Provides true equity continuity across restarts without full trade replay.

Design (per qFTD-009):
  SAVE  — after every trade close, write equity + trade_count + timestamp
  BOOT  — load snapshot first; if consistent with replay, restore instantly
          if mismatch or no snapshot, fall back to full trade replay
  UI    — equity display always sourced from persisted value, never reset to 0

File location: data/exports/equity_snapshot.json
Format:
  {
    "equity":      999.50,
    "trade_count": 116,
    "timestamp":   "2026-04-22T08:47:53Z",
    "session_id":  "abc123"
  }

Consistency check:
  |snapshot_equity - replay_equity| / replay_equity > MISMATCH_TOLERANCE
  → log warning and use replay value (safer)
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from loguru import logger


_SNAPSHOT_PATH = os.path.join("data", "exports", "equity_snapshot.json")
_MISMATCH_TOLERANCE = 0.01   # 1% — larger gap triggers warning and replay fallback


@dataclass
class SnapshotData:
    equity:      float
    trade_count: int
    timestamp:   str
    session_id:  str = ""


class EquitySnapshotManager:
    """
    Saves and restores equity state across process restarts.
    Thread-safe writes (JSON is written atomically via temp-rename).
    """

    def __init__(self, path: str = _SNAPSHOT_PATH):
        self._path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    # ── Save ─────────────────────────────────────────────────────────────────

    def save(self, equity: float, trade_count: int, session_id: str = "") -> None:
        """Persist current equity state. Call after every trade close."""
        snap = SnapshotData(
            equity=round(equity, 4),
            trade_count=trade_count,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            session_id=session_id,
        )
        tmp = self._path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(asdict(snap), f, indent=2)
            os.replace(tmp, self._path)
            logger.debug(
                f"[EQUITY-SNAPSHOT] saved equity={equity:.4f} "
                f"trades={trade_count} ts={snap.timestamp}"
            )
        except Exception as exc:
            logger.warning(f"[EQUITY-SNAPSHOT] save failed: {exc}")

    # ── Load ─────────────────────────────────────────────────────────────────

    def load(self) -> Optional[SnapshotData]:
        """Load snapshot. Returns None if file missing or corrupt."""
        if not os.path.exists(self._path):
            logger.info("[EQUITY-SNAPSHOT] no snapshot file found — will use replay")
            return None
        try:
            with open(self._path) as f:
                raw = json.load(f)
            snap = SnapshotData(
                equity=float(raw["equity"]),
                trade_count=int(raw["trade_count"]),
                timestamp=raw.get("timestamp", ""),
                session_id=raw.get("session_id", ""),
            )
            logger.info(
                f"[EQUITY-SNAPSHOT] loaded equity={snap.equity:.4f} "
                f"trades={snap.trade_count} ts={snap.timestamp}"
            )
            return snap
        except Exception as exc:
            logger.warning(f"[EQUITY-SNAPSHOT] load failed: {exc} — will use replay")
            return None

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self, snapshot_equity: float, replay_equity: float) -> bool:
        """
        Returns True when snapshot and replay are consistent.
        Logs a warning and returns False on mismatch > MISMATCH_TOLERANCE.
        When replay_equity is 0 the snapshot is accepted unconditionally.
        """
        if replay_equity == 0:
            return True
        gap = abs(snapshot_equity - replay_equity) / abs(replay_equity)
        if gap > _MISMATCH_TOLERANCE:
            logger.warning(
                f"[EQUITY-SNAPSHOT] MISMATCH snapshot={snapshot_equity:.4f} "
                f"replay={replay_equity:.4f} gap={gap:.2%} "
                f"(>{_MISMATCH_TOLERANCE:.0%}) — using replay value"
            )
            return False
        return True

    # ── Periodic save ─────────────────────────────────────────────────────────

    async def start_periodic_save(
        self,
        equity_fn:       Callable[[], float],
        trade_count_fn:  Callable[[], int],
        interval_sec:    int = 30,
        session_id:      str = "",
    ) -> None:
        """
        Background task: saves equity snapshot every `interval_sec` seconds.
        Guarantees snapshot exists even when no trades were closed during a session.
        Wire into asyncio tasks list at boot.

        Args:
            equity_fn:      callable returning current equity (e.g. lambda: scaler.equity)
            trade_count_fn: callable returning trade count  (e.g. lambda: len(pnl_calc.trades))
            interval_sec:   save interval in seconds (default 30)
            session_id:     optional session identifier for the snapshot
        """
        logger.info(
            f"[EQUITY-SNAPSHOT] Periodic save started "
            f"(every {interval_sec}s)"
        )
        while True:
            await asyncio.sleep(interval_sec)
            try:
                self.save(
                    equity=equity_fn(),
                    trade_count=trade_count_fn(),
                    session_id=session_id,
                )
            except Exception as exc:
                logger.warning(f"[EQUITY-SNAPSHOT] periodic save error: {exc}")

    # ── Boot helper ───────────────────────────────────────────────────────────

    def restore_or_replay(
        self,
        replay_equity: float,
        replay_trade_count: int,
    ) -> float:
        """
        Core boot decision (qFTD-009 §Q2.3 / §Q5.2):
          1. Load snapshot
          2. Validate against replay
          3. Return snapshot equity if valid, else replay equity

        This is the single call site in main.py startup.
        """
        snap = self.load()
        if snap is None:
            logger.info(
                f"[EQUITY-SNAPSHOT] no snapshot → using replay "
                f"equity={replay_equity:.4f}"
            )
            return replay_equity

        if self.validate(snap.equity, replay_equity):
            logger.info(
                f"[EQUITY-SNAPSHOT] snapshot validated → restoring "
                f"equity={snap.equity:.4f} (replay={replay_equity:.4f})"
            )
            return snap.equity

        # Mismatch — trust replay (safer)
        return replay_equity


# ── Module-level singleton ────────────────────────────────────────────────────
equity_snapshot = EquitySnapshotManager()

"""
FTD-DECISION-SNAP — Suppression Event Persistence Layer

Append-only JSONL log of gate suppression events.
Each suppression writes one line; readers can grep by gate, session, regime,
or pipeline for longitudinal causal analysis.

Fail-open contract: record() NEVER raises.  A write failure is silently
swallowed so suppression logging can never block the execution path.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from core.time.session_definitions import get_session_label

_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "suppression_events.jsonl"


class SuppressionEventLog:
    """
    Thread-safe, append-only JSONL suppression log.

    Schema per line:
        utc_ts    — Unix epoch seconds at suppression time
        symbol    — trading pair
        strategy  — full strategy_id string (may include _PAPER_SPEED suffix)
        pipeline  — "PAPER_SPEED" | "PRIMARY_STRATEGY"
        gate      — gate name that blocked the signal (e.g. "RL_GATE")
        session   — UTC session bucket at suppression time
        regime    — market regime string
        reason    — gate-specific reason string (optional, may be empty)
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass  # fail-open: if dir creation fails, record() will also fail silently

    def record(
        self,
        *,
        gate: str,
        symbol: str,
        strategy: str,
        regime: str,
        utc_hour: int,
        reason: str = "",
    ) -> None:
        """Append one suppression event.  Never raises."""
        try:
            pipeline = "PAPER_SPEED" if strategy.endswith("_PAPER_SPEED") else "PRIMARY_STRATEGY"
            event = {
                "utc_ts":   int(time.time()),
                "symbol":   symbol,
                "strategy": strategy,
                "pipeline": pipeline,
                "gate":     gate,
                "session":  get_session_label(utc_hour),
                "regime":   regime,
                "reason":   reason,
            }
            line = json.dumps(event, separators=(",", ":"))
            with self._lock:
                with self._path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
        except Exception:
            pass  # suppression logging must never interrupt execution

"""
Exit Coordinator — SHADOW mode (FTD-094A blueprint phases X1 + X2)

X1 (audit shim) + X2 (shadow parity) in one safe seam. Observes the live
position's stop-loss / take-profit at one point per tick, detects the NET
transition since the previous observation, classifies it, validates the unified
Exit-Coordinator invariants, and records an audit event.

It has NO write authority: it never sets stop_loss / take_profit / qty and never
closes a position. It only reads and records. Gated by
cfg.EXIT_COORDINATOR_SHADOW_ENABLED (default False).

Why one seam instead of instrumenting all 12 writers (EXIT_AUTHORITY_MAP §1):
touching every live SL/TP write site is the riskier change. Observing net
per-tick state transitions captures the same provenance-by-category and validates
the invariants without modifying any live exit code. Exact per-writer source
tagging (full X1) would require per-site instrumentation — a later, separate step.

Invariants validated (UNIFIED_EXIT_AUTHORITY_BLUEPRINT §2):
  I-1  stop-loss moves only in the protective direction, EXCEPT a terminal
       close-pending write (SL set to ~price to force an exit next tick).
  I-2  take-profit widening is flagged as "needs grant" (currently unguarded — H-3).
  I-4  every transition emits one audit record (field, old, new, category).
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Any, Deque, Dict, Optional

_RING = 500
_PRICE_EPS = 1e-6


@dataclass
class ExitEvent:
    ts: int
    symbol: str
    field: str            # "stop_loss" | "take_profit"
    old: float
    new: float
    direction: str        # "TIGHTEN" | "WIDEN"
    category: str         # PROTECTIVE_TIGHTEN | TERMINAL_CLOSE_PENDING | TP_WIDEN | ...
    invariant_ok: bool
    note: str = ""


class ExitCoordinatorShadow:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state: Dict[str, dict] = {}
        self._events: Deque[ExitEvent] = deque(maxlen=_RING)
        self._transitions = 0
        self._parity_ok = 0
        self._parity_violations = 0

    @staticmethod
    def _is_protective(side: str, old_sl: float, new_sl: float) -> bool:
        # Protective = stop moved toward locking profit: up for LONG, down for SHORT.
        return new_sl > old_sl if side == "LONG" else new_sl < old_sl

    @staticmethod
    def _is_terminal(new_sl: float, price: float) -> bool:
        # VTP/TIME/FAST exits set SL to ~current price to force a close next tick.
        return abs(new_sl - price) <= max(_PRICE_EPS, abs(price) * 1e-4)

    @staticmethod
    def _tp_is_widen(side: str, old_tp: float, new_tp: float) -> bool:
        return new_tp > old_tp if side == "LONG" else new_tp < old_tp

    def observe(self, position: Any, price: float) -> Optional[list]:
        """Detect + classify net SL/TP transitions for one open position.
        NEVER mutates `position`. Returns the list of ExitEvents recorded (or [])."""
        sym = getattr(position, "symbol", "?")
        side = getattr(position, "side", "LONG")
        sl = float(getattr(position, "stop_loss", 0.0) or 0.0)
        tp = float(getattr(position, "take_profit", 0.0) or 0.0)

        recorded: list = []
        with self._lock:
            prev = self._state.get(sym)
            if prev is not None:
                if sl != prev["sl"]:
                    recorded.append(self._record_sl(sym, side, prev["sl"], sl, price))
                if tp != prev["tp"]:
                    recorded.append(self._record_tp(sym, side, prev["tp"], tp))
            self._state[sym] = {"sl": sl, "tp": tp, "side": side}
        return recorded

    def _record_sl(self, sym, side, old_sl, new_sl, price) -> ExitEvent:
        protective = self._is_protective(side, old_sl, new_sl)
        terminal = self._is_terminal(new_sl, price)
        if terminal:
            category, ok, note = "TERMINAL_CLOSE_PENDING", True, "SL→price (forced exit) — exempt from tighten-only"
        elif protective:
            category, ok, note = "PROTECTIVE_TIGHTEN", True, ""
        else:
            category, ok, note = "NON_PROTECTIVE_LOOSEN", False, "I-1 violation: SL loosened without terminal intent (H-1)"
        ev = ExitEvent(int(time.time() * 1000), sym, "stop_loss", round(old_sl, 6),
                       round(new_sl, 6), "TIGHTEN" if protective else "WIDEN", category, ok, note)
        self._commit(ev)
        return ev

    def _record_tp(self, sym, side, old_tp, new_tp) -> ExitEvent:
        widen = self._tp_is_widen(side, old_tp, new_tp)
        # I-2: widening is permitted today but unguarded — flag it as needs-grant.
        category = "TP_WIDEN_NEEDS_GRANT" if widen else "TP_TIGHTEN"
        ok = not widen
        note = "I-2: TP widened with no explicit grant (H-3)" if widen else ""
        ev = ExitEvent(int(time.time() * 1000), sym, "take_profit", round(old_tp, 6),
                       round(new_tp, 6), "WIDEN" if widen else "TIGHTEN", category, ok, note)
        self._commit(ev)
        return ev

    def _commit(self, ev: ExitEvent) -> None:
        self._events.append(ev)
        self._transitions += 1
        if ev.invariant_ok:
            self._parity_ok += 1
        else:
            self._parity_violations += 1

    def on_close(self, symbol: str) -> None:
        with self._lock:
            self._state.pop(symbol, None)

    def summary(self) -> dict:
        with self._lock:
            return {
                "shadow_enabled": _flag(),
                "transitions_observed": self._transitions,
                "invariant_ok": self._parity_ok,
                "invariant_violations": self._parity_violations,
                "parity_pct": round(self._parity_ok / self._transitions * 100, 1) if self._transitions else None,
                "active_positions": len(self._state),
                "recent_events": [asdict(e) for e in list(self._events)[-25:]],
            }

    def reset(self) -> None:
        with self._lock:
            self._state.clear()
            self._events.clear()
            self._transitions = 0
            self._parity_ok = 0
            self._parity_violations = 0


def _flag() -> bool:
    try:
        from config import cfg
        return bool(getattr(cfg, "EXIT_COORDINATOR_SHADOW_ENABLED", False))
    except Exception:
        return False


# Module-level singleton
exit_coordinator_shadow = ExitCoordinatorShadow()

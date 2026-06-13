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
        self._resolve_parity_ok = 0       # X3-a: resolve() vs live agreement
        self._resolve_parity_total = 0

    def record_parity(self, match: bool) -> None:
        with self._lock:
            self._resolve_parity_total += 1
            if match:
                self._resolve_parity_ok += 1

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
                "resolve_parity_ok": self._resolve_parity_ok,
                "resolve_parity_total": self._resolve_parity_total,
                "resolve_parity_pct": round(self._resolve_parity_ok / self._resolve_parity_total * 100, 1) if self._resolve_parity_total else None,
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
            self._resolve_parity_ok = 0
            self._resolve_parity_total = 0


def _flag() -> bool:
    try:
        from config import cfg
        return bool(getattr(cfg, "EXIT_COORDINATOR_SHADOW_ENABLED", False))
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# X3-a — Exit Coordinator ARBITER (pure, non-acting). Builds the single-author
# machinery: typed intents + a precedence/invariant resolver. Nothing here writes
# a live SL/TP or closes a position; resolve() is a pure function and the parity
# harness only logs. Live routing (X3-d) is BLOCKED behind parity + forward + ADR.
# ─────────────────────────────────────────────────────────────────────────────

_STAGE_ORDER = ["OBSERVE", "VALIDATE", "APPROVE", "ADVISE", "GATE", "AUTHORITY"]


def _stage_idx(stage: str) -> int:
    return _STAGE_ORDER.index(stage) if stage in _STAGE_ORDER else 0


@dataclass
class ExitIntent:
    source: str            # "emergency" | "risk_rules" | "trade_manager" | "xte"
    kind: str              # "CLOSE" | "PARTIAL" | "SET_SL" | "SET_TP" | "HOLD"
    value: float = 0.0     # proposed price (SL/TP) or fraction (PARTIAL)
    reason: str = ""
    grant: bool = False    # explicit grant required to WIDEN take-profit (I-2)
    lifecycle_stage: str = "OBSERVE"   # advisor's stage; gates XTE acting


@dataclass
class ExitDecision:
    sl: float
    tp: float
    close: bool = False
    partial: Optional[float] = None
    rationale: list = None


def _is_tighten_sl(side: str, cur: float, val: float) -> bool:
    return val > cur if side == "LONG" else val < cur


def _is_widen_tp(side: str, cur: float, val: float) -> bool:
    return val > cur if side == "LONG" else val < cur


def resolve(intents, side, current_sl, current_tp, price=0.0, xte_stage="OBSERVE") -> ExitDecision:
    """Pure arbiter: one decision from all advisor intents, by precedence
    (emergency > terminal > partial > protective-SL > TP) under invariants I-1
    (SL tighten-only) and I-2 (TP widen needs grant). XTE intents are ignored
    unless its lifecycle stage >= ADVISE. NEVER mutates anything."""
    rationale = []

    def _r(it, note):
        return {"source": it.source, "kind": it.kind, "value": it.value, "note": note}

    # Tier 1 — emergency: overrides everything
    for it in intents:
        if it.source == "emergency":
            return ExitDecision(sl=current_sl, tp=current_tp, close=True,
                                rationale=[_r(it, "emergency override (tier 1)")])
    # Tier 2 — terminal close
    for it in intents:
        if it.kind == "CLOSE":
            return ExitDecision(sl=current_sl, tp=current_tp, close=True,
                                rationale=[_r(it, "terminal close (tier 2)")])
    new_sl, new_tp, partial = current_sl, current_tp, None
    # Tier 3 — partial
    for it in intents:
        if it.kind == "PARTIAL":
            partial = it.value
            rationale.append(_r(it, "partial (tier 3)"))
            break
    # Tier 4 — protective SL (tighten-only); XTE muted below ADVISE
    for it in intents:
        if it.kind != "SET_SL":
            continue
        if it.source == "xte" and _stage_idx(it.lifecycle_stage) < _stage_idx("ADVISE"):
            rationale.append(_r(it, "XTE muted (stage < ADVISE)"))
            continue
        if _is_tighten_sl(side, new_sl, it.value):
            new_sl = it.value
            rationale.append(_r(it, "protective tighten (tier 4)"))
        else:
            rationale.append(_r(it, "REJECTED: would loosen SL (I-1)"))
    # Tier 5 — TP: widen needs grant
    for it in intents:
        if it.kind != "SET_TP":
            continue
        if _is_widen_tp(side, current_tp, it.value):
            if it.grant:
                new_tp = it.value
                rationale.append(_r(it, "TP widen (granted, I-2)"))
            else:
                rationale.append(_r(it, "REJECTED: TP widen needs grant (I-2)"))
        else:
            new_tp = it.value
            rationale.append(_r(it, "TP tighten (tier 5)"))
    return ExitDecision(sl=new_sl, tp=new_tp, close=False, partial=partial, rationale=rationale)


# Adapter helpers — construct intents from already-computed advisor outputs
# (no formula re-derivation; X3-b wires these to live producers).
def risk_rules_intent(proposed_sl, reason="trail/BE/ratchet"):
    return ExitIntent(source="risk_rules", kind="SET_SL", value=proposed_sl, reason=reason)


def trade_manager_intent(action, new_sl=0.0, new_tp=0.0, reason=""):
    m = {"MOVE_BE": ("SET_SL", new_sl), "TRAIL_SL": ("SET_SL", new_sl),
         "EXTEND_TP": ("SET_TP", new_tp), "VTP_EXIT": ("CLOSE", 0.0),
         "TIME_EXIT": ("CLOSE", 0.0), "FAST_FAIL": ("CLOSE", 0.0),
         "PARTIAL_TP": ("PARTIAL", 0.5)}
    kind, val = m.get(action, ("HOLD", 0.0))
    grant = (action == "EXTEND_TP")   # VTP extension is the documented grant path
    return ExitIntent(source="trade_manager", kind=kind, value=val, reason=reason or action, grant=grant)


def xte_intent(advisory_label, proposed_sl, stage="OBSERVE", reason=""):
    kind = "SET_SL" if advisory_label in ("TIGHTEN", "SCALE_OUT", "BREAKEVEN") else "HOLD"
    return ExitIntent(source="xte", kind=kind, value=proposed_sl, reason=reason or advisory_label,
                      lifecycle_stage=stage)


def parity_check(decision: ExitDecision, live_sl, live_tp, live_close, eps=1e-6):
    """Shadow parity: does resolve() agree with what the live writers actually did?
    Records agreement on the singleton for X3-b's parity proof. Logs only."""
    match = (abs(decision.sl - live_sl) <= eps and abs(decision.tp - live_tp) <= eps
             and decision.close == live_close)
    exit_coordinator_shadow.record_parity(match)
    return match


# Module-level singleton
exit_coordinator_shadow = ExitCoordinatorShadow()

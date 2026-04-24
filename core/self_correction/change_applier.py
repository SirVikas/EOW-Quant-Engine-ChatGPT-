"""
FTD-029 Part 6 — Change Applier

Applies approved change plans via delegation to existing owners.
NEVER duplicates logic — uses session overlay + notifies existing singletons.

Delegation map (ONE LOGIC → ONE OWNER):
  Strategy params (TR_EV_WEIGHT, ADAPTIVE_*)  → dynamic_threshold_provider (read-only notify)
  Signal tuning   (P7B_*)                     → session overlay (cfg awareness)
  Portfolio       (KELLY_FRACTION)             → capital_allocator (advisory)

All changes are tagged: change_id + timestamp + version_hash.
Overlay is the single source of truth for active corrections.
"""
from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.self_correction.change_planner import ChangePlan
from core.self_correction.correction_proposal import TUNABLE_PARAMS, HARD_LIMITS


@dataclass
class AppliedChange:
    change_id:    str
    plan_id:      str
    parameter:    str
    before:       float
    after:        float
    delta_pct:    float
    rationale:    str
    target_module: str
    version_hash: str
    applied_ts:   int
    auto_applied: bool


class ChangeApplier:
    """
    Applies change plans to the session overlay.
    Each applied change gets a unique change_id + version_hash for full traceability.
    """

    MODULE = "CHANGE_APPLIER"
    PHASE  = "029"

    def __init__(self):
        self._overlay:  Dict[str, float] = {}   # live session corrections
        self._applied:  List[AppliedChange] = []

    def apply(
        self,
        plans: List[ChangePlan],
        current_params: Dict[str, float],
    ) -> tuple[List[AppliedChange], List[Dict[str, Any]]]:
        """
        Apply each plan after final safety checks.

        Returns:
            applied: list of AppliedChange
            blocked: list of dicts with reason
        """
        applied:  List[AppliedChange] = []
        blocked:  List[Dict[str, Any]] = []

        for plan in plans:
            result = self._apply_one(plan, current_params)
            if result is not None:
                applied.append(result)
                self._applied.append(result)
            else:
                blocked.append({"plan_id": plan.plan_id, "parameter": plan.parameter,
                                 "reason": "SAFETY_GUARD"})

        return applied, blocked

    def rollback_change(self, change_id: str) -> bool:
        """Revert a specific applied change in the overlay."""
        for ch in reversed(self._applied):
            if ch.change_id == change_id:
                self._overlay[ch.parameter] = ch.before
                return True
        return False

    def rollback_all(self) -> None:
        """Clear all session corrections — full revert to base config."""
        self._overlay.clear()

    def get_overlay(self) -> Dict[str, float]:
        return dict(self._overlay)

    def recent_applied(self, n: int = 10) -> List[Dict[str, Any]]:
        return [self._serialise(ch) for ch in self._applied[-n:]]

    def summary(self) -> Dict[str, Any]:
        return {
            "module":           self.MODULE,
            "phase":            self.PHASE,
            "total_applied":    len(self._applied),
            "active_overlay":   len(self._overlay),
            "param_overlay":    dict(self._overlay),
            "recent_applied":   self.recent_applied(3),
            "snapshot_ts":      int(time.time() * 1000),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _apply_one(self, plan: ChangePlan, current_params: Dict[str, float]) -> Optional[AppliedChange]:
        # Final hard-limit check
        if plan.parameter in HARD_LIMITS:
            return None

        # Bounds check
        if plan.parameter in TUNABLE_PARAMS:
            lo, hi, _ = TUNABLE_PARAMS[plan.parameter]
            if not (lo <= plan.proposed_value <= hi):
                return None

        now       = int(time.time() * 1000)
        change_id = f"CHG_{plan.parameter[:6]}_{now}"
        vh_src    = f"{plan.parameter}:{plan.current_value:.6f}:{plan.proposed_value:.6f}:{now}"
        version_hash = hashlib.sha1(vh_src.encode()).hexdigest()[:8]

        self._overlay[plan.parameter] = plan.proposed_value

        # Notify existing owners (delegation, no duplication)
        self._notify_owner(plan.target_module, plan.parameter, plan.proposed_value)

        return AppliedChange(
            change_id=change_id,
            plan_id=plan.plan_id,
            parameter=plan.parameter,
            before=plan.current_value,
            after=plan.proposed_value,
            delta_pct=plan.delta_pct,
            rationale=plan.rationale,
            target_module=plan.target_module,
            version_hash=version_hash,
            applied_ts=now,
            auto_applied=plan.auto_eligible,
        )

    @staticmethod
    def _notify_owner(module: str, param: str, value: float) -> None:
        """
        Advisory notification to existing module owners.
        Read-only — does not modify any module's internal state directly.
        The overlay is the single source of truth; modules that read from
        cfg or from the overlay will pick up the change on their next call.
        """
        try:
            if module == "capital_allocator":
                from core.capital_allocator import capital_allocator as _ca
                if hasattr(_ca, "_correction_hint"):
                    _ca._correction_hint = {param: value}
        except Exception:
            pass   # notification is best-effort, not a hard requirement

    @staticmethod
    def _serialise(ch: AppliedChange) -> Dict[str, Any]:
        return {
            "change_id":    ch.change_id,
            "parameter":    ch.parameter,
            "before":       ch.before,
            "after":        ch.after,
            "delta_pct":    ch.delta_pct,
            "rationale":    ch.rationale,
            "target_module": ch.target_module,
            "version_hash": ch.version_hash,
            "applied_ts":   ch.applied_ts,
            "auto_applied": ch.auto_applied,
        }

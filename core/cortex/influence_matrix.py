"""
PHOENIX CORTEX — Influence Matrix  [CX-4]

The Influence Matrix assigns a dynamic weight to each registered module,
representing its trusted contribution to the final trading decision.

Initial weights come from ModuleDefinition.influence_weight (0–100).
The matrix then adjusts weights based on:
  - Economic contribution (PnL attribution from blame attribution engine)
  - Health score (a module that keeps failing loses influence)
  - Conflict score (a module involved in many conflicts loses weight)
  - Constitutional floor (critical modules cannot go below MIN_CRITICAL_WEIGHT)

Weight update rules
───────────────────
  Weight is never auto-applied to live trading without human approval.
  All weight changes are advisory — they feed the CORTEX recommendation
  engine and are visible in the dashboard.

  Decay:  weight × (1 - DECAY_FACTOR) if module repeatedly causes issues
  Boost:  weight × (1 + BOOST_FACTOR) if module consistently profitable
  Floor:  critical modules min weight = 10
  Ceiling: max weight = 50

Tier-based maximum influence weights:
  Tier A max: 40   (direct execution impact)
  Tier B max: 25   (indirect impact)
  Tier C max: 10   (observability — should not influence trading)
  Tier D max: 5    (infrastructure)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Constants ─────────────────────────────────────────────────────────────────

DECAY_FACTOR  = 0.05    # 5 % decay per negative event
BOOST_FACTOR  = 0.02    # 2 % boost per positive event
MIN_CRITICAL  = 10.0    # critical modules never go below this
MAX_WEIGHT    = 50.0

TIER_MAX: Dict[str, float] = {"A": 40.0, "B": 25.0, "C": 10.0, "D": 5.0}


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ModuleInfluence:
    module_key: str
    tier: str
    current_weight: float
    initial_weight: float
    min_weight: float
    max_weight: float
    health_factor: float    # 0–1; 1 = fully healthy
    conflict_count: int     # times involved in a conflict
    positive_events: int    # profitable attributions
    negative_events: int    # loss attributions
    last_adjusted: float = field(default_factory=time.time)
    locked: bool = False    # if True, weight is immutable (constitutional lock)


# ── Matrix ────────────────────────────────────────────────────────────────────

class InfluenceMatrix:
    """
    Maintains and evolves the influence weight for every CORTEX module.
    All mutations produce advisory outputs only — never auto-applied.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._matrix: Dict[str, ModuleInfluence] = {}
        self._built = False
        self._history: List[dict] = []   # audit trail of adjustments

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> None:
        from core.cortex.module_registry import cortex_module_registry
        modules = cortex_module_registry.all()
        with self._lock:
            for m in modules:
                if m.key in self._matrix:
                    continue
                tier_max = TIER_MAX.get(m.tier, 5.0)
                init_w   = min(m.influence_weight, tier_max)
                min_w    = MIN_CRITICAL if m.critical else 0.0
                # Lock constitutional-protection modules
                locked   = m.key in (
                    "global_gate_controller", "risk_engine",
                    "safe_mode_engine", "drawdown_controller",
                )
                self._matrix[m.key] = ModuleInfluence(
                    module_key=m.key,
                    tier=m.tier,
                    current_weight=init_w,
                    initial_weight=init_w,
                    min_weight=min_w,
                    max_weight=tier_max,
                    health_factor=1.0,
                    conflict_count=0,
                    positive_events=0,
                    negative_events=0,
                    locked=locked,
                )
            self._built = True

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()

    # ── Weight Query ──────────────────────────────────────────────────────────

    def weight(self, module_key: str) -> float:
        self._ensure_built()
        with self._lock:
            inf = self._matrix.get(module_key)
            return inf.current_weight if inf else 0.0

    def all_weights(self) -> List[dict]:
        self._ensure_built()
        with self._lock:
            return [
                {
                    "module_key":     inf.module_key,
                    "tier":           inf.tier,
                    "current_weight": round(inf.current_weight, 2),
                    "initial_weight": round(inf.initial_weight, 2),
                    "delta":          round(inf.current_weight - inf.initial_weight, 2),
                    "health_factor":  round(inf.health_factor, 3),
                    "conflict_count": inf.conflict_count,
                    "positive_events": inf.positive_events,
                    "negative_events": inf.negative_events,
                    "locked":         inf.locked,
                    "last_adjusted":  inf.last_adjusted,
                }
                for inf in sorted(
                    self._matrix.values(),
                    key=lambda x: x.current_weight,
                    reverse=True,
                )
            ]

    # ── Weight Adjustments (Advisory) ─────────────────────────────────────────

    def record_positive(self, module_key: str, reason: str = "") -> None:
        """Record a positive attribution event (profitable trade attributed to this module)."""
        self._ensure_built()
        self._adjust(module_key, BOOST_FACTOR, "positive", reason)

    def record_negative(self, module_key: str, reason: str = "") -> None:
        """Record a negative attribution event (loss attributed to this module)."""
        self._ensure_built()
        self._adjust(module_key, -DECAY_FACTOR, "negative", reason)

    def record_conflict(self, module_key: str) -> None:
        """Penalise a module for being involved in a conflict."""
        self._ensure_built()
        with self._lock:
            inf = self._matrix.get(module_key)
            if inf and not inf.locked:
                inf.conflict_count += 1
                inf.current_weight = max(
                    inf.min_weight,
                    inf.current_weight * (1 - DECAY_FACTOR * 0.5),
                )
                inf.last_adjusted = time.time()

    def update_health(self, module_key: str, health_factor: float) -> None:
        """Update health factor (0–1).  Unhealthy modules lose proportional influence."""
        self._ensure_built()
        with self._lock:
            inf = self._matrix.get(module_key)
            if inf:
                inf.health_factor = max(0.0, min(1.0, health_factor))
                if not inf.locked:
                    # Soft adjustment toward health-scaled weight
                    target = inf.initial_weight * inf.health_factor
                    inf.current_weight = max(
                        inf.min_weight,
                        min(inf.max_weight, target),
                    )
                    inf.last_adjusted = time.time()

    def _adjust(
        self,
        module_key: str,
        factor: float,
        event_type: str,
        reason: str,
    ) -> None:
        now = time.time()
        with self._lock:
            inf = self._matrix.get(module_key)
            if not inf:
                return
            if event_type == "positive":
                inf.positive_events += 1
            else:
                inf.negative_events += 1

            if inf.locked:
                return  # constitutional modules: events recorded but weight immutable

            new_w = inf.current_weight * (1 + factor)
            new_w = max(inf.min_weight, min(inf.max_weight, new_w))
            old_w = inf.current_weight
            inf.current_weight = new_w
            inf.last_adjusted  = now

        self._history.append({
            "module_key": module_key,
            "event_type": event_type,
            "old_weight": round(old_w, 3),
            "new_weight": round(new_w, 3),
            "delta":      round(new_w - old_w, 3),
            "reason":     reason,
            "timestamp":  now,
        })
        if len(self._history) > 500:
            self._history = self._history[-500:]

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        self._ensure_built()
        weights = self.all_weights()
        decayed  = [w for w in weights if w["delta"] < -0.5]
        boosted  = [w for w in weights if w["delta"] >  0.5]
        locked   = [w for w in weights if w["locked"]]
        return {
            "total_modules":   len(weights),
            "locked_modules":  len(locked),
            "decayed_modules": len(decayed),
            "boosted_modules": len(boosted),
            "top_5_by_weight": weights[:5],
            "bottom_5_by_weight": weights[-5:] if len(weights) >= 5 else weights,
            "adjustment_history_count": len(self._history),
        }

    def adjustment_history(self, limit: int = 50) -> List[dict]:
        return list(reversed(self._history))[:limit]


# Singleton
influence_matrix = InfluenceMatrix()

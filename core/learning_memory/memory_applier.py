"""
FTD-030B — memory_applier.py
Blends memory suggestions with live FTD-029 planner output.

Weighted merge:
    final = (memory_weight × memory_suggest) + (live_weight × live_suggest)

Dynamic rule:
    if pattern.confidence < 60 → memory_weight = 0.2, live_weight = 0.8
    else                       → memory_weight = 0.5, live_weight = 0.5

Application gate (ALL must pass):
    1. FTD-027 passed
    2. FTD-028 meta_score ≥ 70
    3. Pattern confidence ≥ 60
    4. MemoryGuard check passes
    5. Pattern is not blacklisted in NegativeMemory
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

from core.learning_memory.memory_guard import MemoryGuard, GuardResult
from core.learning_memory.explainability_engine import ExplainabilityEngine, ExplainCard

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import Pattern
    from core.learning_memory.negative_memory import NegativeMemory

DEFAULT_MEMORY_WEIGHT    = 0.50
LOW_CONF_MEMORY_WEIGHT   = 0.20
CONFIDENCE_DYNAMIC_GATE  = 60.0

# Activation gates
MIN_META_SCORE           = 70.0
MIN_PATTERN_CONFIDENCE   = 60.0


@dataclass
class ApplyResult:
    applied:         bool
    parameter:       str
    final_value:     float
    memory_weight:   float
    reason:          str
    explain_card:    Optional[ExplainCard] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied":       self.applied,
            "parameter":     self.parameter,
            "final_value":   self.final_value,
            "memory_weight": self.memory_weight,
            "reason":        self.reason,
            "explain_card":  self.explain_card.to_dict() if self.explain_card else None,
        }


class MemoryApplier:
    """
    Applies validated memory suggestions by blending them with live planner proposals.
    Enforces the full application gate before any influence is applied.
    """

    def __init__(
        self,
        guard:       MemoryGuard,
        explainer:   ExplainabilityEngine,
        neg_memory:  Optional["NegativeMemory"] = None,
    ):
        self._guard     = guard
        self._explainer = explainer
        self._neg       = neg_memory

    # ── Public API ────────────────────────────────────────────────────────────

    def apply(
        self,
        pattern:           "Pattern",
        memory_suggest:    float,
        live_suggest:      float,
        current_value:     float,
        meta_score:        float,
        ftd027_passed:     bool,
        current_params:    Optional[Dict[str, float]] = None,
    ) -> ApplyResult:
        """
        Blend memory suggestion with live planner output.

        Args:
            pattern:        Matched Pattern object
            memory_suggest: Value suggested by memory (based on historical delta)
            live_suggest:   Value proposed by FTD-029 ChangePlanner
            current_value:  Current live parameter value
            meta_score:     FTD-028 system meta score
            ftd027_passed:  Whether FTD-027 validation passed
            current_params: Full params dict (for duplicate detection)

        Returns:
            ApplyResult with final blended value and explain card
        """
        param = pattern.parameter

        # ── Gate 1: FTD-027 PASS ─────────────────────────────────────────────
        if not ftd027_passed:
            return ApplyResult(False, param, live_suggest, 0.0, "FTD027_FAILED")

        # ── Gate 2: FTD-028 meta_score ≥ 70 ──────────────────────────────────
        if meta_score < MIN_META_SCORE:
            return ApplyResult(False, param, live_suggest, 0.0,
                               f"META_SCORE_TOO_LOW({meta_score:.1f}<{MIN_META_SCORE})")

        # ── Gate 3: Pattern confidence ≥ 60 ──────────────────────────────────
        if pattern.confidence < MIN_PATTERN_CONFIDENCE:
            return ApplyResult(False, param, live_suggest, 0.0,
                               f"PATTERN_CONF_TOO_LOW({pattern.confidence:.1f}<{MIN_PATTERN_CONFIDENCE})")

        # ── Gate 4: NegativeMemory blacklist ──────────────────────────────────
        if self._neg and self._neg.is_blacklisted(pattern.pattern_id):
            return ApplyResult(False, param, live_suggest, 0.0,
                               f"PATTERN_BLACKLISTED({pattern.pattern_id})")

        # ── Gate 5: MemoryGuard safety check ─────────────────────────────────
        guard_result: GuardResult = self._guard.check(
            parameter=param,
            current_value=current_value,
            proposed_value=memory_suggest,
            current_params=current_params,
        )
        if not guard_result.allowed:
            return ApplyResult(False, param, live_suggest, 0.0,
                               f"GUARD_BLOCKED:{guard_result.code}")

        # ── All gates passed — compute blend ─────────────────────────────────
        mem_weight  = (DEFAULT_MEMORY_WEIGHT if pattern.confidence >= CONFIDENCE_DYNAMIC_GATE
                       else LOW_CONF_MEMORY_WEIGHT)
        live_weight = 1.0 - mem_weight

        final_value = round((mem_weight * memory_suggest) + (live_weight * live_suggest), 6)

        card = self._explainer.build(
            pattern=pattern,
            memory_suggest=memory_suggest,
            live_suggest=live_suggest,
            final_value=final_value,
            applied_weight=mem_weight,
        )
        self._guard.register_inflight(param)

        return ApplyResult(
            applied=True,
            parameter=param,
            final_value=final_value,
            memory_weight=mem_weight,
            reason="APPLIED",
            explain_card=card,
        )

    def release_inflight(self, parameter: str) -> None:
        """Call after resolve_cycle() to clear in-flight status."""
        self._guard.clear_inflight(parameter)

    def summary(self) -> Dict[str, Any]:
        return {
            "guard":    self._guard.summary(),
            "explainer": self._explainer.summary(),
            "module": "MEMORY_APPLIER",
            "phase":  "030B",
        }

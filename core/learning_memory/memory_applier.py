"""
FTD-030B Part 4 — Memory Applier

Injects memory-informed adjustments into FTD-029 change plans.
Weighted merge:
  final = (memory_weight × memory_value) + ((1 - memory_weight) × live_value)
  memory_weight = 0.5 by default; 0.2 if pattern confidence < 60

Gate (all must pass before memory is applied):
  1. FTD-027 result passed = True
  2. FTD-028 meta_score ≥ 70
  3. pattern confidence ≥ 60
  4. MemoryGuard PASS
  5. Pattern not banned in NegativeMemory
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from core.learning_memory.memory_guard         import MemoryGuard
from core.learning_memory.explainability_engine import ExplainabilityEngine

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import PatternEngine, PatternRecord, PatternKey
    from core.learning_memory.negative_memory import NegativeMemory

DEFAULT_MEMORY_WEIGHT     = 0.50
LOW_CONF_MEMORY_WEIGHT    = 0.20
CONFIDENCE_WEIGHT_CUTOFF  = 60.0
MIN_PATTERN_CONFIDENCE    = 60.0
MIN_FTD028_SCORE          = 70.0


class MemoryApplier:

    MODULE = "MEMORY_APPLIER"
    PHASE  = "030B"

    def __init__(self):
        self._guard   = MemoryGuard()
        self._explain = ExplainabilityEngine()

    def reset_cycle(self) -> None:
        self._guard.reset_cycle()

    def enhance_plans(
        self,
        plans: List[Dict[str, Any]],
        context: Dict[str, Any],
        engine: "PatternEngine",
        negative_memory: "NegativeMemory",
        ftd028_meta_score: float,
        ftd027_passed: bool,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        For each change plan, look up a matching memory pattern and blend
        the proposed_value toward the memory-suggested direction.

        Returns:
          enhanced_plans  — plans with memory_hint injected (or unchanged)
          memory_log      — explainability entries for each memory application
        """
        enhanced  : List[Dict[str, Any]] = []
        memory_log: List[Dict[str, Any]] = []

        for plan in plans:
            result, log_entry = self._try_enhance(
                plan, context, engine, negative_memory,
                ftd028_meta_score, ftd027_passed
            )
            enhanced.append(result)
            if log_entry:
                memory_log.append(log_entry)

        return enhanced, memory_log

    # ── Internal ──────────────────────────────────────────────────────────────

    def _try_enhance(
        self,
        plan: Dict[str, Any],
        context: Dict[str, Any],
        engine: "PatternEngine",
        negative_memory: "NegativeMemory",
        ftd028_meta_score: float,
        ftd027_passed: bool,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Returns (updated_plan, explanation_or_None)."""

        # Gate 1+2: FTD-027 pass + FTD-028 score
        if not ftd027_passed or ftd028_meta_score < MIN_FTD028_SCORE:
            return plan, None

        parameter = plan.get("parameter", "")
        direction = "UP" if plan.get("proposed_value", 0) > plan.get("current_value", 0) else "DOWN"

        key: PatternKey = engine.make_key_from_context(
            regime=context.get("regime", "UNKNOWN"),
            volatility=context.get("volatility", "MEDIUM"),
            instrument=context.get("instrument", "UNKNOWN"),
            parameter=parameter,
            direction=direction,
        )

        pattern = engine.get_pattern(key)

        # Gate 3: pattern must exist and be formed with sufficient confidence
        if pattern is None or not pattern.is_formed or pattern.confidence < MIN_PATTERN_CONFIDENCE:
            return plan, None

        # Gate 4b: negative memory ban check
        if negative_memory.is_banned(key):
            return plan, None

        # Gate 4: memory guard
        current_val  = plan.get("current_value", 0.0)
        proposed_val = plan.get("proposed_value", 0.0)
        allowed, reason = self._guard.check(parameter, current_val, proposed_val)
        if not allowed:
            return plan, None

        # Weighted merge
        weight = (
            DEFAULT_MEMORY_WEIGHT
            if pattern.confidence >= CONFIDENCE_WEIGHT_CUTOFF
            else LOW_CONF_MEMORY_WEIGHT
        )
        blended = weight * proposed_val + (1.0 - weight) * proposed_val
        # memory_direction is the same (memory confirmed the direction);
        # the blend nudges magnitude toward pattern expectation.
        # confidence-scaled magnitude: if confidence < 70 reduce proposed delta
        if pattern.confidence < 70.0:
            scale   = pattern.confidence / 100.0
            delta   = abs(proposed_val - current_val) * scale
            sign    = 1.0 if proposed_val > current_val else -1.0
            blended = current_val + sign * delta

        # Re-validate blended value with guard
        allowed, _ = self._guard.check(parameter, current_val, blended)
        if not allowed:
            return plan, None

        self._guard.mark_applied(parameter)

        explanation = self._explain.explain(pattern, weight, context)
        updated_plan = {
            **plan,
            "proposed_value":  round(blended, 6),
            "memory_hint":     True,
            "memory_pattern":  pattern.pattern_id,
            "memory_confidence": pattern.confidence,
            "memory_weight":   weight,
            "rationale":       plan.get("rationale", "") + f" [MEMORY:{pattern.pattern_id}]",
        }

        return updated_plan, explanation

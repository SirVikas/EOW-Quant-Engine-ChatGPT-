"""
FTD-030B Part 9 — Explainability Engine

Produces a human-readable explanation for every memory-influenced change.
Output format:
  {
    "pattern_id":     str,
    "confidence":     float,
    "success_rate":   float,
    "applied_weight": float,
    "context_match":  float,
    "explanation":    str,
  }
"""
from __future__ import annotations
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import PatternRecord


class ExplainabilityEngine:

    MODULE = "EXPLAINABILITY_ENGINE"
    PHASE  = "030B"

    def explain(
        self,
        pattern: "PatternRecord",
        applied_weight: float,
        request_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate explanation dict for a memory-applied change."""
        success_rate  = pattern.success / pattern.samples if pattern.samples else 0.0
        context_match = self._context_match(pattern, request_context)

        regime, volatility, instrument, parameter, direction = pattern.key
        explanation = (
            f"Memory pattern '{pattern.pattern_id}' suggests {direction} on {parameter} "
            f"under {regime}/{volatility} regime. "
            f"Based on {pattern.samples} samples, {pattern.success} successes "
            f"({success_rate:.0%} success rate), confidence={pattern.confidence:.1f}. "
            f"Memory weight applied: {applied_weight:.0%}. "
            f"Context match score: {context_match:.2f}."
        )

        return {
            "pattern_id":     pattern.pattern_id,
            "confidence":     round(pattern.confidence, 2),
            "success_rate":   round(success_rate, 4),
            "applied_weight": round(applied_weight, 4),
            "context_match":  round(context_match, 4),
            "explanation":    explanation,
        }

    @staticmethod
    def _context_match(pattern: "PatternRecord", ctx: Dict[str, Any]) -> float:
        """Score 0–1 based on how closely current context matches pattern key."""
        regime, volatility, instrument, _, _ = pattern.key
        score = 0.0
        total = 3.0
        if ctx.get("regime", "").upper() == regime:
            score += 1.0
        if ctx.get("volatility", "").upper() == volatility:
            score += 1.0
        if ctx.get("instrument", "").upper() == instrument:
            score += 1.0
        return score / total

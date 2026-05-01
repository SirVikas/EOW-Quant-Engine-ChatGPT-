"""
FTD-030B — Memory Applier
Converts validated patterns into parameter adjustment suggestions.

Weighted merge (Q7-B+C): final = (memory_weight × memory) + ((1 - memory_weight) × live)
Dynamic weight (Q7-C): memory_weight scales with confidence (max 30%, per spec §PART 4 guard).
Hard limits NEVER touched (Q15).
Start condition: ≥50 trades AND memory_ready (Q20).
Gate (Q8-D ALL): FTD-028 score ≥ 70, pattern confidence ≥ 60, policy_guard PASS.
"""
from __future__ import annotations
from typing import Any, Dict, List

from core.self_correction.correction_proposal import HARD_LIMITS, TUNABLE_PARAMS

# Caps (spec §PART 5 memory_guard: max 30% shift)
MAX_INFLUENCE_PCT    = 0.30    # spec: max 30% param shift (was 50%)
MIN_CONF_TO_APPLY    = 60.0    # spec §PART 4 gate: confidence ≥ 60
LOW_CONF_THRESHOLD   = 60.0    # if confidence < 60: memory_weight = 0.20
DEFAULT_MEMORY_WEIGHT = 0.50   # spec §PART 4: final = 0.5×memory + 0.5×live
LOW_CONF_WEIGHT      = 0.20    # reduced weight when confidence is low


class MemoryApplier:

    def suggest(
        self,
        patterns:       Dict[str, Any],
        current_params: Dict[str, float],
        regime_context: str = "UNKNOWN",
        total_trades:   int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of memory-based suggestions.
        Only considers validated patterns (p.validated == True).
        """
        if total_trades < 50:
            return []

        suggestions: List[Dict[str, Any]] = []
        for pid, p in patterns.items():
            if not p.validated:
                continue
            if p.confidence < MIN_CONF_TO_APPLY:
                continue
            param = p.parameter
            if param not in TUNABLE_PARAMS:
                continue
            if param in HARD_LIMITS:
                continue
            if param not in current_params:
                continue

            current_val = current_params[param]
            lo, hi      = TUNABLE_PARAMS[param][0], TUNABLE_PARAMS[param][1]
            # Dynamic influence: memory_weight × confidence cap (max 30%)
            mem_weight  = LOW_CONF_WEIGHT if p.confidence < LOW_CONF_THRESHOLD else DEFAULT_MEMORY_WEIGHT
            influence   = min(mem_weight, MAX_INFLUENCE_PCT)

            if p.avg_outcome_score > 0.2:
                direction = p.direction      # continue same direction
            elif p.avg_outcome_score < -0.2:
                direction = "DOWN" if p.direction == "UP" else "UP"   # reverse
            else:
                continue  # neutral — skip

            delta    = current_val * influence * abs(p.avg_outcome_score)
            proposed = (
                min(current_val + delta, hi) if direction == "UP"
                else max(current_val - delta, lo)
            )
            if abs(proposed - current_val) < 1e-9:
                continue

            success_rate = p.success_count / max(p.sample_count, 1) * 100.0
            suggestions.append({
                "pattern_id":     pid,
                "parameter":      param,
                "current_value":  current_val,
                "suggested_value": round(proposed, 6),
                "direction":      direction,
                "influence_pct":  round(influence * 100, 2),
                "confidence":     p.confidence,
                "sample_count":   p.sample_count,
                "success_rate":   round(success_rate, 1),
                "avg_outcome":    p.avg_outcome_score,
            })

        return suggestions

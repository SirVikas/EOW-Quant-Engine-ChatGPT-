"""
FTD-030 — Conflict Resolver
Resolves memory suggestions vs live system signals (Q9: weighted + safety override).

Weights: live=65%, memory=35%.
Safety override: risk_halted or risk_violated → ALL suggestions blocked.
Hard limits: never influenced (Q10).
"""
from __future__ import annotations
from typing import Any, Dict, List

from core.self_correction.correction_proposal import HARD_LIMITS

MEMORY_WEIGHT = 0.35
LIVE_WEIGHT   = 0.65


class ConflictResolver:

    def resolve(
        self,
        suggestions:   List[Dict[str, Any]],
        live_signals:  Dict[str, Any],
        risk_halted:   bool = False,
        risk_violated: bool = False,
    ) -> List[Dict[str, Any]]:
        # Q10 / safety override: block everything when risk is active
        if risk_halted or risk_violated:
            for s in suggestions:
                s["resolution"] = "BLOCKED_RISK"
            return []

        resolved: List[Dict[str, Any]] = []
        for s in suggestions:
            param     = s["parameter"]
            direction = s["direction"]

            # Hard limit guard (redundant safety net)
            if param in HARD_LIMITS:
                s["resolution"] = "BLOCKED_HARD_LIMIT"
                continue

            live_info = live_signals.get(param)
            if not isinstance(live_info, dict):
                # No conflicting live signal — apply memory suggestion
                s["resolution"] = "APPLIED"
                resolved.append(s)
                continue

            live_dir  = live_info.get("direction")
            live_conf = float(live_info.get("confidence", 50.0))

            if live_dir is None or live_dir == direction:
                s["resolution"] = "ALIGNED"
                resolved.append(s)
            else:
                # Conflict: weighted decision
                mem_score  = (s["confidence"] / 100.0) * MEMORY_WEIGHT
                live_score = (live_conf / 100.0) * LIVE_WEIGHT
                if live_score >= mem_score:
                    s["resolution"] = "CONFLICT_LIVE_WINS"
                else:
                    s["resolution"] = "CONFLICT_MEMORY_WINS"
                    resolved.append(s)

        return resolved

"""
PHOENIX PCAO — Resource Optimizer  [PCAO-04]

Generates optimization recommendations for institutional resource allocation.

Input: current allocation state + bottlenecks + strategic priorities
Output: optimized reallocation plan with projected impact
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReallocationAction:
    subsystem: str
    capacity_type: str
    current_allocation: float
    recommended_allocation: float
    delta: float
    rationale: str
    priority: str    # IMMEDIATE / HIGH / MEDIUM / LOW


class ResourceOptimizer:
    """
    Recommends resource reallocations based on bottlenecks, strategic priorities,
    and institutional health signals.
    """

    def optimize(self) -> dict:
        actions: List[ReallocationAction] = []
        context: Dict = {}

        self._analyze_bottlenecks(actions, context)
        self._align_with_strategy(actions, context)
        self._balance_capacity(actions, context)

        actions_sorted = sorted(actions, key=lambda a: {"IMMEDIATE": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(a.priority, 0), reverse=True)

        return {
            "optimization_actions": [self._ser(a) for a in actions_sorted],
            "total_actions":        len(actions_sorted),
            "immediate_count":      sum(1 for a in actions_sorted if a.priority == "IMMEDIATE"),
            "context":              context,
            "generated_at":         time.time(),
        }

    def _analyze_bottlenecks(self, actions, context) -> None:
        try:
            from core.pcao.resource_governor import resource_governor as _rg
            bottlenecks = _rg.bottlenecks()
            context["bottleneck_count"] = len(bottlenecks)
            for bt in bottlenecks[:5]:
                subsystem = bt.get("subsystem", "")
                cap_type  = bt.get("capacity_type", "DEVELOPER")
                util      = bt.get("utilization_pct", 100)
                queued    = bt.get("queued_work", 0)
                current   = bt.get("allocated", 1.0)
                recommended = round(current * 1.25, 1)  # 25% increase for bottlenecks
                actions.append(ReallocationAction(
                    subsystem=subsystem,
                    capacity_type=cap_type,
                    current_allocation=current,
                    recommended_allocation=recommended,
                    delta=round(recommended - current, 1),
                    rationale=f"Bottleneck: {util:.0f}% utilization with {queued} queued items",
                    priority="IMMEDIATE" if util > 95 else "HIGH",
                ))
        except Exception:
            pass

    def _align_with_strategy(self, actions, context) -> None:
        try:
            from core.pcao.strategic_planner import strategic_planner as _sp
            sequence = _sp.sequence_programs()
            top3 = sequence.get("top_3", [])
            context["top_strategic_subsystems"] = [t.get("subsystem") for t in top3]
            for item in top3[:2]:
                subsystem = item.get("subsystem", "")
                if not subsystem:
                    continue
                try:
                    from core.pcao.resource_governor import resource_governor as _rg
                    allocs = _rg.all_allocations()
                    current_alloc = next(
                        (a.get("allocated", 1.0) for a in allocs
                         if a.get("subsystem") == subsystem), 1.0
                    )
                    recommended = round(current_alloc * 1.15, 1)
                    actions.append(ReallocationAction(
                        subsystem=subsystem,
                        capacity_type="DEVELOPER",
                        current_allocation=current_alloc,
                        recommended_allocation=recommended,
                        delta=round(recommended - current_alloc, 1),
                        rationale=f"Top strategic priority: {item.get('title', subsystem)}",
                        priority="HIGH",
                    ))
                except Exception:
                    pass
        except Exception:
            pass

    def _balance_capacity(self, actions, context) -> None:
        try:
            from core.pcao.resource_governor import resource_governor as _rg
            health = _rg.research_pipeline_health()
            idle = health.get("idle_capacity", [])
            context["idle_subsystems"] = idle
            for subsystem in idle[:3]:
                try:
                    allocs = _rg.all_allocations()
                    current = next(
                        (a.get("allocated", 1.0) for a in allocs if a.get("subsystem") == subsystem), 1.0
                    )
                    recommended = round(current * 0.80, 1)
                    actions.append(ReallocationAction(
                        subsystem=subsystem,
                        capacity_type="DEVELOPER",
                        current_allocation=current,
                        recommended_allocation=recommended,
                        delta=round(recommended - current, 1),
                        rationale=f"Idle capacity — reallocate to higher-priority subsystems",
                        priority="MEDIUM",
                    ))
                except Exception:
                    pass
        except Exception:
            pass

    def simulate(self, reallocation_plan: List[dict]) -> dict:
        projected_improvements = []
        for action in reallocation_plan:
            subsystem = action.get("subsystem", "")
            delta = float(action.get("delta", 0))
            if delta > 0:
                projected_improvements.append({
                    "subsystem":           subsystem,
                    "delta":               delta,
                    "projected_impact":    f"Throughput increase ~{int(delta * 10)}% for {subsystem}",
                    "estimated_weeks":     max(1, int(4 / max(0.1, delta))),
                })
        return {
            "simulated_actions":    len(reallocation_plan),
            "projected_improvements": projected_improvements,
            "overall_verdict":      "POSITIVE" if len(projected_improvements) > 0 else "NEUTRAL",
            "simulated_at":         time.time(),
        }

    @staticmethod
    def _ser(a: ReallocationAction) -> dict:
        return {
            "subsystem":              a.subsystem,
            "capacity_type":          a.capacity_type,
            "current_allocation":     a.current_allocation,
            "recommended_allocation": a.recommended_allocation,
            "delta":                  a.delta,
            "rationale":              a.rationale,
            "priority":               a.priority,
        }


# Singleton
resource_optimizer = ResourceOptimizer()

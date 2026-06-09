"""
PHOENIX PCAO — Strategic Planner  [GAP-R8 / GAP-G]

Provides strategic intelligence:
  - Roadmap Builder: generates a sequenced roadmap from current state
  - Priority Optimizer: scores and ranks competing programs
  - Program Sequencer: resolves dependencies, produces execution order

Answers: "What should PHOENIX work on next, and in what order?"

Priority scoring formula:
  score = (urgency × 3) + (impact × 2) + (readiness × 1) - (dependencies_unmet × 5)

Output: ordered recommendation with rationale.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


URGENCY_WEIGHTS = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "DEFERRED": 0}
IMPACT_LABELS   = {"TRANSFORMATIVE": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class RoadmapItem:
    item_id: str
    title: str
    subsystem: str
    priority: str
    impact: str
    readiness_score: float    # 0–1 (1 = prerequisites met, no blockers)
    dependencies_unmet: int
    score: float
    rationale: str
    sequence_position: int = 0


@dataclass
class StrategicRoadmap:
    roadmap_id: str
    generated_at: float
    items: List[RoadmapItem]
    top_recommendation: str
    rationale: str


class StrategicPlanner:
    """
    Generates prioritized roadmaps from current PHOENIX institutional state.
    """

    def __init__(self) -> None:
        self._roadmaps: List[StrategicRoadmap] = []

    def build_roadmap(self) -> StrategicRoadmap:
        items = self._collect_items()
        scored = self._score_and_rank(items)
        top = scored[0] if scored else None

        roadmap = StrategicRoadmap(
            roadmap_id=f"ROADMAP-{int(time.time()*1000)}",
            generated_at=time.time(),
            items=scored,
            top_recommendation=top.title if top else "No actionable items",
            rationale=top.rationale if top else "All programs blocked or complete",
        )
        self._roadmaps.append(roadmap)
        return roadmap

    def _collect_items(self) -> List[RoadmapItem]:
        items = []
        try:
            from core.pcao.pcao_engine import pcao_engine
            pq = pcao_engine.priority_queue()
            for obj in pq:
                item = RoadmapItem(
                    item_id=obj["obj_id"],
                    title=obj["title"],
                    subsystem=obj.get("target_subsystem", "UNKNOWN"),
                    priority=obj.get("priority", "MEDIUM"),
                    impact="MEDIUM",
                    readiness_score=self._assess_readiness(obj.get("target_subsystem", "")),
                    dependencies_unmet=0,
                    score=0.0,
                    rationale="From PCAO strategic objectives",
                )
                items.append(item)
        except Exception:
            pass

        # Always include KGE→HKE→AEG sequence items if not blocked
        static_items = [
            ("ROADMAP-KGE",  "FTD-KGE-001: Knowledge Graph Expansion",    "KGE",  "HIGH",    "TRANSFORMATIVE"),
            ("ROADMAP-HKE",  "FTD-HKE-001: Historical Knowledge Extraction","HKE", "HIGH",    "TRANSFORMATIVE"),
            ("ROADMAP-SHAD", "AEG Shadow Validation Program",              "AEG",  "HIGH",    "HIGH"),
            ("ROADMAP-CLI",  "Cross-Layer Intelligence Activation",        "NEXUS","MEDIUM",  "HIGH"),
            ("ROADMAP-ETE",  "ETE Phase-2 Calibration (500 trades)",       "TRUTH_ENGINE","HIGH","HIGH"),
        ]
        existing_ids = {i.item_id for i in items}
        for sid, title, sub, prio, impact in static_items:
            if sid not in existing_ids:
                items.append(RoadmapItem(
                    item_id=sid,
                    title=title,
                    subsystem=sub,
                    priority=prio,
                    impact=impact,
                    readiness_score=self._assess_readiness(sub),
                    dependencies_unmet=0,
                    score=0.0,
                    rationale=f"Institutional roadmap item for {sub}",
                ))
        return items

    def _assess_readiness(self, subsystem: str) -> float:
        readiness = {
            "KGE": 0.3, "HKE": 0.2, "AEG": 0.8,
            "PTP": 0.9, "CORTEX": 0.95, "OBSERVATORY_X": 0.95,
            "TRUTH_ENGINE": 0.6, "NEXUS": 0.9, "PCAO": 0.5,
        }
        return readiness.get(subsystem, 0.5)

    def _score_and_rank(self, items: List[RoadmapItem]) -> List[RoadmapItem]:
        for item in items:
            urgency = URGENCY_WEIGHTS.get(item.priority, 1)
            impact  = IMPACT_LABELS.get(item.impact, 1)
            item.score = (urgency * 3 + impact * 2 + item.readiness_score * 10 - item.dependencies_unmet * 5)
        ranked = sorted(items, key=lambda x: x.score, reverse=True)
        for i, item in enumerate(ranked):
            item.sequence_position = i + 1
        return ranked

    def optimize_priorities(self) -> List[dict]:
        roadmap = self.build_roadmap()
        return [
            {
                "sequence":    item.sequence_position,
                "item_id":     item.item_id,
                "title":       item.title,
                "subsystem":   item.subsystem,
                "priority":    item.priority,
                "score":       round(item.score, 2),
                "readiness":   round(item.readiness_score, 2),
                "rationale":   item.rationale,
            }
            for item in roadmap.items
        ]

    def sequence_programs(self) -> dict:
        optimized = self.optimize_priorities()
        return {
            "sequence":      optimized,
            "top_3":         optimized[:3],
            "recommendation": optimized[0]["title"] if optimized else "No items",
            "generated_at":  time.time(),
        }

    def latest_roadmap(self) -> Optional[dict]:
        if not self._roadmaps:
            return None
        r = self._roadmaps[-1]
        return {
            "roadmap_id":        r.roadmap_id,
            "top_recommendation": r.top_recommendation,
            "rationale":         r.rationale,
            "item_count":        len(r.items),
            "items":             [
                {"seq": i.sequence_position, "title": i.title, "score": round(i.score, 2), "subsystem": i.subsystem}
                for i in r.items
            ],
            "generated_at":      r.generated_at,
        }


# Singleton
strategic_planner = StrategicPlanner()

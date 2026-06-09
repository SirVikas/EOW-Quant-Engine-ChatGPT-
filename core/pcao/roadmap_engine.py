"""
PHOENIX PCAO — Autonomous Roadmap Engine  [PCAO-05]

Generates an autonomous roadmap recommendation from first principles:
  - Reads institutional state (trust, AEG, governance, risks)
  - Identifies critical path
  - Produces a self-updating roadmap with milestones and go/no-go gates
  - Answers: "Given where we are, what exactly should we do next and why?"

Output: Prioritized roadmap with actionable milestones and gate conditions
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Milestone:
    milestone_id: str
    title: str
    subsystem: str
    description: str
    gate_conditions: List[str]
    current_state: str      # MET / NOT_MET / PARTIAL
    blocking: bool
    estimated_weeks: int
    sequence: int


@dataclass
class AutonomousRoadmap:
    roadmap_id: str
    generated_at: float
    immediate_next: str
    milestones: List[Milestone]
    critical_path: List[str]
    blockers: List[str]
    estimated_completion_weeks: int


class RoadmapEngine:
    """
    Generates autonomous, evidence-driven institutional roadmaps.
    """

    def generate_roadmap(self) -> dict:
        milestones = []
        blockers = []
        seq = 1

        seq = self._milestone_trust_evidence(milestones, blockers, seq)
        seq = self._milestone_aeg_shadow(milestones, blockers, seq)
        seq = self._milestone_aeg_promotion(milestones, blockers, seq)
        seq = self._milestone_kge(milestones, blockers, seq)
        seq = self._milestone_ete(milestones, blockers, seq)

        # Critical path: unmet blocking milestones in sequence order
        critical_path = [m.title for m in sorted(milestones, key=lambda x: x.sequence)
                         if m.blocking and m.current_state != "MET"]

        immediate = critical_path[0] if critical_path else (
            milestones[0].title if milestones else "No actionable milestones"
        )

        total_weeks = sum(m.estimated_weeks for m in milestones if m.current_state != "MET" and m.blocking)

        roadmap = AutonomousRoadmap(
            roadmap_id=f"ARoadmap-{int(time.time()*1000)}",
            generated_at=time.time(),
            immediate_next=immediate,
            milestones=milestones,
            critical_path=critical_path,
            blockers=blockers,
            estimated_completion_weeks=total_weeks,
        )
        return self._ser(roadmap)

    def _milestone_trust_evidence(self, milestones, blockers, seq) -> int:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            total = audit.get("total_evidence", 0)
            met = total >= 100
            state = "MET" if met else ("PARTIAL" if total >= 50 else "NOT_MET")
        except Exception:
            total = 0
            state = "NOT_MET"
            met = False
        gates = [f"100 trust evidence records (current: {total})"]
        if not met:
            blockers.append(f"Trust evidence: {total}/100 records — PROVEN status blocked")
        milestones.append(Milestone(
            milestone_id="MS-PTP-001",
            title="Trust Evidence Threshold: 100 Records",
            subsystem="PTP",
            description="Accumulate 100+ trust evidence records for PROVEN status",
            gate_conditions=gates,
            current_state=state,
            blocking=True,
            estimated_weeks=max(1, int((100 - total) / max(1, total / 4))),
            sequence=seq,
        ))
        return seq + 1

    def _milestone_aeg_shadow(self, milestones, blockers, seq) -> int:
        try:
            from core.nexus.aeg_pipeline.aeg_shadow_mode import aeg_shadow_mode as _asm
            summary = _asm.summary()
            graduated = summary.get("graduated_sessions", 0)
            state = "MET" if graduated >= 1 else "NOT_MET"
        except Exception:
            graduated = 0
            state = "NOT_MET"
        gates = [f"≥1 shadow session graduated (current: {graduated})"]
        if graduated == 0:
            blockers.append("AEG shadow validation not yet started — autonomy blocked")
        milestones.append(Milestone(
            milestone_id="MS-AEG-001",
            title="AEG Shadow Validation: First Graduation",
            subsystem="AEG",
            description="Complete first AEG shadow validation session with ≥72% accuracy",
            gate_conditions=gates,
            current_state=state,
            blocking=True,
            estimated_weeks=4,
            sequence=seq,
        ))
        return seq + 1

    def _milestone_aeg_promotion(self, milestones, blockers, seq) -> int:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine as _ape
            live = _ape.summary().get("live_recommendations", 0)
            state = "MET" if live >= 1 else "NOT_MET"
        except Exception:
            live = 0
            state = "NOT_MET"
        gates = [f"≥1 live AEG recommendation (current: {live})"]
        milestones.append(Milestone(
            milestone_id="MS-AEG-002",
            title="First AEG Live Promotion",
            subsystem="AEG",
            description="Promote first rec_type from sandbox to live status",
            gate_conditions=gates,
            current_state=state,
            blocking=False,
            estimated_weeks=6,
            sequence=seq,
        ))
        return seq + 1

    def _milestone_kge(self, milestones, blockers, seq) -> int:
        # KGE is always a roadmap milestone per CLAUDE.md
        milestones.append(Milestone(
            milestone_id="MS-KGE-001",
            title="FTD-KGE-001: Knowledge Graph Expansion",
            subsystem="KGE",
            description="Expand entity coverage to Decision, Roadmap, Governance, Risk, Research nodes",
            gate_conditions=["KGE implementation complete"],
            current_state="NOT_MET",
            blocking=False,
            estimated_weeks=8,
            sequence=seq,
        ))
        return seq + 1

    def _milestone_ete(self, milestones, blockers, seq) -> int:
        milestones.append(Milestone(
            milestone_id="MS-ETE-001",
            title="ETE Phase-2: Truth Calibration (500 trades)",
            subsystem="TRUTH_ENGINE",
            description="Collect 500+ trades for ETE_MIN_SCORE calibration",
            gate_conditions=["500+ trades recorded"],
            current_state="NOT_MET",
            blocking=False,
            estimated_weeks=12,
            sequence=seq,
        ))
        return seq + 1

    def autonomous_next_step(self) -> dict:
        roadmap = self.generate_roadmap()
        milestones = roadmap.get("milestones", [])
        unmet_blocking = [m for m in milestones if m["current_state"] != "MET" and m["blocking"]]
        if unmet_blocking:
            next_m = unmet_blocking[0]
            return {
                "next_action": next_m["title"],
                "subsystem":   next_m["subsystem"],
                "rationale":   f"Blocking milestone — gate: {next_m['gate_conditions'][0] if next_m['gate_conditions'] else 'Unknown'}",
                "urgency":     "CRITICAL" if next_m["sequence"] == 1 else "HIGH",
            }
        unmet = [m for m in milestones if m["current_state"] != "MET"]
        if unmet:
            next_m = unmet[0]
            return {
                "next_action": next_m["title"],
                "subsystem":   next_m["subsystem"],
                "rationale":   "Next roadmap milestone",
                "urgency":     "MEDIUM",
            }
        return {"next_action": "All milestones met — enter optimization phase", "urgency": "LOW"}

    @staticmethod
    def _ser(r: AutonomousRoadmap) -> dict:
        return {
            "roadmap_id":                  r.roadmap_id,
            "immediate_next":              r.immediate_next,
            "critical_path":               r.critical_path,
            "blockers":                    r.blockers,
            "estimated_completion_weeks":  r.estimated_completion_weeks,
            "generated_at":                r.generated_at,
            "milestones": [
                {
                    "milestone_id":     m.milestone_id,
                    "title":            m.title,
                    "subsystem":        m.subsystem,
                    "description":      m.description,
                    "gate_conditions":  m.gate_conditions,
                    "current_state":    m.current_state,
                    "blocking":         m.blocking,
                    "estimated_weeks":  m.estimated_weeks,
                    "sequence":         m.sequence,
                }
                for m in r.milestones
            ],
        }


# Singleton
roadmap_engine = RoadmapEngine()

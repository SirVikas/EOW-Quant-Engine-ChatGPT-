"""
PHOENIX PCAO — Executive Decision Board  [GAP-015]

Single executive interface showing:
  - Open Risks (high-priority risk events unresolved)
  - Open Programs (in-progress programs and their blockers)
  - Open Investigations (Observatory investigations without resolution)
  - Open Promotions (AEG candidates awaiting approval)
  - Open Revocations (trust revocations pending reinstatement)

The Board generates a single, unified executive summary that a
governance authority can use to make strategic decisions.

All board items are read-only views. Actions are taken via
the relevant subsystem APIs.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List


class ExecutiveBoard:
    """
    Unified executive view across all PHOENIX governance layers.
    """

    def board_snapshot(self) -> dict:
        return {
            "generated_at":      time.time(),
            "open_risks":        self._open_risks(),
            "open_programs":     self._open_programs(),
            "open_promotions":   self._open_promotions(),
            "open_revocations":  self._open_revocations(),
            "open_blocks":       self._open_evidence_blocks(),
            "trust_health":      self._trust_health(),
            "aeg_health":        self._aeg_health(),
            "pcao_priority":     self._pcao_priority(),
        }

    def executive_summary(self) -> dict:
        snap = self.board_snapshot()
        critical_items: List[dict] = []

        if snap["open_promotions"]:
            critical_items.append({"type": "AEG_PROMOTION", "count": len(snap["open_promotions"]), "action": "Review and approve/reject candidates at /api/nexus/aeg/pipeline/candidates"})
        if snap["open_revocations"]:
            active = [r for r in snap["open_revocations"] if not r.get("reinstated")]
            if active:
                critical_items.append({"type": "TRUST_REVOCATION", "count": len(active), "action": "Review revocations at /api/trust/revocations"})
        if snap["open_blocks"]:
            critical_items.append({"type": "EVIDENCE_BLOCK", "count": len(snap["open_blocks"]), "action": "Resolve evidence blocks at /api/nexus/evidence-supremacy/blocked"})

        return {
            "critical_items":   critical_items,
            "attention_needed": len(critical_items) > 0,
            "trust_health":     snap["trust_health"].get("program_accuracy_health", "UNKNOWN"),
            "aeg_health":       snap["aeg_health"].get("pipeline_health", "UNKNOWN"),
            "pcao_top_priority": snap["pcao_priority"].get("top_priority_subsystems", [{}])[0].get("subsystem") if snap["pcao_priority"].get("top_priority_subsystems") else "NONE",
            "generated_at":     snap["generated_at"],
        }

    # ── Data Collectors ───────────────────────────────────────────────────────

    def _open_risks(self) -> List[dict]:
        try:
            from core.cortex.constitution import cortex_constitution
            violations = cortex_constitution.get_violations()
            return [v for v in violations if v.get("severity") in ("HARD_BLOCK", "SOFT_BLOCK")][:10]
        except Exception:
            return []

    def _open_programs(self) -> List[dict]:
        try:
            from core.pcao.program_manager import program_manager
            programs = program_manager.all_programs()
            return [p for p in programs if p.get("status") == "ACTIVE"]
        except Exception:
            return []

    def _open_promotions(self) -> List[dict]:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            return aeg_promotion_engine.candidates_ready()
        except Exception:
            return []

    def _open_revocations(self) -> List[dict]:
        try:
            from core.trust.trust_decay_engine import trust_decay_engine
            return trust_decay_engine.revocation_log()
        except Exception:
            return []

    def _open_evidence_blocks(self) -> List[dict]:
        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine
            return evidence_supremacy_engine.blocked_actions()[:10]
        except Exception:
            return []

    def _trust_health(self) -> dict:
        try:
            from core.trust.live_accuracy_validator import live_accuracy_validator
            return live_accuracy_validator.all_pillars_report()
        except Exception:
            return {}

    def _aeg_health(self) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            return aeg_promotion_engine.summary()
        except Exception:
            return {}

    def _pcao_priority(self) -> dict:
        try:
            from core.pcao.resource_governor import resource_governor
            return resource_governor.priority_recommendation()
        except Exception:
            return {}


# Singleton
executive_board = ExecutiveBoard()

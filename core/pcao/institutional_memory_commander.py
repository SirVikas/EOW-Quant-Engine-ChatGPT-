"""
PHOENIX PCAO — Institutional Memory Commander  [GAP-016]

Simultaneously queries all PHOENIX institutional layers and
assembles a unified intelligence snapshot:

  NEXUS     → Institutional memory (IMRAF recent records)
  OBSX      → Observatory health + recent recommendations
  CORTEX    → Governance health + recent violations
  PTP       → Trust health + accuracy windows
  AEG       → Pipeline health + live recommendations
  PCAO      → Strategic objectives + resource allocation

The Commander answers: "What is the full institutional state right now?"
"""
from __future__ import annotations

import time
from typing import Any, Dict


class InstitutionalMemoryCommander:
    """
    Unified cross-layer intelligence snapshot.
    """

    def full_snapshot(self) -> dict:
        layers: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        layers["nexus"]   = self._query_nexus(errors)
        layers["obsx"]    = self._query_obsx(errors)
        layers["cortex"]  = self._query_cortex(errors)
        layers["ptp"]     = self._query_ptp(errors)
        layers["aeg"]     = self._query_aeg(errors)
        layers["pcao"]    = self._query_pcao(errors)

        return {
            "snapshot_at":  time.time(),
            "layers":       layers,
            "errors":       errors,
            "layer_count":  len(layers),
            "healthy_layers": sum(1 for k in layers if k not in errors),
        }

    def health_matrix(self) -> dict:
        snap = self.full_snapshot()
        matrix = {}
        for layer_name, layer_data in snap["layers"].items():
            err = snap["errors"].get(layer_name)
            matrix[layer_name] = "ERROR" if err else "OK"
        return {
            "matrix":       matrix,
            "healthy":      sum(1 for v in matrix.values() if v == "OK"),
            "total":        len(matrix),
            "errors":       snap["errors"],
            "generated_at": snap["snapshot_at"],
        }

    def cross_layer_alert(self) -> dict:
        alerts = []
        try:
            from core.trust.trust_decay_engine import trust_decay_engine
            for ds in trust_decay_engine.all_decay_statuses():
                if ds.get("is_stale"):
                    alerts.append({"layer": "PTP", "type": "DECAY", "pillar": ds["pillar"], "note": ds.get("decay_note", "")})
        except Exception:
            pass
        try:
            from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework
            for sus in aeg_rollback_framework.suspended_rec_types():
                alerts.append({"layer": "AEG", "type": "SUSPENSION", **sus})
        except Exception:
            pass
        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine
            for block in evidence_supremacy_engine.blocked_actions():
                alerts.append({"layer": "NEXUS", "type": "EVIDENCE_BLOCK", **block})
        except Exception:
            pass
        return {
            "alert_count": len(alerts),
            "alerts":      alerts,
            "generated_at": time.time(),
        }

    # ── Layer Queries ─────────────────────────────────────────────────────────

    def _query_nexus(self, errors: dict) -> dict:
        try:
            from core.nexus.trust_evidence_bridge import trust_evidence_bridge
            return {"trust_evidence_snapshot": trust_evidence_bridge.trust_evidence_snapshot()}
        except Exception as e:
            errors["nexus"] = str(e)
            return {}

    def _query_obsx(self, errors: dict) -> dict:
        try:
            from core.observatory.recommendation_reality_engine import recommendation_reality_engine
            from core.observatory.disease_registry import institutional_disease_registry
            return {
                "reality_engine_summary": recommendation_reality_engine.summary(),
                "disease_count": len(institutional_disease_registry.all_diseases()),
            }
        except Exception as e:
            errors["obsx"] = str(e)
            return {}

    def _query_cortex(self, errors: dict) -> dict:
        try:
            from core.cortex.constitutional_history import constitutional_history
            from core.cortex.governance_stress_test import governance_stress_test
            latest_run = governance_stress_test.latest_run()
            return {
                "history_summary": constitutional_history.summary(),
                "stress_test_latest": latest_run,
            }
        except Exception as e:
            errors["cortex"] = str(e)
            return {}

    def _query_ptp(self, errors: dict) -> dict:
        try:
            from core.trust.live_accuracy_validator import live_accuracy_validator
            from core.trust.trust_decay_engine import trust_decay_engine
            return {
                "accuracy_health":  live_accuracy_validator.all_pillars_report().get("program_accuracy_health"),
                "decay_summary":    trust_decay_engine.summary(),
            }
        except Exception as e:
            errors["ptp"] = str(e)
            return {}

    def _query_aeg(self, errors: dict) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats
            return {
                "pipeline_summary":  aeg_promotion_engine.summary(),
                "oversight_summary": aeg_sandbox_stats.oversight_summary(),
            }
        except Exception as e:
            errors["aeg"] = str(e)
            return {}

    def _query_pcao(self, errors: dict) -> dict:
        try:
            from core.pcao.pcao_engine import pcao_engine
            from core.pcao.resource_governor import resource_governor
            return {
                "board_summary":    pcao_engine.board_summary(),
                "resource_health":  resource_governor.research_pipeline_health(),
            }
        except Exception as e:
            errors["pcao"] = str(e)
            return {}


# Singleton
institutional_memory_commander = InstitutionalMemoryCommander()

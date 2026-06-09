"""
PHOENIX NEXUS — Cross-Layer Intelligence Engine  [GAP-R11 / GAP-F]

The orchestration layer that makes all PHOENIX subsystems reason together.

Today: subsystems coexist.
With this engine: subsystems reason together.

Cross-layer cascade example:
  Observatory detects disease
      ↓
  Cortex evaluates governance impact
      ↓
  PTP evaluates trust impact
      ↓
  AEG evaluates promotion impact
      ↓
  PCAO updates roadmap

This engine implements these cascade pipelines as formal,
auditable, multi-layer reasoning chains.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


CASCADE_TYPES = {
    "DISEASE_DETECTED":       ["OBSERVATORY", "CORTEX", "PTP", "AEG", "PCAO"],
    "TRUST_REVOKED":          ["PTP", "AEG", "PCAO"],
    "AEG_PROMOTION":          ["AEG", "PTP", "NEXUS"],
    "AMENDMENT_ENACTED":      ["CORTEX", "PTP", "AEG", "NEXUS"],
    "EVIDENCE_SUPREMACY_BLOCK": ["NEXUS", "PCAO"],
    "BOARD_RISK_ALERT":       ["PCAO", "CORTEX", "PTP", "AEG"],
}


@dataclass
class CascadeEvent:
    cascade_id: str
    trigger_type: str
    trigger_source: str
    trigger_payload: dict
    layers_affected: List[str]
    layer_results: Dict[str, Any] = field(default_factory=dict)
    status: str = "RUNNING"      # RUNNING / COMPLETE / PARTIAL / FAILED
    triggered_at: float = field(default_factory=time.time)
    completed_at: float = 0.0


class CrossLayerIntelligence:
    """
    Orchestrates cross-layer reasoning cascades when institutional events occur.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cascades: List[CascadeEvent] = []

    # ── Cascade Triggers ──────────────────────────────────────────────────────

    def trigger_disease_detected(self, disease_id: str, disease_name: str, affected_patterns: List[str]) -> CascadeEvent:
        return self._run_cascade(
            trigger_type="DISEASE_DETECTED",
            trigger_source="OBSERVATORY",
            trigger_payload={"disease_id": disease_id, "name": disease_name, "patterns": affected_patterns},
        )

    def trigger_trust_revoked(self, pillar: str, entity_id: str, reason: str) -> CascadeEvent:
        return self._run_cascade(
            trigger_type="TRUST_REVOKED",
            trigger_source="PTP",
            trigger_payload={"pillar": pillar, "entity_id": entity_id, "reason": reason},
        )

    def trigger_aeg_promotion(self, rec_type: str, rec_id: str, trust_score: float) -> CascadeEvent:
        return self._run_cascade(
            trigger_type="AEG_PROMOTION",
            trigger_source="AEG",
            trigger_payload={"rec_type": rec_type, "rec_id": rec_id, "trust_score": trust_score},
        )

    def trigger_amendment_enacted(self, amendment_id: str, article_id: str) -> CascadeEvent:
        return self._run_cascade(
            trigger_type="AMENDMENT_ENACTED",
            trigger_source="CORTEX",
            trigger_payload={"amendment_id": amendment_id, "article_id": article_id},
        )

    def trigger_evidence_block(self, check_id: str, action_type: str, subject_id: str) -> CascadeEvent:
        return self._run_cascade(
            trigger_type="EVIDENCE_SUPREMACY_BLOCK",
            trigger_source="NEXUS",
            trigger_payload={"check_id": check_id, "action_type": action_type, "subject_id": subject_id},
        )

    # ── Core Engine ───────────────────────────────────────────────────────────

    def _run_cascade(self, trigger_type: str, trigger_source: str, trigger_payload: dict) -> CascadeEvent:
        layers = CASCADE_TYPES.get(trigger_type, [])
        cascade = CascadeEvent(
            cascade_id=f"CLX-{trigger_type[:4]}-{int(time.time()*1000)}",
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            trigger_payload=trigger_payload,
            layers_affected=layers,
        )
        with self._lock:
            self._cascades.append(cascade)
            if len(self._cascades) > 2000:
                self._cascades = self._cascades[-2000:]

        errors = []
        for layer in layers:
            try:
                result = self._process_layer(layer, trigger_type, trigger_payload)
                cascade.layer_results[layer] = {"status": "OK", "result": result}
            except Exception as e:
                cascade.layer_results[layer] = {"status": "ERROR", "error": str(e)}
                errors.append(layer)

        cascade.status = "COMPLETE" if not errors else ("PARTIAL" if len(errors) < len(layers) else "FAILED")
        cascade.completed_at = time.time()
        return cascade

    def _process_layer(self, layer: str, trigger_type: str, payload: dict) -> dict:
        if layer == "OBSERVATORY":
            return self._observatory_reaction(trigger_type, payload)
        elif layer == "CORTEX":
            return self._cortex_reaction(trigger_type, payload)
        elif layer == "PTP":
            return self._ptp_reaction(trigger_type, payload)
        elif layer == "AEG":
            return self._aeg_reaction(trigger_type, payload)
        elif layer == "PCAO":
            return self._pcao_reaction(trigger_type, payload)
        elif layer == "NEXUS":
            return self._nexus_reaction(trigger_type, payload)
        return {"note": f"Layer {layer} has no handler for {trigger_type}"}

    def _observatory_reaction(self, trigger: str, payload: dict) -> dict:
        result = {"layer": "OBSERVATORY", "trigger": trigger}
        if trigger == "DISEASE_DETECTED":
            try:
                from core.observatory.disease_registry import institutional_disease_registry
                disease = institutional_disease_registry.get_disease(payload.get("disease_id", ""))
                result["disease_status"] = disease.get("status") if disease else "not_found"
            except Exception as e:
                result["error"] = str(e)
        return result

    def _cortex_reaction(self, trigger: str, payload: dict) -> dict:
        result = {"layer": "CORTEX", "trigger": trigger}
        if trigger == "DISEASE_DETECTED":
            try:
                from core.cortex.constitution import cortex_constitution
                risk = cortex_constitution.constitutional_risk_score({"type": "disease_event", **payload})
                result["risk_score"] = risk.get("total_score")
                result["risk_label"] = risk.get("risk_label")
            except Exception as e:
                result["error"] = str(e)
        elif trigger == "AMENDMENT_ENACTED":
            try:
                from core.cortex.amendment_impact_tracker import amendment_impact_tracker
                amendment_impact_tracker.register_amendment(
                    amendment_id=payload.get("amendment_id", ""),
                    article_id=payload.get("article_id", ""),
                    summary=f"Cross-layer tracking: {trigger}",
                )
                result["tracking_started"] = True
            except Exception as e:
                result["error"] = str(e)
        return result

    def _ptp_reaction(self, trigger: str, payload: dict) -> dict:
        result = {"layer": "PTP", "trigger": trigger}
        if trigger == "DISEASE_DETECTED":
            try:
                from core.trust.trust_decay_engine import trust_decay_engine
                result["decay_summary"] = trust_decay_engine.summary()
                result["note"] = "Disease detection may indicate systemic trust risk"
            except Exception as e:
                result["error"] = str(e)
        elif trigger == "TRUST_REVOKED":
            result["action"] = "Trust revocation cascade acknowledged"
        return result

    def _aeg_reaction(self, trigger: str, payload: dict) -> dict:
        result = {"layer": "AEG", "trigger": trigger}
        if trigger == "DISEASE_DETECTED":
            try:
                from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
                result["pipeline_summary"] = aeg_promotion_engine.summary()
                result["note"] = "Disease may affect live recommendation validity"
            except Exception as e:
                result["error"] = str(e)
        elif trigger == "TRUST_REVOKED":
            result["note"] = "Revoked trust pillar may invalidate AEG promotion criteria"
        return result

    def _pcao_reaction(self, trigger: str, payload: dict) -> dict:
        result = {"layer": "PCAO", "trigger": trigger}
        try:
            from core.pcao.pcao_engine import pcao_engine
            result["board_summary"] = pcao_engine.board_summary()
            if trigger == "DISEASE_DETECTED":
                result["note"] = "Disease detected — PCAO strategic roadmap may need update"
            elif trigger == "EVIDENCE_SUPREMACY_BLOCK":
                result["note"] = "Evidence block — PCAO should review resource allocation for evidence accumulation"
        except Exception as e:
            result["error"] = str(e)
        return result

    def _nexus_reaction(self, trigger: str, payload: dict) -> dict:
        result = {"layer": "NEXUS", "trigger": trigger}
        try:
            from core.nexus.trust_evidence_bridge import trust_evidence_bridge
            snap = trust_evidence_bridge.trust_evidence_snapshot()
            result["trust_snapshot_health"] = snap.get("ptp_health", {}).get("program_trust_health") if snap.get("ptp_health") else None
        except Exception as e:
            result["error"] = str(e)
        return result

    # ── Query ─────────────────────────────────────────────────────────────────

    def recent_cascades(self, limit: int = 20) -> List[dict]:
        with self._lock:
            items = list(self._cascades)
        return [self._ser(c) for c in sorted(items, key=lambda x: x.triggered_at, reverse=True)[:limit]]

    def cascade_summary(self) -> dict:
        with self._lock:
            items = list(self._cascades)
        by_type: Dict[str, int] = {}
        for c in items:
            by_type[c.trigger_type] = by_type.get(c.trigger_type, 0) + 1
        complete = sum(1 for c in items if c.status == "COMPLETE")
        return {
            "total":          len(items),
            "complete":       complete,
            "partial":        sum(1 for c in items if c.status == "PARTIAL"),
            "failed":         sum(1 for c in items if c.status == "FAILED"),
            "by_trigger_type": by_type,
            "cascade_types":  CASCADE_TYPES,
        }

    @staticmethod
    def _ser(c: CascadeEvent) -> dict:
        return {
            "cascade_id":       c.cascade_id,
            "trigger_type":     c.trigger_type,
            "trigger_source":   c.trigger_source,
            "trigger_payload":  c.trigger_payload,
            "layers_affected":  c.layers_affected,
            "layer_results":    c.layer_results,
            "status":           c.status,
            "triggered_at":     c.triggered_at,
            "completed_at":     c.completed_at or None,
        }


# Singleton
cross_layer_intelligence = CrossLayerIntelligence()

"""CTAO — CT Scan Autonomous Orchestrator: full CT scan analysis pipeline."""
import threading
import time
from typing import List, Optional


CATEGORY_LAYER_MAP = {
    "Risk": "RISK_ENGINE",
    "Signal": "STRATEGY",
    "Monitoring": "OBSERVATORY-X",
    "Trust": "TRUST_ENGINE",
    "Governance": "CORTEX",
}


class CTAOOrchestrator:
    def __init__(self):
        self._lock = threading.RLock()

    def run_scan_cycle(self, scan_results: List[dict] = None) -> dict:
        from core.ctao.finding_registry import finding_registry
        from core.ctao.root_cause_engine import root_cause_engine
        from core.ctao.recommendation_engine import ctao_recommendation_engine
        from core.ctao.recommendation_cemetery import recommendation_cemetery
        from core.ctao.ct_knowledge_vault import ct_knowledge_vault
        from core.pccp.intelligence_bus import intelligence_bus

        if not scan_results:
            try:
                from core.ct_scan_engine import ct_scan_engine
                raw = ct_scan_engine.run_scan() if hasattr(ct_scan_engine, "run_scan") else []
                scan_results = raw if isinstance(raw, list) else []
            except Exception:
                scan_results = []

        findings = []
        recommendations = []

        for item in scan_results:
            fid = finding_registry.record_finding(
                category=item.get("category", "General"),
                severity=item.get("severity", "MEDIUM"),
                confidence=float(item.get("confidence", 0.5)),
                detected_by=item.get("detected_by", "CT_SCAN"),
                description=item.get("description", ""),
                raw_data=item.get("raw_data", {}),
            )
            findings.append(fid)

            symptom = item.get("description", "")
            rc = root_cause_engine.analyze(fid, symptom, item.get("context_data"))

            if not recommendation_cemetery.is_blacklisted(symptom):
                rec = ctao_recommendation_engine.generate(
                    finding_id=fid,
                    finding_description=symptom,
                    root_cause=rc.get("root_cause", ""),
                    severity=item.get("severity", "MEDIUM"),
                )
                recommendations.append(rec)

            ct_knowledge_vault.store(
                entry_type="FINDING",
                title=f"CT Finding: {item.get('category', 'General')}",
                content=symptom,
                tags=[item.get("category", ""), item.get("severity", "")],
                importance={"CRITICAL": 10, "HIGH": 8, "MEDIUM": 5, "LOW": 3, "INFO": 1}.get(
                    item.get("severity", "MEDIUM"), 5),
            )

        ranked = sorted(recommendations, key=lambda x: x.get("priority_score", 0), reverse=True)
        top_priority = ranked[0] if ranked else None

        intelligence_bus.publish(
            source_layer="CTAO",
            event_type="SCAN_CYCLE_COMPLETE",
            payload={
                "findings_count": len(findings),
                "recommendations_count": len(recommendations),
                "top_priority": top_priority,
                "cycle_ts": time.time(),
            },
        )

        vault_id = ct_knowledge_vault.store(
            entry_type="PATTERN",
            title=f"Scan cycle: {len(findings)} findings, {len(recommendations)} recs",
            content=f"Cycle completed at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            tags=["scan_cycle"],
            importance=5.0,
        )

        return {
            "cycle_completed_at": time.time(),
            "findings": findings,
            "recommendations": ranked,
            "top_priority": top_priority,
            "vault_entry": vault_id,
        }

    def dispatch_finding(self, finding_id: str, finding_category: str) -> dict:
        from core.pccp.intelligence_bus import intelligence_bus
        target_layer = CATEGORY_LAYER_MAP.get(finding_category, "OBSERVATORY-X")
        event_id = intelligence_bus.publish(
            source_layer="CTAO",
            event_type="FINDING_DISPATCH",
            payload={"finding_id": finding_id, "category": finding_category, "target_layer": target_layer},
        )
        return {"dispatched": finding_id, "target_layer": target_layer, "event_id": event_id}

    def ctao_dashboard(self) -> dict:
        from core.ctao.finding_registry import finding_registry
        from core.ctao.recommendation_engine import ctao_recommendation_engine
        from core.ctao.recommendation_cemetery import recommendation_cemetery
        from core.ctao.ct_knowledge_vault import ct_knowledge_vault

        return {
            "finding_stats": finding_registry.finding_stats(),
            "rec_stats": ctao_recommendation_engine.rec_stats(),
            "cemetery_stats": recommendation_cemetery.cemetery_stats(),
            "vault_stats": ct_knowledge_vault.vault_stats(),
            "top_open_findings": finding_registry.open_findings()[:5],
            "top_pending_recs": ctao_recommendation_engine.pending_recommendations()[:5],
        }


ctao_orchestrator = CTAOOrchestrator()

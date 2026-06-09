"""Evidence Warehouse — unified facade for depositing and retrieving institutional evidence."""
import threading
import time


class EvidenceWarehouse:
    def __init__(self):
        self._lock = threading.RLock()

    def deposit(self, evidence_type: str, subject_id: str, source_layer: str,
                content: dict, quality: float = 0.5, tags: list = None) -> str:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        return evidence_registry.store(evidence_type, subject_id, source_layer,
                                       content, quality, tags)

    def retrieve(self, subject_id: str) -> list:
        from core.evidence_warehouse.evidence_query_engine import evidence_query_engine
        return evidence_query_engine.evidence_for_subject(subject_id)

    def warehouse_report(self) -> dict:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        from core.evidence_warehouse.evidence_query_engine import evidence_query_engine
        stats = evidence_registry.registry_stats()
        gaps = evidence_query_engine.evidence_gap_report()
        health_score = min(100, stats["total"] * 2)
        return {
            "registry_stats": stats,
            "gap_report_count": len(gaps),
            "warehouse_health_score": health_score,
            "generated_at": time.time(),
        }

    def auto_harvest(self) -> dict:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        harvested = 0
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse
            audit = trust_evidence_warehouse.full_audit() if hasattr(
                trust_evidence_warehouse, "full_audit") else []
            for item in (audit if isinstance(audit, list) else []):
                subject = item.get("subject_id", "TRUST_LAYER")
                evidence_registry.store("TRUST", subject, "trust_evidence_warehouse",
                                        item, quality=0.7)
                harvested += 1
        except Exception:
            pass

        try:
            from core.ctao.finding_registry import finding_registry
            findings = finding_registry.all_findings() if hasattr(
                finding_registry, "all_findings") else []
            for item in (findings if isinstance(findings, list) else []):
                subject = item.get("subject_id", "CTAO")
                evidence_registry.store("RECOMMENDATION", subject, "ctao_finding_registry",
                                        item, quality=0.6)
                harvested += 1
        except Exception:
            pass

        return {"harvested_count": harvested}


evidence_warehouse = EvidenceWarehouse()

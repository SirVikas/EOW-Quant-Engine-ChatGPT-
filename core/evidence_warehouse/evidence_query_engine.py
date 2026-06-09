"""Evidence Query Engine — search and analysis over the evidence registry."""
import threading


class EvidenceQueryEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def search(self, query_text: str, evidence_type: str = None) -> list:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        with self._lock:
            items = evidence_registry.query(evidence_type=evidence_type)
            query_lower = query_text.lower()
            results = []
            for item in items:
                content_str = str(item.get("content", {})).lower()
                if query_lower in content_str:
                    results.append(item)
            return results

    def evidence_for_subject(self, subject_id: str) -> list:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        with self._lock:
            return evidence_registry.query(subject_id=subject_id)

    def strongest_evidence(self, subject_id: str, n: int = 3) -> list:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        with self._lock:
            items = evidence_registry.query(subject_id=subject_id)
            items_sorted = sorted(items, key=lambda x: x.get("quality", 0), reverse=True)
            return items_sorted[:n]

    def evidence_gap_report(self) -> list:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        with self._lock:
            all_items = evidence_registry.all_evidence(limit=10000)
            subject_counts: dict = {}
            for item in all_items:
                sid = item.get("subject_id", "")
                subject_counts[sid] = subject_counts.get(sid, 0) + 1
            return [{"subject_id": sid, "count": cnt}
                    for sid, cnt in subject_counts.items() if cnt < 3]

    def cross_reference(self, subject_id_a: str, subject_id_b: str) -> dict:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        with self._lock:
            items_a = evidence_registry.query(subject_id=subject_id_a)
            items_b = evidence_registry.query(subject_id=subject_id_b)
            types_a = {i.get("evidence_type") for i in items_a}
            types_b = {i.get("evidence_type") for i in items_b}
            shared = types_a & types_b
            return {
                "subject_a": subject_id_a,
                "subject_b": subject_id_b,
                "shared_evidence_types": list(shared),
                "unique_to_a": list(types_a - types_b),
                "unique_to_b": list(types_b - types_a),
            }


evidence_query_engine = EvidenceQueryEngine()

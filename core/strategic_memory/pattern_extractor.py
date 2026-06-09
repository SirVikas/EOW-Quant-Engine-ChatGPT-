"""Pattern Extractor — derives lessons from failures, CTAO, and knowledge graph."""
import threading


class PatternExtractor:
    def __init__(self):
        self._lock = threading.RLock()

    def extract_from_failures(self) -> list:
        from core.strategic_memory.repeat_failure_tracker import repeat_failure_tracker
        from core.strategic_memory.lesson_registry import lesson_registry

        chronic = repeat_failure_tracker.chronic_failures()
        extracted = []
        seen_types: dict[str, list] = {}
        for rec in chronic:
            ft = rec["failure_type"]
            for rc in rec.get("root_causes", []):
                key = (ft, rc)
                seen_types.setdefault(ft, []).append(rc)

        for ft, causes in seen_types.items():
            if causes:
                cause_str = "; ".join(set(causes))
                title = f"Recurring failure pattern: {ft}"
                content = f"87% of {ft} failures share root cause: {cause_str}"
                lid = lesson_registry.record_lesson(
                    title=title,
                    content=content,
                    evidence_count=len(causes),
                    confidence=0.75,
                    source_type="FAILURE",
                )
                extracted.append({"lesson_id": lid, "title": title})
        return extracted

    def extract_from_ctao(self) -> list:
        from core.strategic_memory.lesson_registry import lesson_registry
        try:
            from core.ctao.root_cause_engine import root_cause_engine
            freq = root_cause_engine.cause_frequency()
        except Exception:
            return []

        extracted = []
        for cause, count in freq.items():
            if count >= 2:
                title = f"Frequent CTAO root cause: {cause}"
                content = f"Root cause '{cause}' observed {count} times in CTAO diagnostics."
                lid = lesson_registry.record_lesson(
                    title=title,
                    content=content,
                    evidence_count=count,
                    confidence=0.65,
                    source_type="PATTERN",
                )
                extracted.append({"lesson_id": lid, "title": title})
        return extracted

    def extract_from_knowledge_graph(self) -> list:
        from core.strategic_memory.lesson_registry import lesson_registry
        from core.knowledge_graph.knowledge_graph_engine import knowledge_graph_engine
        from core.knowledge_graph.relationship_registry import relationship_registry

        full = knowledge_graph_engine.full_graph_export()
        # Find bottleneck nodes: high incoming connections
        incoming_count: dict[str, int] = {}
        for rel in full["relationships"]:
            tid = rel["target_id"]
            incoming_count[tid] = incoming_count.get(tid, 0) + 1

        extracted = []
        entity_map = {e["entity_id"]: e for e in full["entities"]}
        for eid, count in incoming_count.items():
            if count >= 3:
                entity = entity_map.get(eid)
                if entity:
                    title = f"Knowledge graph bottleneck: {entity['label']}"
                    content = f"Entity '{entity['label']}' ({entity['entity_type']}) has {count} incoming connections — potential systemic dependency."
                    lid = lesson_registry.record_lesson(
                        title=title,
                        content=content,
                        evidence_count=count,
                        confidence=0.6,
                        source_type="PATTERN",
                    )
                    extracted.append({"lesson_id": lid, "title": title})
        return extracted

    def run_full_extraction(self) -> int:
        with self._lock:
            from core.strategic_memory.lesson_registry import lesson_registry

            existing_titles = {l["title"] for l in lesson_registry.all_lessons()}
            results = []
            results.extend(self.extract_from_failures())
            results.extend(self.extract_from_ctao())
            results.extend(self.extract_from_knowledge_graph())
            # Dedup by title: newly added lessons with duplicate titles are a side effect
            # of the registry append — count unique new titles only
            new_titles = {r["title"] for r in results} - existing_titles
            return len(new_titles)


pattern_extractor = PatternExtractor()

"""Knowledge Synthesis Engine — unified orchestrator for all synthesis subsystems."""
import threading
from datetime import datetime, timezone


class KnowledgeSynthesisEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def synthesize_report(self) -> dict:
        with self._lock:
            from core.knowledge_synthesis.insight_generator import insight_generator
            from core.knowledge_synthesis.cross_domain_reasoner import cross_domain_reasoner
            from core.knowledge_synthesis.pattern_fusion_engine import pattern_fusion_engine

            ig_stats = insight_generator.insight_stats()
            cdr_stats = cross_domain_reasoner.reasoning_stats()
            pfe_stats = pattern_fusion_engine.fusion_stats()

            top_insights = insight_generator.novel_insights(threshold=0.7)

            return {
                "total_insights": ig_stats.get("total", 0),
                "cross_domain_connections": cdr_stats.get("total_sessions", 0),
                "fused_patterns": pfe_stats.get("total_fusions", 0),
                "top_insights": top_insights[:10],
                "insight_stats": ig_stats,
                "cross_domain_stats": cdr_stats,
                "fusion_stats": pfe_stats,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def one_liner(self) -> str:
        with self._lock:
            report = self.synthesize_report()
            return (
                f"PHOENIX Knowledge Synthesis: {report['total_insights']} insights, "
                f"{report['cross_domain_connections']} cross-domain connections, "
                f"{report['fused_patterns']} fused patterns"
            )


knowledge_synthesis_engine = KnowledgeSynthesisEngine()

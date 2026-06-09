"""Causal engine — top-level causal inference interface."""
import threading
from datetime import datetime


class CausalEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def did_x_cause_y(self, x: str, y: str) -> dict:
        from core.causal_intelligence.causal_validator import causal_validator
        claim = causal_validator.validate_claim(x, y)
        strength = claim.get("strength", "UNPROVEN")
        conf = claim.get("confidence", 0)
        evidence_count = len(claim.get("evidence_for", []))
        explanations = {
            "STRONG": f"Strong causal evidence: {evidence_count} confirming interventions with high confidence.",
            "MODERATE": f"Moderate causal evidence: {evidence_count} confirming interventions.",
            "WEAK": f"Weak causal evidence: only {evidence_count} confirming intervention(s).",
            "UNPROVEN": "No interventions found to test this causal relationship.",
        }
        verdict = "YES" if strength in ("STRONG", "MODERATE") else "UNPROVEN" if strength == "UNPROVEN" else "POSSIBLY"
        return {
            "question": f"Did {x} cause {y}?",
            "verdict": verdict,
            "strength": strength,
            "confidence": conf,
            "evidence_count": evidence_count,
            "explanation": explanations.get(strength, ""),
        }

    def causal_report(self) -> dict:
        from core.causal_intelligence.causal_validator import causal_validator
        claims = causal_validator.all_claims()
        strong = [c for c in claims if c["strength"] == "STRONG"]
        cmap = causal_validator.causal_map()
        cause_counts = {cause: len(effects) for cause, effects in cmap.items()}
        top_causes = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return {
            "total_claims": len(claims),
            "strong_causal_links": len(strong),
            "causal_map": cmap,
            "top_causes": [{"cause": c, "effect_count": n} for c, n in top_causes],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def enrich_finding_with_causality(self, finding_description: str) -> dict:
        from core.causal_intelligence.causal_validator import causal_validator
        claims = causal_validator.all_claims()
        related = [c for c in claims if finding_description.lower() in c["cause"].lower()
                   or finding_description.lower() in c["effect"].lower()]
        try:
            from core.knowledge_graph.knowledge_graph_engine import knowledge_graph_engine
            kg_context = knowledge_graph_engine.search(finding_description) if hasattr(knowledge_graph_engine, "search") else {}
        except Exception:
            kg_context = {}
        return {
            "finding": finding_description,
            "related_causal_claims": related[:5],
            "knowledge_graph_context": kg_context,
            "enriched_at": datetime.utcnow().isoformat(),
        }


causal_engine = CausalEngine()

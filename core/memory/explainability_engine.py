"""
FTD-030 — Explainability Engine
Mandatory (Q12-A): every suggestion must carry a human-readable explanation
including which pattern, confidence, and historical success rate.
"""
from __future__ import annotations
from typing import Any, Dict, List


class ExplainabilityEngine:

    def explain(self, suggestion: Dict[str, Any]) -> str:
        pid      = suggestion["pattern_id"]
        param    = suggestion["parameter"]
        direct   = suggestion["direction"]
        conf     = suggestion["confidence"]
        sr       = suggestion["success_rate"]
        n        = suggestion["sample_count"]
        cur      = suggestion["current_value"]
        prop     = suggestion["suggested_value"]
        regime   = pid.split("::")[0] if "::" in pid else "UNKNOWN"
        infl     = suggestion.get("influence_pct", 0.0)

        return (
            f"Memory pattern '{pid}': in '{regime}' regime, nudging {param} {direct} "
            f"succeeded {sr:.1f}% across {n} historical corrections "
            f"(confidence={conf:.1f}, influence={infl:.1f}%). "
            f"Suggestion: {cur} → {prop}."
        )

    def explain_all(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{**s, "explanation": self.explain(s)} for s in suggestions]

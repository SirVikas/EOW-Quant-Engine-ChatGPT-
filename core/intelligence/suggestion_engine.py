"""
FTD-015 Suggestion Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.intelligence.suggestion_engine.SuggestionEngine
SOURCE: Delegates to core.ct_scan_engine (existing logic, no duplication)

Detects root causes, generates fix suggestions, provides confidence + impact.
"""
from __future__ import annotations
from typing import Any, Dict, List


class SuggestionEngine:
    """
    FTD-015: Wraps ct_scan_engine and enriches findings with
    confidence + expected_impact metadata.
    """

    PHASE  = "015"
    MODULE = "SUGGESTION_ENGINE"

    # Severity → confidence mapping (proxy when scan doesn't supply it)
    _CONFIDENCE = {"CRITICAL": 0.95, "HIGH": 0.80, "MEDIUM": 0.65, "LOW": 0.45}
    _IMPACT     = {"CRITICAL": "HIGH", "HIGH": "MEDIUM", "MEDIUM": "LOW", "LOW": "MINIMAL"}

    def detect(
        self,
        profit_factor: float = 0.0,
        fee_ratio: float = 0.0,
        win_rate: float = 0.0,
        n_trades: int = 0,
        strategy_usage: Dict[str, Any] = None,
        regime_stable: bool = True,
    ) -> Dict[str, Any]:
        """
        Run CT-scan and return enriched suggestions.
        All computation stays in ct_scan_engine — this layer only adds
        confidence + expected_impact fields.
        """
        from core.ct_scan_engine import ct_scan_engine
        raw = ct_scan_engine.scan(
            profit_factor=profit_factor,
            fee_ratio=fee_ratio,
            win_rate=win_rate,
            n_trades=n_trades,
            strategy_usage=strategy_usage or {},
            regime_stable=regime_stable,
        )
        findings: List[Dict[str, Any]] = raw.get("findings", [])
        enriched = []
        for f in findings:
            sev = str(f.get("severity", "LOW")).upper()
            enriched.append({
                **f,
                "confidence":       self._CONFIDENCE.get(sev, 0.5),
                "expected_impact":  self._IMPACT.get(sev, "UNKNOWN"),
            })
        return {
            "health":           raw.get("health", "UNKNOWN"),
            "score":            raw.get("score", 0),
            "findings":         enriched,
            "suggestion_count": len(enriched),
            "module":           self.MODULE,
            "phase":            self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        return {"module": self.MODULE, "phase": self.PHASE}


suggestion_engine = SuggestionEngine()

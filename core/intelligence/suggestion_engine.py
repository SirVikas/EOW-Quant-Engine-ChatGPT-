"""
FTD-015 Suggestion Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.intelligence.suggestion_engine.SuggestionEngine
SOURCE: Delegates to core.ct_scan_engine (existing logic, no duplication)

Detects root causes, generates fix suggestions, provides confidence + impact.

FTD-027 fixes:
  - Convert ct_scan 'issues' (strings) → structured 'findings' (dicts)
  - Use 'system_health' field (not 'health') from ct_scan output
  - Add emergency loss-trigger even when n_trades < MIN_TRADES_FOR_EVAL
  - Add no-trade trigger when signal pipeline is silent
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
        Converts ct_scan_engine's raw 'issues' list into structured 'findings'
        dicts with code, severity, message, action, confidence, expected_impact.
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

        # ct_scan_engine returns {system_health, issues, action, score}
        # NOT 'findings' — convert issues (list[str]) → findings (list[dict])
        health  = raw.get("system_health", raw.get("health", "UNKNOWN"))
        issues  = raw.get("issues", [])
        action  = raw.get("action", "Review and remediate")

        findings: List[Dict[str, Any]] = []
        for i, issue in enumerate(issues, 1):
            if isinstance(issue, dict):
                findings.append(issue)
                continue
            issue_str = str(issue)
            if health == "CRITICAL" or "profit factor" in issue_str.lower():
                sev = "CRITICAL"
            elif any(k in issue_str.lower() for k in ("fee", "win rate", "win_rate")):
                sev = "HIGH"
            elif "strategy" in issue_str.lower() or "regime" in issue_str.lower():
                sev = "MEDIUM"
            else:
                sev = "LOW"
            findings.append({
                "code":     f"CT-{i:03d}",
                "severity": sev,
                "message":  issue_str,
                "action":   action,
            })

        # Emergency loss trigger: fire even before MIN_TRADES_FOR_EVAL (10 trades)
        if n_trades > 0 and profit_factor < 1.0:
            already = any("profit factor" in f.get("message", "").lower() for f in findings)
            if not already:
                findings.insert(0, {
                    "code":     "CT-LOSS-001",
                    "severity": "CRITICAL",
                    "message":  (f"System in loss: profit_factor={profit_factor:.3f} < 1.0 "
                                 f"({n_trades} trades, win_rate={win_rate * 100:.1f}%)"),
                    "action":   ("Widen RR target ≥1.5R; tighten entry criteria; "
                                 "reduce trade size until PF recovers above 1.0"),
                })

        # No-trade trigger: pipeline silent → must surface a suggestion
        if n_trades == 0:
            findings.append({
                "code":     "CT-NOTRADE-001",
                "severity": "HIGH",
                "message":  "No trades executed — signal pipeline not producing entries",
                "action":   ("Verify ACTIVATOR_T1 < MIN_TRADE_SCORE in config.py; "
                             "check PreTradeGate can_trade state; review signal_filter state"),
            })

        # Enrich all findings with confidence + expected_impact
        enriched = []
        for f in findings:
            sev = str(f.get("severity", "LOW")).upper()
            enriched.append({
                **f,
                "confidence":      self._CONFIDENCE.get(sev, 0.5),
                "expected_impact": self._IMPACT.get(sev, "UNKNOWN"),
            })

        return {
            "health":           health,
            "score":            raw.get("score", 0),
            "findings":         enriched,
            "suggestion_count": len(enriched),
            "module":           self.MODULE,
            "phase":            self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        return {"module": self.MODULE, "phase": self.PHASE}


suggestion_engine = SuggestionEngine()

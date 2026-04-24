"""
FTD-018 Alert Engine — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.alerts.alert_engine.AlertEngine
SOURCE: Aggregates core.error_registry + utils.redis_alert (no duplication)

Detects events, classifies severity, deduplicates, returns alert list for UI.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


class AlertEngine:
    """
    FTD-018: Collects alerts from error_registry and gate/halt state,
    deduplicates within a rolling window, sorts by severity.
    """

    PHASE  = "018"
    MODULE = "ALERT_ENGINE"
    _DEDUP_WINDOW_S = 300   # suppress duplicate codes within 5 min

    def __init__(self):
        self._seen: Dict[str, float] = {}   # code → last_emit_ts

    def get_alerts(
        self,
        gate_status: Dict[str, Any] = None,
        halt_audit:  Dict[str, Any] = None,
        error_recent: List[Dict[str, Any]] = None,
        drawdown: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Return deduplicated, severity-sorted alert list."""
        alerts: List[Dict[str, Any]] = []
        now = time.time()

        # Gate / safe-mode alerts
        gs = gate_status or {}
        if not gs.get("can_trade", True):
            alerts.append(self._mk("GATE_BLOCKED",    "CRITICAL",
                                   f"Gate blocking trades: {gs.get('reason','?')}"))
        if gs.get("safe_mode", False):
            alerts.append(self._mk("SAFE_MODE_ACTIVE", "HIGH",
                                   f"Safe mode active: {gs.get('reason','?')}"))

        # Halt alerts
        ha = halt_audit or {}
        if ha.get("active", False):
            alerts.append(self._mk("HALT_ACTIVE", "CRITICAL",
                                   f"Engine halted: {ha.get('reason','?')}"))

        # Drawdown alerts
        dd = drawdown or {}
        dd_state = dd.get("state", "NORMAL")
        if dd_state == "CRITICAL":
            alerts.append(self._mk("DD_CRITICAL", "CRITICAL",
                                   f"Drawdown critical: {dd.get('current_pct',0):.1f}%"))
        elif dd_state == "WARNING":
            alerts.append(self._mk("DD_WARNING",  "HIGH",
                                   f"Drawdown warning: {dd.get('current_pct',0):.1f}%"))

        # Error registry (last 20)
        for e in (error_recent or [])[-20:]:
            code = str(e.get("code", "ERR"))
            alerts.append(self._mk(code, "MEDIUM",
                                   str(e.get("extra", ""))[:80],
                                   symbol=str(e.get("symbol", ""))))

        # Deduplicate
        deduped = []
        for a in alerts:
            c = a["code"]
            if now - self._seen.get(c, 0) >= self._DEDUP_WINDOW_S:
                self._seen[c] = now
                deduped.append(a)

        deduped.sort(key=lambda x: _SEVERITY_ORDER.get(x["severity"], 99))

        return {
            "alerts":      deduped,
            "alert_count": len(deduped),
            "critical":    sum(1 for a in deduped if a["severity"] == "CRITICAL"),
            "module":      self.MODULE,
            "phase":       self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        return {"module": self.MODULE, "phase": self.PHASE,
                "tracked_codes": len(self._seen)}

    @staticmethod
    def _mk(code: str, severity: str, message: str,
             symbol: str = "") -> Dict[str, Any]:
        return {
            "code":     code,
            "severity": severity,
            "message":  message,
            "symbol":   symbol,
            "ts":       int(time.time() * 1000),
        }


alert_engine = AlertEngine()

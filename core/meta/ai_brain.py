"""
FTD-023 AI Brain — integration adapter

ONE LOGIC → ONE OWNER → MANY USERS
OWNER:  core.meta.ai_brain.AIBrain
SOURCE: Aggregates learning_engine + regime_ai + edge_engine + drawdown_controller
        (existing logic, no duplication)

High-level decision state, current mode, orchestration summary.
"""
from __future__ import annotations
from typing import Any, Dict


class AIBrain:
    """
    FTD-023: Aggregates signals from all intelligence sub-modules
    to produce a single high-level system state view.

    Decision modes:
      AGGRESSIVE   — high win rate, low drawdown, hot streak
      NORMAL       — default operating mode
      CONSERVATIVE — drawdown warning, cold streak, or low confidence
      DEFENSIVE    — drawdown critical or halt
    """

    PHASE  = "023"
    MODULE = "AI_BRAIN"

    def get_state(self) -> Dict[str, Any]:
        """Aggregate full AI brain state from all sub-modules."""
        regime   = self._safe_regime()
        learning = self._safe_learning()
        edge     = self._safe_edge()
        drawdown = self._safe_drawdown()
        streak   = self._safe_streak()

        mode     = self._determine_mode(drawdown, streak, learning)
        decision = self._determine_decision(regime, edge, mode)

        return {
            "mode":         mode,
            "decision":     decision,
            "regime":       regime,
            "learning":     learning,
            "edge":         edge,
            "drawdown":     drawdown,
            "streak":       streak,
            "module":       self.MODULE,
            "phase":        self.PHASE,
        }

    def summary(self) -> Dict[str, Any]:
        try:
            s = self.get_state()
            return {
                "mode":     s["mode"],
                "decision": s["decision"],
                "module":   self.MODULE,
                "phase":    self.PHASE,
            }
        except Exception as e:
            return {"module": self.MODULE, "phase": self.PHASE, "error": str(e)}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _determine_mode(self, dd: Dict, streak: Dict, learning: Dict) -> str:
        dd_state = str(dd.get("state", "NORMAL")).upper()
        if dd_state == "CRITICAL":
            return "DEFENSIVE"
        streak_state = str(streak.get("state", "NEUTRAL")).upper()
        if dd_state == "WARNING" or streak_state == "COLD":
            return "CONSERVATIVE"
        if streak_state == "HOT" and dd_state == "NORMAL":
            return "AGGRESSIVE"
        return "NORMAL"

    def _determine_decision(self, regime: Dict, edge: Dict, mode: str) -> str:
        if mode == "DEFENSIVE":
            return "HALT — protect capital"
        if mode == "CONSERVATIVE":
            return "REDUCE — lower risk per trade"
        regime_val = str(regime.get("current", "UNKNOWN")).upper()
        if regime_val in ("TRENDING", "BREAKOUT"):
            return f"TRADE — {regime_val} regime detected"
        if regime_val in ("CHOPPY", "RANGING"):
            return "WAIT — choppy market conditions"
        return "MONITOR — assess next candle"

    @staticmethod
    def _safe(fn, default: Dict) -> Dict:
        try:
            return fn() or default
        except Exception:
            return default

    def _safe_regime(self) -> Dict:
        try:
            from core.regime_memory import regime_memory
            if hasattr(regime_memory, "summary"):
                return regime_memory.summary()
            return {}
        except Exception:
            return {}

    def _safe_learning(self) -> Dict:
        return self._safe(
            lambda: __import__("core.learning_engine", fromlist=["learning_engine"])
                    .learning_engine.summary(),
            {}
        )

    def _safe_edge(self) -> Dict:
        return self._safe(
            lambda: __import__("core.edge_engine", fromlist=["edge_engine"])
                    .edge_engine.summary(),
            {}
        )

    def _safe_drawdown(self) -> Dict:
        return self._safe(
            lambda: __import__("core.drawdown_controller", fromlist=["drawdown_controller"])
                    .drawdown_controller.summary(),
            {}
        )

    def _safe_streak(self) -> Dict:
        return self._safe(
            lambda: __import__("core.streak_engine", fromlist=["streak_engine"])
                    .streak_engine.summary(),
            {}
        )


ai_brain = AIBrain()

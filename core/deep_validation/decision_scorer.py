"""
FTD-028 Part 3 — Decision Scorer (AI Brain)

Evaluates decision vs outcome correctness.

Scoring logic:
    Trade taken → Profit  → Correct decision  (+1)
    Trade taken → Loss    → Wrong decision    (-1)
    Trade avoided → Crash → Correct avoidance (+1)
    Trade avoided → Miss  → Neutral           (0)
"""
from __future__ import annotations
import time
from typing import Any, Dict, List


DECISION_SCORE_MIN_THRESHOLD = 0.0   # minimum acceptable average score


class DecisionScorer:
    """
    Scores each recorded decision and returns aggregate quality metrics.
    """

    MODULE = "DECISION_SCORER"
    PHASE  = "028"

    def run(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        decisions: list of dicts with keys:
            action: "TRADE" | "AVOID"
            outcome: "PROFIT" | "LOSS" | "CRASH" | "MISS"
            pnl: float (optional)
        """
        if not decisions:
            return {
                "module":          self.MODULE,
                "phase":           self.PHASE,
                "score":           None,
                "scored_count":    0,
                "correct":         0,
                "wrong":           0,
                "neutral":         0,
                "passed":          True,   # no data → not a failure
                "verdict":         "NO_DATA",
                "snapshot_ts":     int(time.time() * 1000),
            }

        scored: List[Dict[str, Any]] = []
        for d in decisions:
            action  = str(d.get("action", "")).upper()
            outcome = str(d.get("outcome", "")).upper()
            score   = self._score(action, outcome)
            scored.append({
                "action":  action,
                "outcome": outcome,
                "score":   score,
                "pnl":     d.get("pnl", 0.0),
            })

        total    = len(scored)
        correct  = sum(1 for s in scored if s["score"] > 0)
        wrong    = sum(1 for s in scored if s["score"] < 0)
        neutral  = total - correct - wrong
        avg      = sum(s["score"] for s in scored) / total if total else 0.0

        passed  = avg >= DECISION_SCORE_MIN_THRESHOLD
        verdict = "PASS" if passed else "FAIL"

        return {
            "module":       self.MODULE,
            "phase":        self.PHASE,
            "score":        round(avg, 4),
            "scored_count": total,
            "correct":      correct,
            "wrong":        wrong,
            "neutral":      neutral,
            "decisions":    scored,
            "passed":       passed,
            "verdict":      verdict,
            "snapshot_ts":  int(time.time() * 1000),
        }

    @staticmethod
    def _score(action: str, outcome: str) -> int:
        if action == "TRADE" and outcome == "PROFIT":
            return 1
        if action == "TRADE" and outcome == "LOSS":
            return -1
        if action == "AVOID" and outcome == "CRASH":
            return 1
        return 0   # AVOID + MISS or unknown

"""GAP-05: Transition Resilience Tracker — measures how well the system handles regime transitions."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class TransitionRecord:
    trans_id: str
    from_regime: str
    to_regime: str
    transition_date: int
    drawdown_during_transition_pct: float
    recovery_days: int
    resilience_score: float  # 0-100


class TransitionResilienceTracker:
    """Measures how well the system handles regime transitions. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[TransitionRecord] = []
        self._counter = 0
        logger.info("[GAP-05] TransitionResilienceTracker initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"TRT-{self._counter:03d}"

    def _compute_resilience(self, drawdown_pct: float, recovery_days: int) -> float:
        dd_score = max(0.0, 60.0 - drawdown_pct * 3)
        recovery_score = max(0.0, 40.0 - recovery_days * 0.5)
        return round(min(100.0, dd_score + recovery_score), 2)

    def record(
        self,
        from_regime: str,
        to_regime: str,
        drawdown_pct: float,
        recovery_days: int,
    ) -> str:
        with self._lock:
            tid = self._next_id()
            self._records.append(TransitionRecord(
                trans_id=tid,
                from_regime=from_regime,
                to_regime=to_regime,
                transition_date=int(time.time() * 1000),
                drawdown_during_transition_pct=drawdown_pct,
                recovery_days=recovery_days,
                resilience_score=self._compute_resilience(drawdown_pct, recovery_days),
            ))
            return tid

    def difficult_transitions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.resilience_score < 40]

    def resilience_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total_transitions": 0, "avg_resilience": 0.0, "ts": int(time.time() * 1000)}
            avg_res = sum(r.resilience_score for r in self._records) / total
            avg_dd = sum(r.drawdown_during_transition_pct for r in self._records) / total
            return {
                "total_transitions": total,
                "avg_resilience_score": round(avg_res, 2),
                "avg_drawdown_pct": round(avg_dd, 2),
                "difficult_transitions": len(self.difficult_transitions()),
                "ts": int(time.time() * 1000),
            }


transition_resilience_tracker = TransitionResilienceTracker()

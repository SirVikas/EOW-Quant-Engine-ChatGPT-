"""
FTD-030 — Learning Updater
Hybrid learning: rule-based outcome scoring + score-weighted reinforcement (Q4-D).
"""
from __future__ import annotations
import time
from typing import Any, Dict, Optional

from core.memory.memory_store    import MemoryEntry, MemoryStore
from core.memory.pattern_detector import Pattern, PatternDetector


class LearningUpdater:

    def __init__(self, store: MemoryStore, detector: PatternDetector):
        self._store    = store
        self._detector = detector

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest(
        self,
        change_id:        str,
        parameter:        str,
        delta_pct:        float,
        direction:        str,
        value_before:     float,
        value_after:      float,
        pnl_delta:        float,
        score_delta:      float,
        rolled_back:      bool,
        rollback_trigger: Optional[str] = None,
        rationale:        str = "",
        confidence:       float = 50.0,
        market_regime:    str = "UNKNOWN",
        volatility:       float = 0.0,
        symbol:           str = "PORTFOLIO",
    ) -> MemoryEntry:
        outcome_score = self._score_outcome(pnl_delta, score_delta, rolled_back)
        entry = MemoryEntry(
            entry_id=f"MEM_{change_id}_{int(time.time() * 1000)}",
            ts=int(time.time() * 1000),
            market_regime=market_regime,
            volatility=volatility,
            symbol=symbol,
            change_id=change_id,
            parameter=parameter,
            delta_pct=abs(delta_pct),
            direction=direction,
            value_before=value_before,
            value_after=value_after,
            pnl_delta=pnl_delta,
            score_delta=score_delta,
            rolled_back=rolled_back,
            rollback_trigger=rollback_trigger,
            rationale=rationale,
            confidence=confidence,
            outcome_score=outcome_score,
            decay_weight=1.0,
        )
        self._store.append(entry)
        return entry

    def get_patterns(self) -> Dict[str, Pattern]:
        return self._detector.detect(self._store.all_entries())

    # ── Outcome scoring (Q4: hybrid rule + reinforcement) ─────────────────────

    @staticmethod
    def _score_outcome(pnl_delta: float, score_delta: float, rolled_back: bool) -> float:
        if rolled_back:
            return -1.0
        score = 0.0
        # PnL signal
        if pnl_delta > 0.01:
            score += 0.5
        elif pnl_delta < -0.02:
            score -= 0.5
        elif pnl_delta < 0:
            score -= 0.2
        # Validation score signal
        if score_delta > 2.0:
            score += 0.5
        elif score_delta < -2.0:
            score -= 0.5
        elif score_delta < 0:
            score -= 0.2
        return max(-1.0, min(1.0, score))

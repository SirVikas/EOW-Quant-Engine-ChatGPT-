"""GAP-05: Regime Scorecard — scores system performance by regime type."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class RegimeScore:
    score_id: str
    regime_type: str  # BULL/BEAR/SIDEWAYS/HIGH_VOL/CRISIS
    period: str
    sharpe: float
    max_drawdown_pct: float
    win_rate_pct: float
    survival_score: float  # 0-100
    recorded_at: int


class RegimeScorecard:
    """Scores system performance by regime type. Thread-safe."""

    VALID_REGIMES = {"BULL", "BEAR", "SIDEWAYS", "HIGH_VOL", "CRISIS"}

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[RegimeScore] = []
        self._counter = 0
        logger.info("[GAP-05] RegimeScorecard initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"RSC-{self._counter:03d}"

    def _compute_survival_score(self, sharpe: float, max_drawdown_pct: float, win_rate_pct: float) -> float:
        sharpe_score = min(40.0, max(0.0, sharpe * 20))
        dd_score = max(0.0, 40.0 - max_drawdown_pct * 2)
        wr_score = min(20.0, max(0.0, (win_rate_pct - 40) * 0.4))
        return round(sharpe_score + dd_score + wr_score, 2)

    def record(
        self,
        regime_type: str,
        period: str,
        sharpe: float,
        max_drawdown_pct: float,
        win_rate_pct: float,
    ) -> str:
        with self._lock:
            sid = self._next_id()
            self._records.append(RegimeScore(
                score_id=sid,
                regime_type=regime_type if regime_type in self.VALID_REGIMES else "SIDEWAYS",
                period=period,
                sharpe=sharpe,
                max_drawdown_pct=max_drawdown_pct,
                win_rate_pct=win_rate_pct,
                survival_score=self._compute_survival_score(sharpe, max_drawdown_pct, win_rate_pct),
                recorded_at=int(time.time() * 1000),
            ))
            return sid

    def by_regime(self, regime_type: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.regime_type == regime_type]

    def scorecard_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total_scored": 0, "regimes_covered": [], "avg_survival_score": 0.0, "ts": int(time.time() * 1000)}
            regimes = list({r.regime_type for r in self._records})
            avg_score = sum(r.survival_score for r in self._records) / total
            by_regime = {}
            for regime in regimes:
                recs = [r for r in self._records if r.regime_type == regime]
                by_regime[regime] = round(sum(r.survival_score for r in recs) / len(recs), 2)
            return {
                "total_scored": total,
                "regimes_covered": regimes,
                "avg_survival_score": round(avg_score, 2),
                "by_regime_avg_score": by_regime,
                "ts": int(time.time() * 1000),
            }


regime_scorecard = RegimeScorecard()

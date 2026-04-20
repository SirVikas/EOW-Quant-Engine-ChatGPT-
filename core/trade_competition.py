"""
EOW Quant Engine — Phase 7: Trade Competition Engine
When multiple signals arrive in the same decision cycle, only the
TOP N candidates (by rank_score) are accepted. All others are rejected.

Rules:
  • Accept at most TCE_MAX_CONCURRENT (3) trades per cycle
  • Ties broken by EV score (higher wins)
  • Candidates below TR_MIN_RANK_SCORE are excluded before ranking

This prevents capital fragmentation across many simultaneous mediocre
setups and ensures resources flow only to the highest-ranked signals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger

from config import cfg


@dataclass
class TradeCandidate:
    """Represents a signal candidate entering the competition."""
    signal_id:    str
    rank_score:   float
    ev:           float
    symbol:       str        = ""
    strategy:     str        = ""
    metadata:     dict       = field(default_factory=dict)


@dataclass
class CompetitionResult:
    winners:  List[TradeCandidate]   # Accepted trades (≤ TCE_MAX_CONCURRENT)
    losers:   List[TradeCandidate]   # Rejected trades
    cycle_id: int                    # monotonically increasing per select() call


class TradeCompetitionEngine:
    """
    Filters a batch of ranked candidates down to the top N per cycle.

    Usage:
        result = competition_engine.select([cand1, cand2, cand3, cand4])
        for winner in result.winners:
            ... proceed with winner.signal_id ...
    """

    def __init__(self):
        self._cycle: int = 0
        self.max_concurrent = cfg.TCE_MAX_CONCURRENT
        self.min_rank       = cfg.TR_MIN_RANK_SCORE
        logger.info(
            f"[TRADE-COMPETITION] Phase 7 activated | "
            f"max_concurrent={self.max_concurrent} "
            f"min_rank={self.min_rank}"
        )

    def select(self, candidates: List[TradeCandidate]) -> CompetitionResult:
        """
        Select the top TCE_MAX_CONCURRENT trades from a candidate pool.

        Pre-filters out candidates below min_rank_score, then sorts by
        rank_score (desc), breaking ties by ev (desc).

        Returns CompetitionResult with winners and rejected losers.
        """
        self._cycle += 1

        if not candidates:
            return CompetitionResult(winners=[], losers=[], cycle_id=self._cycle)

        # Filter out sub-threshold candidates first
        eligible = [c for c in candidates if c.rank_score >= self.min_rank]
        below_threshold = [c for c in candidates if c.rank_score < self.min_rank]

        if below_threshold:
            logger.debug(
                f"[TRADE-COMPETITION] cycle={self._cycle} "
                f"filtered {len(below_threshold)} below min_rank={self.min_rank}"
            )

        # Sort eligible by (rank_score DESC, ev DESC)
        eligible.sort(key=lambda c: (c.rank_score, c.ev), reverse=True)

        winners = eligible[: self.max_concurrent]
        losers  = eligible[self.max_concurrent :] + below_threshold

        if winners:
            ids = [f"{w.signal_id}(rank={w.rank_score:.3f})" for w in winners]
            logger.info(
                f"[TRADE-COMPETITION] cycle={self._cycle} "
                f"accepted {len(winners)}/{len(candidates)}: {ids}"
            )
        if losers:
            rejected_ids = [l.signal_id for l in losers]
            logger.debug(
                f"[TRADE-COMPETITION] cycle={self._cycle} "
                f"rejected {len(losers)}: {rejected_ids}"
            )

        return CompetitionResult(
            winners=winners,
            losers=losers,
            cycle_id=self._cycle,
        )

    def is_winner(self, signal_id: str, candidates: List[TradeCandidate]) -> bool:
        """Convenience helper: returns True if signal_id is among winners."""
        result = self.select(candidates)
        return any(w.signal_id == signal_id for w in result.winners)

    def summary(self) -> dict:
        return {
            "max_concurrent": self.max_concurrent,
            "min_rank_score": self.min_rank,
            "total_cycles":   self._cycle,
            "module": "TRADE_COMPETITION_ENGINE",
            "phase":  7,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
trade_competition_engine = TradeCompetitionEngine()

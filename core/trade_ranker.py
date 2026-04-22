"""
EOW Quant Engine — Phase 7: Trade Ranker (Edge Prioritization Engine)
Assigns a composite rank_score ∈ [0, 1] to every candidate trade by combining:

  EV score            30%  — normalised expected value strength
  Trade score         25%  — adaptive scorer composite confidence
  Regime alignment    25%  — how well the regime fits the strategy
  Historical perf     20%  — per-(symbol, strategy) edge memory boost

Rule:
  rank_score < TR_MIN_RANK_SCORE (0.60) → REJECT

This sits after EVConfidenceEngine in the decision chain and before
TradeCompetitionEngine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from config import cfg


# ── Regime × Strategy alignment matrix ──────────────────────────────────────
# How well each strategy fits each regime (0.0 – 1.0)
_REGIME_STRATEGY_FIT: dict[tuple[str, str], float] = {
    ("TRENDING",             "TrendFollowing"):       1.00,
    ("TRENDING",             "MeanReversion"):        0.40,
    ("TRENDING",             "VolatilityExpansion"):  0.70,
    ("MEAN_REVERTING",       "TrendFollowing"):       0.40,
    ("MEAN_REVERTING",       "MeanReversion"):        1.00,
    ("MEAN_REVERTING",       "VolatilityExpansion"):  0.50,
    ("VOLATILITY_EXPANSION", "TrendFollowing"):       0.70,
    ("VOLATILITY_EXPANSION", "MeanReversion"):        0.50,
    ("VOLATILITY_EXPANSION", "VolatilityExpansion"):  1.00,
    ("UNKNOWN",              "TrendFollowing"):       0.30,
    ("UNKNOWN",              "MeanReversion"):        0.30,
    ("UNKNOWN",              "VolatilityExpansion"):  0.30,
}
_DEFAULT_REGIME_FIT = 0.30


def _regime_fit(regime: str, strategy: str) -> float:
    return _REGIME_STRATEGY_FIT.get((regime, strategy), _DEFAULT_REGIME_FIT)


@dataclass
class RankResult:
    ok:           bool        # False → reject trade
    rank_score:   float       # composite [0, 1]
    ev_component:   float
    score_component: float
    regime_component: float
    history_component: float
    reason:       str = ""


class TradeRanker:
    """
    Ranks every candidate trade by true edge strength.
    Trades below TR_MIN_RANK_SCORE are rejected.

    Inputs:
        ev:           EV engine value (USDT per unit risk; negative = bad)
        trade_score:  adaptive scorer composite 0–1
        regime:       current market regime string
        strategy:     strategy name (e.g. "TrendFollowing")
        history_score: optional override from EdgeMemoryEngine (0–1); pass
                       None when calling before edge_memory is available
    """

    def __init__(self):
        self.min_rank = cfg.TR_MIN_RANK_SCORE
        self._w_ev      = cfg.TR_EV_WEIGHT
        self._w_score   = cfg.TR_TRADE_SCORE_WEIGHT
        self._w_regime  = cfg.TR_REGIME_WEIGHT
        self._w_history = cfg.TR_HISTORY_WEIGHT
        logger.info(
            f"[TRADE-RANKER] Phase 7 activated | "
            f"min_rank={self.min_rank} "
            f"weights(ev={self._w_ev} score={self._w_score} "
            f"regime={self._w_regime} history={self._w_history})"
        )

    def _normalise_ev(self, ev: float) -> float:
        """Map EV to [0, 1]: negative → 0, clamp at EVC_HIGH_THRESHOLD ceiling."""
        if ev <= 0:
            return 0.0
        # Ramp 0→1 as EV goes from 0 to 3× HIGH_THRESHOLD
        ceiling = cfg.EVC_HIGH_THRESHOLD * 3.0
        return min(ev / ceiling, 1.0)

    def rank(
        self,
        ev:            float,
        trade_score:   float,
        regime:        str,
        strategy:      str,
        history_score: Optional[float] = None,
    ) -> RankResult:
        """
        Compute and return a RankResult. ok=False → trade must be rejected.

        Args:
            ev:            Expected Value from EVEngine (USDT / unit risk)
            trade_score:   Composite score from AdaptiveScorer (0–1)
            regime:        Market regime string
            strategy:      Strategy name
            history_score: Optional [0, 1] from EdgeMemoryEngine. Defaults to
                           neutral 0.5 when not available.
        """
        # Phase 7B: hard reject any trade with strictly negative EV
        if ev < 0:
            reason = f"NEGATIVE_EV({ev:.4f})"
            logger.debug(f"[TRADE-RANKER] {reason}")
            return RankResult(
                ok=False, rank_score=0.0,
                ev_component=0.0, score_component=0.0,
                regime_component=0.0, history_component=0.0,
                reason=reason,
            )

        c_ev     = self._normalise_ev(ev)
        c_score  = max(0.0, min(trade_score, 1.0))
        c_regime = _regime_fit(regime, strategy)
        c_hist   = max(0.0, min(history_score if history_score is not None else 0.5, 1.0))

        rank_score = round(
            c_ev     * self._w_ev
            + c_score  * self._w_score
            + c_regime * self._w_regime
            + c_hist   * self._w_history,
            4,
        )

        if rank_score < self.min_rank:
            reason = (
                f"RANK_REJECT({rank_score:.3f}<{self.min_rank}) "
                f"ev={c_ev:.3f} score={c_score:.3f} "
                f"regime={c_regime:.3f} hist={c_hist:.3f}"
            )
            logger.debug(f"[TRADE-RANKER] {reason}")
            return RankResult(
                ok=False, rank_score=rank_score,
                ev_component=c_ev, score_component=c_score,
                regime_component=c_regime, history_component=c_hist,
                reason=reason,
            )

        logger.debug(
            f"[TRADE-RANKER] PASS rank={rank_score:.3f} "
            f"ev={c_ev:.3f} score={c_score:.3f} "
            f"regime={c_regime:.3f} hist={c_hist:.3f} "
            f"strategy={strategy} regime={regime}"
        )
        return RankResult(
            ok=True, rank_score=rank_score,
            ev_component=c_ev, score_component=c_score,
            regime_component=c_regime, history_component=c_hist,
        )

    def summary(self) -> dict:
        return {
            "min_rank_score": self.min_rank,
            "weights": {
                "ev":      self._w_ev,
                "score":   self._w_score,
                "regime":  self._w_regime,
                "history": self._w_history,
            },
            "module": "TRADE_RANKER",
            "phase":  7,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
trade_ranker = TradeRanker()


# ── FTD-008: Multi-signal ranking helper ─────────────────────────────────────

def rank_trades(signals: list) -> list:
    """
    Sort a list of signal objects by quality in descending order.
    Primary key: score, secondary: ev, tertiary: rr.

    Each signal must expose .score, .ev, and .rr attributes.
    Returns a new sorted list — caller should execute only signals[0].

    Usage:
        ranked = rank_trades(valid_signals)
        execute(ranked[0])
    """
    return sorted(
        signals,
        key=lambda s: (
            getattr(s, "score", 0.0),
            getattr(s, "ev",    0.0),
            getattr(s, "rr",    0.0),
        ),
        reverse=True,
    )

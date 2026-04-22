"""
EOW Quant Engine — FTD-008: Edge Filter (Primary Hard Gate)
Rejects any signal that fails the minimum score + RR threshold.

Rule (non-negotiable):
  score < MIN_TRADE_SCORE  →  BLOCK
  rr    < MIN_RR_RATIO     →  BLOCK

Both must pass for a trade to enter the pipeline.
This is the first gate — cheap, stateless, runs before EV / ranking.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class EdgeFilterResult:
    ok:     bool
    reason: str = ""


def has_minimum_edge(signal) -> bool:
    """
    Returns True only when the signal clears both hard thresholds.
    `signal` must expose .score (float 0–1) and .rr (float ≥ 0).
    """
    score_ok = signal.score >= cfg.MIN_TRADE_SCORE
    rr_ok    = signal.rr    >= cfg.MIN_RR_RATIO

    if not score_ok or not rr_ok:
        logger.debug(
            f"[EDGE-BLOCK] score={signal.score:.3f}(min={cfg.MIN_TRADE_SCORE}) "
            f"rr={signal.rr:.2f}(min={cfg.MIN_RR_RATIO})"
        )
        return False

    return True


def check_edge(signal) -> EdgeFilterResult:
    """
    Structured variant — returns EdgeFilterResult for gate-log compatibility.
    Prefer has_minimum_edge() for simple boolean gates.
    """
    score_ok = signal.score >= cfg.MIN_TRADE_SCORE
    rr_ok    = signal.rr    >= cfg.MIN_RR_RATIO

    if not score_ok:
        return EdgeFilterResult(
            ok=False,
            reason=f"SCORE_BELOW_MIN({signal.score:.3f}<{cfg.MIN_TRADE_SCORE})",
        )
    if not rr_ok:
        return EdgeFilterResult(
            ok=False,
            reason=f"RR_BELOW_MIN({signal.rr:.2f}<{cfg.MIN_RR_RATIO})",
        )

    return EdgeFilterResult(ok=True, reason="EDGE_PASS")

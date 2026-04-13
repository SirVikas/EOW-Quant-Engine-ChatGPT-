"""
EOW Quant Engine — Deployability Engine  (FTD-REF-MASTER-001)
Standalone weighted deployability scorer.

Score formula (0–100):
  0.30 × sharpe_norm  +
  0.25 × sortino_norm +
  0.20 × win_rate     +
  0.15 × risk_ctrl    +
  0.10 × dd_inverse

Status tiers:
  ≥ 85  → READY
  60–84 → IMPROVING
  < 60  → NOT_READY

Hard block conditions (cap score at 0):
  Sharpe < 1.0 AND trades ≥ MIN_TRADES
  Drawdown > 20%
  Risk-of-Ruin > 10%

Insufficient data:
  trades < MIN_TRADES → returns status="INSUFFICIENT_DATA", score=0
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List


# ── Constants ─────────────────────────────────────────────────────────────────
MIN_TRADES         = 50     # minimum trades before scoring is meaningful
SHARPE_TARGET      = 2.0   # sharpe normalised against this ceiling
SORTINO_TARGET     = 3.0   # sortino normalised against this ceiling
MAX_DD_BLOCK       = 0.20  # drawdown > 20% → hard block
MAX_RUIN_BLOCK     = 0.10  # risk-of-ruin > 10% → hard block
MIN_SHARPE_DEPLOY  = 1.0   # sharpe < 1.0 is a block condition

STATUS_READY      = "READY"
STATUS_IMPROVING  = "IMPROVING"
STATUS_NOT_READY  = "NOT_READY"
STATUS_INSUF_DATA = "INSUFFICIENT_DATA"
STATUS_BLOCKED    = "BLOCKED"


@dataclass
class DeployabilityResult:
    score:          float   # 0–100
    status:         str     # READY / IMPROVING / NOT_READY / INSUFFICIENT_DATA / BLOCKED
    block_reason:   str     # populated when BLOCKED
    sharpe_norm:    float
    sortino_norm:   float
    win_rate_score: float
    risk_ctrl_score: float
    dd_inverse:     float
    n_trades:       int


class DeployabilityEngine:
    """
    Stateless scorer. Call compute() with current session metrics.
    """

    def compute(
        self,
        trades:       int,
        sharpe:       float,
        sortino:      float,
        win_rate:     float,     # 0.0 – 1.0
        max_drawdown: float,     # 0.0 – 1.0 (fraction, e.g. 0.12 = 12%)
        risk_of_ruin: float,     # 0.0 – 1.0
        avg_r:        float,     # average R-multiple per trade
    ) -> DeployabilityResult:
        """
        Compute the deployability score from session metrics.
        Returns a DeployabilityResult with score, status, and per-component breakdown.
        """
        # ── Insufficient data ─────────────────────────────────────────────────
        if trades < MIN_TRADES:
            return DeployabilityResult(
                score=0, status=STATUS_INSUF_DATA,
                block_reason=f"INSUFFICIENT_TRADES({trades}<{MIN_TRADES})",
                sharpe_norm=0, sortino_norm=0, win_rate_score=0,
                risk_ctrl_score=0, dd_inverse=0, n_trades=trades,
            )

        # ── Hard block conditions ─────────────────────────────────────────────
        block_reason = ""
        if sharpe < MIN_SHARPE_DEPLOY:
            block_reason = f"LOW_SHARPE({sharpe:.2f}<{MIN_SHARPE_DEPLOY})"
        elif max_drawdown > MAX_DD_BLOCK:
            block_reason = f"HIGH_DD({max_drawdown:.1%}>{MAX_DD_BLOCK:.0%})"
        elif risk_of_ruin > MAX_RUIN_BLOCK:
            block_reason = f"HIGH_ROR({risk_of_ruin:.1%}>{MAX_RUIN_BLOCK:.0%})"

        if block_reason:
            return DeployabilityResult(
                score=0, status=STATUS_BLOCKED, block_reason=block_reason,
                sharpe_norm=0, sortino_norm=0, win_rate_score=0,
                risk_ctrl_score=0, dd_inverse=0, n_trades=trades,
            )

        # ── Component scores ──────────────────────────────────────────────────
        sharpe_norm  = min(1.0, max(0.0, sharpe  / SHARPE_TARGET))
        sortino_norm = min(1.0, max(0.0, sortino / SORTINO_TARGET))
        wr_score     = min(1.0, max(0.0, win_rate))
        # Risk control: penalise high drawdown; 0 DD = perfect score
        risk_ctrl    = max(0.0, 1.0 - max_drawdown / MAX_DD_BLOCK)
        # Drawdown inverse: lower DD = higher score
        dd_inv       = max(0.0, 1.0 - max_drawdown / MAX_DD_BLOCK)

        raw = (
            0.30 * sharpe_norm  +
            0.25 * sortino_norm +
            0.20 * wr_score     +
            0.15 * risk_ctrl    +
            0.10 * dd_inv
        )
        score = round(raw * 100, 1)

        # ── Status tier ───────────────────────────────────────────────────────
        if score >= 85:
            status = STATUS_READY
        elif score >= 60:
            status = STATUS_IMPROVING
        else:
            status = STATUS_NOT_READY

        return DeployabilityResult(
            score=score, status=status, block_reason="",
            sharpe_norm=round(sharpe_norm, 3),
            sortino_norm=round(sortino_norm, 3),
            win_rate_score=round(wr_score, 3),
            risk_ctrl_score=round(risk_ctrl, 3),
            dd_inverse=round(dd_inv, 3),
            n_trades=trades,
        )

    def to_dict(self, result: DeployabilityResult) -> dict:
        return {
            "score":          result.score,
            "status":         result.status,
            "block_reason":   result.block_reason,
            "n_trades":       result.n_trades,
            "components": {
                "sharpe_norm":      result.sharpe_norm,
                "sortino_norm":     result.sortino_norm,
                "win_rate_score":   result.win_rate_score,
                "risk_ctrl_score":  result.risk_ctrl_score,
                "dd_inverse":       result.dd_inverse,
            },
            "thresholds": {
                "min_trades":      MIN_TRADES,
                "min_sharpe":      MIN_SHARPE_DEPLOY,
                "max_drawdown":    f"{MAX_DD_BLOCK:.0%}",
                "max_ruin":        f"{MAX_RUIN_BLOCK:.0%}",
                "ready_at":        85,
                "improving_at":    60,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
deployability_engine = DeployabilityEngine()

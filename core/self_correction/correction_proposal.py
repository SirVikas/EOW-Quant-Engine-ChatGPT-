"""
FTD-029 — Correction Proposal Generator

Diagnoses current system state and proposes bounded parameter adjustments.
Respects HARD_LIMITS (Q14) and confidence-scaled change magnitude (Q3).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import cfg

# ── Hard Limits — NEVER auto-changed (Q14) ───────────────────────────────────
HARD_LIMITS: Dict[str, Any] = {
    "MAX_DRAWDOWN_HALT":     cfg.MAX_DRAWDOWN_HALT,   # absolute DD halt — immutable
    "MAX_LEVERAGE_CAP":      3.0,                      # max exposure / equity ratio — immutable
    "KILL_SWITCH_THRESHOLD": 0.20,                     # emergency stop threshold — immutable
    "MIN_EQUITY_FLOOR":      0.50,                     # equity must never drop below 50% initial — immutable
    "MAX_TRADES_PER_DAY":    cfg.MAX_TRADES_PER_DAY,  # daily trade cap — immutable
    "AUTH_ENABLED":          cfg.AUTH_ENABLED,         # auth config — immutable
}

# ── Tunable parameter catalogue (Q1: scope A+C+D) ────────────────────────────
# Each entry: param_name → (min_value, max_value, description)
TUNABLE_PARAMS: Dict[str, tuple] = {
    # Signal logic tuning (C)
    "P7B_PERF_WIN_THRESHOLD":   (0.55, 0.75,  "Win-rate threshold for EV performance boost"),
    "P7B_PERF_LOSS_THRESHOLD":  (0.30, 0.50,  "Win-rate threshold for EV performance penalty"),
    "P7B_EV_HIGH_THRESHOLD":    (0.05, 0.30,  "EV level for capital-commitment boost"),
    "P7B_EV_LOW_THRESHOLD":     (0.01, 0.10,  "EV level for capital-commitment penalty"),
    # Strategy parameters (A)
    "TR_EV_WEIGHT":             (0.30, 0.70,  "EV weight in trade-scorer composite"),
    "ADAPTIVE_LR":              (0.01, 0.15,  "Adaptive scorer learning rate"),
    "ADAPTIVE_MIN_WEIGHT":      (0.02, 0.10,  "Floor for any single factor weight"),
    "ADAPTIVE_MAX_WEIGHT":      (0.30, 0.50,  "Ceiling for any single factor weight"),
    # Portfolio allocation (D)
    "KELLY_FRACTION":           (0.10, 0.35,  "Kelly fraction for position sizing"),
    "EXPLORE_EV_FLOOR":         (0.30, 0.70,  "Max EV negative fraction for exploration"),
}

# ── Change magnitude bounds by confidence (Q3: dynamic) ──────────────────────
def max_change_pct(confidence_score: float) -> float:
    """Returns the maximum allowed parameter change percentage (0–1 fraction)."""
    if confidence_score >= 80:
        return 0.15
    if confidence_score >= 60:
        return 0.10
    return 0.05


@dataclass
class Proposal:
    param:       str
    current:     float
    proposed:    float
    delta_pct:   float
    reason:      str
    objective:   str    # what multi-objective metric this improves
    confidence:  float
    auto_apply:  bool   # True if delta_pct ≤ 5% (Q2: semi-auto)


class CorrectionProposal:
    """
    Diagnoses system state and generates bounded correction proposals.
    Never proposes changes to HARD_LIMITS parameters.
    """

    MODULE = "CORRECTION_PROPOSAL"
    PHASE  = "029"

    def generate(
        self,
        state: Dict[str, Any],
        current_params: Dict[str, float],
        confidence_score: float = 70.0,
    ) -> List[Proposal]:
        proposals: List[Proposal] = []
        max_pct = max_change_pct(confidence_score)

        win_rate    = state.get("win_rate", 0.0) or 0.0
        sharpe      = state.get("sharpe_ratio", 0.0) or 0.0
        drawdown    = state.get("current_drawdown_pct", 0.0) or 0.0
        total_pnl   = state.get("total_pnl", 0.0) or 0.0
        n_trades    = state.get("total_trades", 0) or 0

        # ── Diagnosis 1: Low win rate → tighten EV win threshold ─────────────
        if win_rate < 0.45 and n_trades >= 10:
            cur = current_params.get("P7B_PERF_WIN_THRESHOLD", cfg.P7B_PERF_WIN_THRESHOLD)
            delta = min(max_pct, 0.05) * cur
            proposed = min(cur + delta, TUNABLE_PARAMS["P7B_PERF_WIN_THRESHOLD"][1])
            if not math.isclose(proposed, cur):
                proposals.append(self._mk(
                    "P7B_PERF_WIN_THRESHOLD", cur, proposed, confidence_score,
                    f"win_rate={win_rate:.2%} < 0.45 — raise win threshold to demand higher quality",
                    "WIN_RATE",
                ))

        # ── Diagnosis 2: High win rate but negative PnL → increase EV weight ─
        if win_rate > 0.60 and total_pnl < 0 and n_trades >= 10:
            cur = current_params.get("TR_EV_WEIGHT", cfg.TR_EV_WEIGHT)
            delta = min(max_pct, 0.08) * cur
            proposed = min(cur + delta, TUNABLE_PARAMS["TR_EV_WEIGHT"][1])
            if not math.isclose(proposed, cur):
                proposals.append(self._mk(
                    "TR_EV_WEIGHT", cur, proposed, confidence_score,
                    f"win_rate={win_rate:.2%} but pnl<0 — increase EV weight to filter poor RR trades",
                    "RISK_ADJUSTED_RETURN",
                ))

        # ── Diagnosis 3: High drawdown → reduce Kelly fraction ────────────────
        if drawdown > 0.08:
            cur = current_params.get("KELLY_FRACTION", cfg.KELLY_FRACTION)
            delta = min(max_pct, 0.10) * cur
            proposed = max(cur - delta, TUNABLE_PARAMS["KELLY_FRACTION"][0])
            if not math.isclose(proposed, cur):
                proposals.append(self._mk(
                    "KELLY_FRACTION", cur, proposed, confidence_score,
                    f"drawdown={drawdown:.2%} > 8% — reduce Kelly fraction for capital protection",
                    "STABILITY",
                ))

        # ── Diagnosis 4: Negative Sharpe → increase learning rate ─────────────
        if sharpe is not None and sharpe < 0 and n_trades >= 10:
            cur = current_params.get("ADAPTIVE_LR", cfg.ADAPTIVE_LR)
            delta = min(max_pct, 0.08) * cur
            proposed = min(cur + delta, TUNABLE_PARAMS["ADAPTIVE_LR"][1])
            if not math.isclose(proposed, cur):
                proposals.append(self._mk(
                    "ADAPTIVE_LR", cur, proposed, confidence_score,
                    f"sharpe={sharpe:.3f} < 0 — increase learning rate to adapt faster",
                    "CONSISTENCY",
                ))

        # ── Diagnosis 5: Recovery from DD → restore Kelly ─────────────────────
        if drawdown < 0.03 and current_params.get("KELLY_FRACTION", cfg.KELLY_FRACTION) < 0.20:
            cur = current_params.get("KELLY_FRACTION", cfg.KELLY_FRACTION)
            delta = min(max_pct, 0.05) * 0.25   # target baseline = 0.25
            proposed = min(cur + delta, TUNABLE_PARAMS["KELLY_FRACTION"][1])
            if not math.isclose(proposed, cur):
                proposals.append(self._mk(
                    "KELLY_FRACTION", cur, proposed, confidence_score,
                    f"drawdown={drawdown:.2%} < 3% — gradually restore Kelly fraction",
                    "STABILITY",
                ))

        return proposals

    @staticmethod
    def _mk(
        param: str, current: float, proposed: float,
        confidence: float, reason: str, objective: str,
    ) -> Proposal:
        delta_pct = abs(proposed - current) / abs(current) if current else 0.0
        return Proposal(
            param=param,
            current=round(current, 6),
            proposed=round(proposed, 6),
            delta_pct=round(delta_pct, 4),
            reason=reason,
            objective=objective,
            confidence=confidence,
            auto_apply=delta_pct <= 0.05,   # Q2: ≤5% → auto
        )

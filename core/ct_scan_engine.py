"""
EOW Quant Engine — CT-Scan Engine  (FTD-REF-026)
Unified system health reporter aggregating signals from all subsystems.

Examines five dimensions and produces a structured health report:
  1. Profit Factor  — negative expectancy is the primary CRITICAL trigger
  2. Fee Ratio      — fees eating >20% of gross signals WARNING
  3. Strategy Diversity — only 1 active strategy signals WARNING
  4. Win Rate       — < 40% WR signals WARNING
  5. Regime Stability — passed in as a boolean flag

Output schema:
  {
    "system_health": "CRITICAL" | "WARNING" | "HEALTHY",
    "issues":  ["High fees", "Low profit factor", "Single strategy usage"],
    "action":  "Reduce trades + improve RR",
    "score":   0–100  (higher = healthier),
  }

Singleton: ct_scan_engine
"""
from __future__ import annotations

from typing import Dict, List

from loguru import logger


# ── Health levels ─────────────────────────────────────────────────────────────
HEALTH_CRITICAL = "CRITICAL"
HEALTH_WARNING  = "WARNING"
HEALTH_HEALTHY  = "HEALTHY"

# ── Scoring thresholds ────────────────────────────────────────────────────────
PF_CRITICAL_BELOW    = 1.0    # PF below this → CRITICAL (−35 pts)
FEE_RATIO_WARN       = 0.20   # fee / gross > 20% → WARNING (−20 pts)
WIN_RATE_WARN        = 0.40   # WR < 40% → WARNING (−20 pts)
SINGLE_STRAT_THRESH  = 1      # ≤ this many active strategies → issue (−15 pts)
REGIME_INSTAB_SCORE  = -10    # regime instability deduction
MIN_TRADES_FOR_EVAL  = 10     # need at least this many trades to evaluate


class CtScanEngine:
    """
    Stateless system health scanner — call scan() on demand.
    All inputs are passed in explicitly so the engine is pure and testable.
    """

    def scan(
        self,
        *,
        profit_factor:   float,
        fee_ratio:       float,         # total_fees / total_gross_profit (0.0–1.0+)
        strategy_usage:  Dict[str, float],   # {"TrendFollowing": 1.0, "MR": 0.0, …}
        win_rate:        float,         # 0.0–1.0
        regime_stable:   bool  = True,
        n_trades:        int   = 0,
    ) -> dict:
        """
        Run a full CT-Scan and return structured health report.

        Returns:
          {
            "system_health": str,
            "issues":        List[str],
            "action":        str,
            "score":         int (0–100),
          }
        """
        issues: List[str] = []
        score = 100

        # ── Gate 1: Profit Factor ─────────────────────────────────────────────
        if n_trades >= MIN_TRADES_FOR_EVAL and profit_factor < PF_CRITICAL_BELOW:
            issues.append(f"Low profit factor ({profit_factor:.2f} < 1.0)")
            score -= 35

        # ── Gate 2: Fee Drag ──────────────────────────────────────────────────
        if fee_ratio > FEE_RATIO_WARN:
            issues.append(f"High fees ({fee_ratio * 100:.1f}% of gross profit)")
            score -= 20

        # ── Gate 3: Strategy Diversity ────────────────────────────────────────
        active_strats = [s for s, u in strategy_usage.items() if u >= 0.05]
        if n_trades >= MIN_TRADES_FOR_EVAL and len(active_strats) <= SINGLE_STRAT_THRESH:
            dominant = active_strats[0] if active_strats else "none"
            issues.append(f"Single strategy usage ({dominant} dominates)")
            score -= 15

        # ── Gate 4: Win Rate ──────────────────────────────────────────────────
        if n_trades >= MIN_TRADES_FOR_EVAL and win_rate < WIN_RATE_WARN:
            issues.append(f"Low win rate ({win_rate * 100:.1f}% < 40%)")
            score -= 20

        # ── Gate 5: Regime Stability ──────────────────────────────────────────
        if not regime_stable:
            issues.append("Regime instability detected")
            score += REGIME_INSTAB_SCORE   # negative

        score = max(0, score)

        # ── Determine health level ────────────────────────────────────────────
        if score <= 45 or (
            n_trades >= MIN_TRADES_FOR_EVAL and profit_factor < PF_CRITICAL_BELOW
        ):
            health = HEALTH_CRITICAL
        elif issues:
            health = HEALTH_WARNING
        else:
            health = HEALTH_HEALTHY

        action = self._decide_action(issues, profit_factor, fee_ratio)

        result = {
            "system_health": health,
            "issues":        issues,
            "action":        action,
            "score":         score,
        }
        logger.debug(
            f"[CT-SCAN] health={health} score={score} issues={len(issues)}"
        )
        return result

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _decide_action(
        issues:        List[str],
        profit_factor: float,
        fee_ratio:     float,
    ) -> str:
        if not issues:
            return "System operating normally — no action required"
        parts: List[str] = []
        if profit_factor < PF_CRITICAL_BELOW:
            parts.append("Reduce trades + improve RR")
        if fee_ratio > FEE_RATIO_WARN:
            parts.append("Avoid small-notional trades to reduce fee drag")
        if not parts:
            parts.append("Monitor closely and review recent signals")
        return " | ".join(parts)


# ── Module-level singleton ────────────────────────────────────────────────────
ct_scan_engine = CtScanEngine()

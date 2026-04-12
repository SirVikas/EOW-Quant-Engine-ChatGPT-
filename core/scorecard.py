"""
EOW Quant Engine — Go-Live Scorecard  (Phase 3)

Produces an automated, structured Go / No-Go decision checklist before the
engine is permitted to escalate from PAPER → LIVE mode.

The scorecard verifies three pillars from the Phase 3 memorandum:

1. Security Verification
   • JWT auth must be enabled in LIVE mode.
   • All privileged endpoints require an access token (checked via config).

2. Expectancy Confidence
   • Every active strategy must have passed OOS validation (PF ≥ 1.0 on
     unseen data) before going live.
   • The overfitting ratio (train_pf / oos_pf) must be below the configured
     ceiling, confirming the edge is not curve-fitted.

3. Execution Parity
   • The post-cost average R-multiple must be positive, confirming that the
     simulated fill model (fees + slippage) produces genuine net-positive
     expectancy — not just gross edge that disappears after costs.
   • At least one successful promotion must appear in the recent audit log,
     confirming the genome cycle has run and validated at least one strategy.

Usage:
    from core.scorecard import compute_scorecard
    scorecard = compute_scorecard(genome_engine, cfg)
    if not scorecard.overall_pass:
        raise RuntimeError("Go-Live blocked: " + scorecard.summary())
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.genome_engine import GenomeEngine
    from config import EngineConfig


@dataclass
class ScorecardItem:
    name:      str
    passed:    bool
    value:     Any        # observed value
    threshold: Any        # required value / direction
    note:      str        # human-readable explanation


@dataclass
class GoLiveScorecard:
    ts:           int
    mode:         str
    overall_pass: bool
    items:        List[ScorecardItem] = field(default_factory=list)

    def summary(self) -> str:
        """One-line summary listing all failing checks."""
        failed = [i.name for i in self.items if not i.passed]
        if not failed:
            return "ALL CHECKS PASSED — GO"
        return "NO-GO: " + ", ".join(failed)

    def to_dict(self) -> dict:
        return {
            "ts":           self.ts,
            "mode":         self.mode,
            "overall_pass": self.overall_pass,
            "summary":      self.summary(),
            "items": [
                {
                    "name":      i.name,
                    "passed":    i.passed,
                    "value":     i.value,
                    "threshold": i.threshold,
                    "note":      i.note,
                }
                for i in self.items
            ],
        }


# ── Scorecard Computation ────────────────────────────────────────────────────

def compute_scorecard(genome: "GenomeEngine", config: "EngineConfig") -> GoLiveScorecard:
    """
    Evaluate all Go-Live gates and return a GoLiveScorecard.

    Parameters
    ----------
    genome : GenomeEngine
        Live genome engine instance (must have run at least one evolution cycle
        for the scorecard to be meaningful).
    config : EngineConfig
        Engine configuration singleton.
    """
    mode  = config.TRADE_MODE
    items: List[ScorecardItem] = []

    # ── Pillar 1: Security ────────────────────────────────────────────────────

    auth_ok = config.AUTH_ENABLED
    items.append(ScorecardItem(
        name="security_auth_enabled",
        passed=auth_ok,
        value=auth_ok,
        threshold=True,
        note="AUTH_ENABLED must be True before switching to LIVE mode.",
    ))

    api_keys_set = bool(config.CONTROL_API_KEYS.strip())
    items.append(ScorecardItem(
        name="security_api_keys_configured",
        passed=api_keys_set,
        value="<configured>" if api_keys_set else "<empty>",
        threshold="<configured>",
        note="CONTROL_API_KEYS must contain at least one token:role pair.",
    ))

    # ── Pillar 2: Expectancy Confidence (OOS + overfitting) ───────────────────

    _STRATEGY_TYPES = ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]

    for st in _STRATEGY_TYPES:
        m = genome.active_metrics.get(st)

        if m is None:
            items.append(ScorecardItem(
                name=f"{st}_calibrated",
                passed=False,
                value="not_calibrated",
                threshold="calibrated",
                note=f"{st}: genome has not yet promoted a validated candidate.",
            ))
            continue

        # OOS profit factor
        oos_ok = m.oos_pf >= config.GENOME_OOS_MIN_PF
        items.append(ScorecardItem(
            name=f"{st}_oos_pf",
            passed=oos_ok,
            value=round(m.oos_pf, 3),
            threshold=config.GENOME_OOS_MIN_PF,
            note=f"{st}: OOS profit factor must be ≥ {config.GENOME_OOS_MIN_PF}.",
        ))

        # Overfitting ratio
        if m.oos_pf > 0.0:
            overfit_ratio = round(m.profit_factor / m.oos_pf, 2)
        else:
            overfit_ratio = 999.0
        overfit_ok = overfit_ratio <= config.GENOME_OVERFITTING_MAX_RATIO
        items.append(ScorecardItem(
            name=f"{st}_overfit_ratio",
            passed=overfit_ok,
            value=overfit_ratio,
            threshold=f"≤ {config.GENOME_OVERFITTING_MAX_RATIO}",
            note=(
                f"{st}: train_pf/oos_pf ratio must be ≤ "
                f"{config.GENOME_OVERFITTING_MAX_RATIO} (curve-fit guard)."
            ),
        ))

    # ── Pillar 3: Execution Parity ────────────────────────────────────────────

    for st in _STRATEGY_TYPES:
        m = genome.active_metrics.get(st)
        if m is None:
            continue

        # Average R-multiple (post-fee, post-slippage)
        r_ok = m.avg_r_multiple >= config.GENOME_MIN_AVG_R
        items.append(ScorecardItem(
            name=f"{st}_avg_r_multiple",
            passed=r_ok,
            value=round(m.avg_r_multiple, 3),
            threshold=f"≥ {config.GENOME_MIN_AVG_R}",
            note=(
                f"{st}: post-cost average R-multiple must be ≥ "
                f"{config.GENOME_MIN_AVG_R} per trade."
            ),
        ))

        # Cost drag — informational (warn above 15 %)
        cost_ok = m.cost_drag_pct <= 15.0
        items.append(ScorecardItem(
            name=f"{st}_cost_drag_pct",
            passed=cost_ok,
            value=round(m.cost_drag_pct, 2),
            threshold="≤ 15.0%",
            note=(
                f"{st}: fee+slippage drag on gross PnL should stay below 15 %. "
                f"Above this threshold, review the fill model assumptions."
            ),
        ))

    # Recent promotion audit (confirms genome cycle is active and healthy)
    recent_promotions = [
        p for p in genome.promotion_log[-20:]
        if p.decision == "PROMOTED"
    ]
    promotion_ok = len(recent_promotions) > 0
    items.append(ScorecardItem(
        name="genome_recent_promotion",
        passed=promotion_ok,
        value=len(recent_promotions),
        threshold=">= 1",
        note=(
            "At least one PROMOTED event must appear in the last 20 promotion "
            "log entries — confirms the genome cycle is running and healthy."
        ),
    ))

    overall = all(i.passed for i in items)

    return GoLiveScorecard(
        ts=int(time.time() * 1000),
        mode=mode,
        overall_pass=overall,
        items=items,
    )

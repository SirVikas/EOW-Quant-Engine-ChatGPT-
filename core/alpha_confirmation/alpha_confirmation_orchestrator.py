"""
I.7 Alpha Confirmation Orchestrator.

Final synthesis of I.1–I.6.  Lineage format: ALPHA-{ts_ms}-{sha256[:16]}

Tiers:
  CONFIRMED   ≥ 85  — strong statistical evidence of real edge
  CANDIDATE   ≥ 65  — promising evidence, more data / OOS needed
  DEVELOPING  ≥ 40  — early signals present, not certifiable yet
  UNPROVEN    < 40  — insufficient or contradictory evidence

CONSTITUTIONAL NOTICE:
  CONFIRMED does NOT authorize live trading.
  It means the data supports beginning human due diligence.
  live_deployment_authorized is always False and cannot be set otherwise.

Score breakdown (100 total):
  I.1 Statistical significance  +25
  I.2 OOS validation            +20
  I.3 Fee survival              +20
  I.4 Regime robustness         +20
  I.5 Drawdown tolerance        +15

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

from core.alpha_confirmation.statistical_significance_engine import compute_statistical_significance
from core.alpha_confirmation.oos_validation_engine           import compute_oos_validation
from core.alpha_confirmation.fee_survival_engine             import compute_fee_survival
from core.alpha_confirmation.regime_robustness_engine        import compute_regime_robustness
from core.alpha_confirmation.drawdown_tolerance_engine       import compute_drawdown_tolerance
from core.alpha_confirmation.live_readiness_gate             import compute_live_readiness

_STAT_SCORES  = {"PROVEN": 25,               "INDICATIVE": 16,         "INSUFFICIENT_EVIDENCE": 7,  "NO_EDGE": 0}
_OOS_SCORES   = {"OOS_CONSISTENT": 20,       "MINOR_DEGRADATION": 13,  "SIGNIFICANT_DEGRADATION": 5,"OOS_FAILURE": 0}
_FEE_SCORES   = {"FEE_CERTIFIED": 20,        "MARGINAL": 12,           "FEE_ERODED": 4,             "FEE_DESTROYED": 0}
_REG_SCORES   = {"ROBUST": 20,               "ADEQUATE": 13,           "CONCENTRATED": 6,           "FRAGILE": 0}
_DD_SCORES    = {"DEPLOYMENT_READY": 15,     "BORDERLINE": 9,          "EXCESSIVE_DRAWDOWN": 3,     "DISQUALIFYING": 0}


def run_alpha_confirmation(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        i1 = compute_statistical_significance(trades)
        i2 = compute_oos_validation(trades)
        i3 = compute_fee_survival(trades)
        i4 = compute_regime_robustness(trades)
        i5 = compute_drawdown_tolerance(trades)
        i6 = compute_live_readiness([i1, i2, i3, i4, i5])

        score = (
            _STAT_SCORES.get(i1.get("state", "NO_EDGE"),          0) +
            _OOS_SCORES.get( i2.get("state", "OOS_FAILURE"),       0) +
            _FEE_SCORES.get( i3.get("state", "FEE_DESTROYED"),     0) +
            _REG_SCORES.get( i4.get("state", "FRAGILE"),           0) +
            _DD_SCORES.get(  i5.get("state", "DISQUALIFYING"),     0)
        )

        tier = (
            "CONFIRMED"  if score >= 85 else
            "CANDIDATE"  if score >= 65 else
            "DEVELOPING" if score >= 40 else
            "UNPROVEN"
        )

        payload    = f"ALPHA|{ts_ms}|{score}|{tier}"
        lineage_id = "ALPHA-" + str(ts_ms) + "-" + hashlib.sha256(payload.encode()).hexdigest()[:16]

        gate_status = i6.get("gate_status", "BLOCKED")
        blocking    = i6.get("blocking_reasons", [])

        return {
            "engine":               "I.7_ALPHA_CONFIRMATION",
            "lineage_id":           lineage_id,
            "alpha_score":          score,
            "alpha_tier":           tier,
            "gate_status":          gate_status,
            "blocking_reasons":     blocking,
            "trade_count":          len(trades),
            "sub_engine_states": {
                "i1_statistical":   i1.get("state"),
                "i2_oos":           i2.get("state"),
                "i3_fee_survival":  i3.get("state"),
                "i4_regime":        i4.get("state"),
                "i5_drawdown":      i5.get("state"),
                "i6_gate":          gate_status,
            },
            "sub_engine_scores": {
                "statistical_score":  _STAT_SCORES.get(i1.get("state", "NO_EDGE"), 0),
                "oos_score":          _OOS_SCORES.get( i2.get("state", "OOS_FAILURE"), 0),
                "fee_score":          _FEE_SCORES.get( i3.get("state", "FEE_DESTROYED"), 0),
                "regime_score":       _REG_SCORES.get( i4.get("state", "FRAGILE"), 0),
                "drawdown_score":     _DD_SCORES.get(  i5.get("state", "DISQUALIFYING"), 0),
            },
            # Constitutional invariants — immutable
            "live_deployment_authorized":  False,
            "human_confirmation_required": True,
            "diagnostic_only":             True,
            "auto_authorized":             False,
            "lineage_preserved":           True,
        }
    except Exception as exc:
        return {
            "engine": "I.7_ALPHA_CONFIRMATION", "alpha_tier": "UNPROVEN",
            "alpha_score": 0, "gate_status": "BLOCKED",
            "error": str(exc),
            "live_deployment_authorized": False, "human_confirmation_required": True,
            "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
        }


def get_alpha_health() -> dict:
    """Boot-time health check — no trade data required."""
    return {
        "subsystem":  "alpha_confirmation",
        "phase":      "I",
        "status":     "operational",
        "engines":    ["I.1", "I.2", "I.3", "I.4", "I.5", "I.6", "I.7"],
        "endpoints":  [
            "/api/alpha-confirmation/statistics",
            "/api/alpha-confirmation/oos",
            "/api/alpha-confirmation/fee-survival",
            "/api/alpha-confirmation/regime-robustness",
            "/api/alpha-confirmation/drawdown-tolerance",
            "/api/alpha-confirmation/gate",
            "/api/alpha-confirmation/orchestration",
        ],
        "live_deployment_authorized": False,
    }

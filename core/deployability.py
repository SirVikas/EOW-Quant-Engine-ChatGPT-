"""
EOW Quant Engine — Deployability Engine  (FTD-REF-023 upgraded)
Standalone weighted deployability scorer.

Score formula (0–100):
  0.30 × sharpe_norm  +
  0.25 × sortino_norm +
  0.20 × win_rate     +
  0.15 × risk_ctrl    +
  0.10 × dd_inverse

FTD-REF-023 additions:
  Warmup mode  — trades < WARMUP_TRADES: relax hard blocks, use warmup scoring
  Consistency  — if win_rate ≥ CONSISTENCY_THRESH & trades ≥ 20: +10 bonus

Status tiers:
  ≥ 85  → READY
  60–84 → IMPROVING
  < 60  → NOT_READY

Hard block conditions (full scoring only, bypassed in warmup):
  Sharpe < 1.0 AND trades ≥ MIN_TRADES
  Drawdown > 20%
  Risk-of-Ruin > 10%
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Constants ─────────────────────────────────────────────────────────────────
MIN_TRADES          = 50     # full scoring requires this many trades
WARMUP_TRADES       = 30     # below this: warmup mode (relaxed)
SHARPE_TARGET       = 2.0
SORTINO_TARGET      = 3.0
MAX_DD_BLOCK        = 0.20
MAX_RUIN_BLOCK      = 0.10
MIN_SHARPE_DEPLOY   = 1.0

CONSISTENCY_THRESH  = 0.55   # win_rate ≥ 55% → consistency bonus
CONSISTENCY_BONUS   = 10.0   # points added to final score

STATUS_READY        = "READY"
STATUS_IMPROVING    = "IMPROVING"
STATUS_NOT_READY    = "NOT_READY"
STATUS_INSUF_DATA   = "INSUFFICIENT_DATA"
STATUS_BLOCKED      = "BLOCKED"
STATUS_WARMUP       = "WARMUP"


@dataclass
class DeployabilityResult:
    score:           float
    status:          str
    block_reason:    str
    sharpe_norm:     float
    sortino_norm:    float
    win_rate_score:  float
    risk_ctrl_score: float
    dd_inverse:      float
    n_trades:        int
    consistency_bonus: float = 0.0
    warmup_mode:     bool   = False


class DeployabilityEngine:
    """Stateless scorer. Call compute() with current session metrics."""

    def compute(
        self,
        trades:       int,
        sharpe:       float,
        sortino:      float,
        win_rate:     float,
        max_drawdown: float,
        risk_of_ruin: float,
        avg_r:        float,
    ) -> DeployabilityResult:

        # ── Warmup mode (< WARMUP_TRADES) ────────────────────────────────────
        if trades < WARMUP_TRADES:
            return self._warmup_score(trades, win_rate, max_drawdown, avg_r)

        # ── Insufficient data (WARMUP_TRADES ≤ trades < MIN_TRADES) ──────────
        if trades < MIN_TRADES:
            # Partial scoring — no hard blocks, capped at IMPROVING
            result = self._compute_raw(trades, sharpe, sortino, win_rate,
                                       max_drawdown, risk_of_ruin)
            result.score  = min(result.score, 79.0)   # cap at IMPROVING tier
            result.status = STATUS_IMPROVING if result.score >= 60 else STATUS_NOT_READY
            return result

        # ── Hard blocks (full data) ───────────────────────────────────────────
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

        return self._compute_raw(trades, sharpe, sortino, win_rate,
                                 max_drawdown, risk_of_ruin)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _compute_raw(
        self, trades, sharpe, sortino, win_rate, max_drawdown, risk_of_ruin
    ) -> DeployabilityResult:
        sharpe_norm  = min(1.0, max(0.0, sharpe  / SHARPE_TARGET))
        sortino_norm = min(1.0, max(0.0, sortino / SORTINO_TARGET))
        wr_score     = min(1.0, max(0.0, win_rate))
        risk_ctrl    = max(0.0, 1.0 - max_drawdown / MAX_DD_BLOCK)
        dd_inv       = max(0.0, 1.0 - max_drawdown / MAX_DD_BLOCK)

        raw = (
            0.30 * sharpe_norm  +
            0.25 * sortino_norm +
            0.20 * wr_score     +
            0.15 * risk_ctrl    +
            0.10 * dd_inv
        )
        score = round(raw * 100, 1)

        # Consistency bonus (FTD-REF-023)
        bonus = 0.0
        if win_rate >= CONSISTENCY_THRESH and trades >= 20:
            bonus  = CONSISTENCY_BONUS
            score  = min(100.0, score + bonus)

        score  = round(score, 1)
        status = (STATUS_READY if score >= 85
                  else STATUS_IMPROVING if score >= 60
                  else STATUS_NOT_READY)

        return DeployabilityResult(
            score=score, status=status, block_reason="",
            sharpe_norm=round(sharpe_norm, 3),
            sortino_norm=round(sortino_norm, 3),
            win_rate_score=round(wr_score, 3),
            risk_ctrl_score=round(risk_ctrl, 3),
            dd_inverse=round(dd_inv, 3),
            n_trades=trades,
            consistency_bonus=bonus,
        )

    @staticmethod
    def _warmup_score(
        trades: int, win_rate: float, max_drawdown: float, avg_r: float
    ) -> DeployabilityResult:
        """
        Warmup scoring for trades < WARMUP_TRADES.
        Uses simplified formula; no hard blocks; capped at 60 (IMPROVING).
        """
        progress = trades / WARMUP_TRADES        # 0→1
        wr_s     = min(1.0, max(0.0, win_rate))
        dd_s     = max(0.0, 1.0 - max_drawdown / MAX_DD_BLOCK)
        r_s      = min(1.0, max(0.0, avg_r / 2.0))

        raw   = (0.40 * progress + 0.30 * wr_s + 0.20 * dd_s + 0.10 * r_s)
        score = round(raw * 60, 1)   # max 60 in warmup

        return DeployabilityResult(
            score=score, status=STATUS_WARMUP, block_reason="",
            sharpe_norm=0, sortino_norm=0,
            win_rate_score=round(wr_s, 3),
            risk_ctrl_score=round(dd_s, 3),
            dd_inverse=round(dd_s, 3),
            n_trades=trades,
            warmup_mode=True,
        )

    def to_dict(self, result: DeployabilityResult) -> dict:
        return {
            "score":            result.score,
            "status":           result.status,
            "block_reason":     result.block_reason,
            "n_trades":         result.n_trades,
            "warmup_mode":      result.warmup_mode,
            "consistency_bonus":result.consistency_bonus,
            "components": {
                "sharpe_norm":      result.sharpe_norm,
                "sortino_norm":     result.sortino_norm,
                "win_rate_score":   result.win_rate_score,
                "risk_ctrl_score":  result.risk_ctrl_score,
                "dd_inverse":       result.dd_inverse,
            },
            "thresholds": {
                "warmup_trades":   WARMUP_TRADES,
                "min_trades":      MIN_TRADES,
                "min_sharpe":      MIN_SHARPE_DEPLOY,
                "max_drawdown":    f"{MAX_DD_BLOCK:.0%}",
                "max_ruin":        f"{MAX_RUIN_BLOCK:.0%}",
                "consistency_at":  CONSISTENCY_THRESH,
                "ready_at":        85,
                "improving_at":    60,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
deployability_engine = DeployabilityEngine()


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 6.5 — Boot Deployability Engine (Data-Readiness Gate)
#
# Scores the system's OPERATIONAL readiness at boot and during runtime,
# combining four data-stability signals into a 0–100 readiness score:
#
#   Data Health     30%  — tick freshness, candle coverage, latency
#   Indicator Ready 25%  — all indicators warmed and free of NaN
#   WS Stability    25%  — reconnect count, latency, connection state
#   Risk Engine     20%  — drawdown + daily loss headroom
#
# Rule:
#   score < BDE_MIN_SCORE (70) → block_trading = True → activate safe mode
# ═══════════════════════════════════════════════════════════════════════════════

from dataclasses import dataclass as _dc


@_dc
class BootDeployabilityResult:
    score:              float     # 0–100 composite readiness
    ok:                 bool      # True → system ready to trade
    block_trading:      bool
    data_health_score:  float     # 0–100 component
    indicator_score:    float     # 0–100 component
    ws_stability_score: float     # 0–100 component
    risk_score:         float     # 0–100 component
    status:             str       # "READY" | "DEGRADED" | "BLOCKED"
    reason:             str = ""


class BootDeployabilityEngine:
    """
    Combines DataHealthMonitor, IndicatorValidator, WsStabilityEngine, and
    risk headroom into a single operational readiness score.

    Call evaluate() before every signal cycle. If ok=False, block new trades
    and activate SafeModeController.

    Args to evaluate():
        data_health_score:  0–100 from DataHealthMonitor.check().health_score
        indicator_score:    0–1 from IndicatorValidator.validate().score → ×100
        ws_stability_score: 0–100 from WsStabilityEngine.stability_score()
        current_drawdown:   current DD as fraction (0–1)
        daily_loss_pct:     today's loss as fraction of equity (0–1)
    """

    def __init__(self):
        from loguru import logger as _log
        from config import cfg as _cfg
        _log.info(
            f"[BOOT-DEPLOY] Phase 6.5 activated | "
            f"min_score={_cfg.BDE_MIN_SCORE} "
            f"weights(data={_cfg.BDE_DATA_HEALTH_WEIGHT} "
            f"ind={_cfg.BDE_INDICATOR_WEIGHT} "
            f"ws={_cfg.BDE_WS_STABILITY_WEIGHT} "
            f"risk={_cfg.BDE_RISK_ENGINE_WEIGHT})"
        )

    def evaluate(
        self,
        data_health_score:  float,   # 0–100
        indicator_score:    float,   # 0–1  (fraction of checks passed)
        ws_stability_score: float,   # 0–100
        current_drawdown:   float = 0.0,
        daily_loss_pct:     float = 0.0,
    ) -> BootDeployabilityResult:
        from loguru import logger as _log
        from config import cfg as _cfg

        # Normalise all to 0–100
        ind_100 = min(100.0, max(0.0, indicator_score * 100.0))
        dh_100  = min(100.0, max(0.0, data_health_score))
        ws_100  = min(100.0, max(0.0, ws_stability_score))

        # Risk score: penalise for drawdown and daily loss proximity to limits
        dd_headroom   = max(0.0, 1.0 - current_drawdown / max(_cfg.DD_STOP_AT, 1e-9))
        dl_headroom   = max(0.0, 1.0 - daily_loss_pct / max(_cfg.DAILY_RISK_CAP * 3, 1e-9))
        risk_100      = round(min(1.0, (dd_headroom * 0.6 + dl_headroom * 0.4)) * 100, 1)

        composite = (
            dh_100  * _cfg.BDE_DATA_HEALTH_WEIGHT
            + ind_100 * _cfg.BDE_INDICATOR_WEIGHT
            + ws_100  * _cfg.BDE_WS_STABILITY_WEIGHT
            + risk_100 * _cfg.BDE_RISK_ENGINE_WEIGHT
        )
        score = round(composite, 1)

        block_trading = score < _cfg.BDE_MIN_SCORE
        ok = not block_trading

        if score >= 85:
            status = "READY"
        elif score >= _cfg.BDE_MIN_SCORE:
            status = "DEGRADED"
        else:
            status = "BLOCKED"

        reason = ""
        if block_trading:
            parts = []
            if dh_100 < 60:
                parts.append(f"data_health={dh_100:.0f}")
            if ind_100 < 60:
                parts.append(f"indicators={ind_100:.0f}%")
            if ws_100 < 50:
                parts.append(f"ws_stability={ws_100:.0f}")
            if risk_100 < 50:
                parts.append(f"risk={risk_100:.0f}")
            reason = f"BOOT_DEPLOY_BLOCK({score:.1f}<{_cfg.BDE_MIN_SCORE}): {', '.join(parts)}"
            _log.warning(f"[BOOT-DEPLOY] {reason}")
        else:
            _log.debug(
                f"[BOOT-DEPLOY] {status} score={score:.1f} "
                f"data={dh_100:.0f} ind={ind_100:.0f} "
                f"ws={ws_100:.0f} risk={risk_100:.0f}"
            )

        return BootDeployabilityResult(
            score=score,
            ok=ok,
            block_trading=block_trading,
            data_health_score=dh_100,
            indicator_score=ind_100,
            ws_stability_score=ws_100,
            risk_score=risk_100,
            status=status,
            reason=reason,
        )

    def summary(self) -> dict:
        from config import cfg as _cfg
        return {
            "min_score":    _cfg.BDE_MIN_SCORE,
            "weights": {
                "data_health":   _cfg.BDE_DATA_HEALTH_WEIGHT,
                "indicator":     _cfg.BDE_INDICATOR_WEIGHT,
                "ws_stability":  _cfg.BDE_WS_STABILITY_WEIGHT,
                "risk_engine":   _cfg.BDE_RISK_ENGINE_WEIGHT,
            },
            "module": "BOOT_DEPLOYABILITY_ENGINE",
            "phase":  "6.5",
        }


# ── Phase 6.5 singleton ───────────────────────────────────────────────────────
boot_deployability_engine = BootDeployabilityEngine()

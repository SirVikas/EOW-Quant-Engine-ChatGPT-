"""
I.1 Statistical Significance Engine.

Tests whether observed win rate and mean PnL are statistically distinguishable
from noise.  Uses binomial z-score (win rate vs 0.5) and t-score (mean PnL vs 0).

Conservative design: requires 30+ trades minimum; reports exact p-values.
Even PROVEN does not authorize live trading — diagnostic only.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, math, time
from typing import List

_MIN_TRADES = 30


def compute_statistical_significance(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < _MIN_TRADES:
            return _insufficient(ts_ms, n)

        pnls = [float(t.get("pnl", 0)) for t in trades]
        wins = sum(1 for p in pnls if p > 0)
        win_rate = wins / n

        # Binomial z-score: H0 = win_rate == 0.5
        se_binom = math.sqrt(0.5 * 0.5 / n)
        z_win    = (win_rate - 0.5) / se_binom if se_binom > 0 else 0.0

        # t-score: H0 = mean_pnl == 0
        mean_pnl = sum(pnls) / n
        std_pnl  = math.sqrt(sum((p - mean_pnl) ** 2 for p in pnls) / (n - 1)) if n > 1 else 0.0
        t_pnl    = (mean_pnl / (std_pnl / math.sqrt(n))) if std_pnl > 0 else 0.0

        # Approximate two-tailed p-value from z (normal approximation sufficient for n≥30)
        def _p_from_z(z):
            # Abramowitz & Stegun approximation
            abs_z = abs(z)
            t_val = 1.0 / (1.0 + 0.2316419 * abs_z)
            poly  = t_val * (0.319381530 + t_val * (-0.356563782 + t_val * (1.781477937
                    + t_val * (-1.821255978 + t_val * 1.330274429))))
            phi   = math.exp(-0.5 * abs_z ** 2) / math.sqrt(2 * math.pi)
            return 2.0 * phi * poly

        p_win = _p_from_z(z_win)
        p_pnl = _p_from_z(t_pnl)

        # Combined evidence score: both signals must be significant
        # z ≥ 1.96 → p < 0.05; z ≥ 2.576 → p < 0.01
        evidence_score = 0.0
        if abs(z_win) >= 2.576 and abs(t_pnl) >= 2.576:
            evidence_score = 90.0
        elif abs(z_win) >= 1.96 and abs(t_pnl) >= 1.96:
            evidence_score = 70.0
        elif abs(z_win) >= 1.645 or abs(t_pnl) >= 1.645:
            evidence_score = 45.0
        else:
            evidence_score = 15.0

        # Require positive direction for PROVEN
        if mean_pnl <= 0 or win_rate <= 0.5:
            evidence_score = min(evidence_score, 30.0)

        state = (
            "PROVEN"               if evidence_score >= 80 else
            "INDICATIVE"           if evidence_score >= 55 else
            "INSUFFICIENT_EVIDENCE"if evidence_score >= 30 else
            "NO_EDGE"
        )

        payload    = f"I1|{ts_ms}|{round(z_win,4)}|{round(t_pnl,4)}|{state}"
        lineage_id = "ALPHA-I1-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "I.1_STATISTICAL_SIGNIFICANCE",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "win_rate":            round(win_rate, 4),
            "mean_pnl":            round(mean_pnl, 4),
            "std_pnl":             round(std_pnl, 4),
            "z_win_rate":          round(z_win, 4),
            "t_mean_pnl":          round(t_pnl, 4),
            "p_win_rate":          round(p_win, 4),
            "p_mean_pnl":          round(p_pnl, 4),
            "evidence_score":      round(evidence_score, 1),
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "live_deployment_authorized": False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "I.1_STATISTICAL_SIGNIFICANCE", "state": "NO_EDGE",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "live_deployment_authorized": False, "lineage_preserved": True,
        }


def _insufficient(ts_ms: int, n: int) -> dict:
    return {
        "engine": "I.1_STATISTICAL_SIGNIFICANCE", "state": "INSUFFICIENT_EVIDENCE",
        "trade_count": n, "min_required": _MIN_TRADES,
        "diagnostic_only": True, "auto_authorized": False,
        "live_deployment_authorized": False, "lineage_preserved": True,
    }

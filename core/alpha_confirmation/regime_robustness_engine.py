"""
I.4 Regime Robustness Engine.

Tests whether the edge holds across multiple distinct market regimes.
Concentration in a single regime = fragile, not certifiable for live.

Requires: at least 2 regimes with ≥10 trades each showing positive win rate.
A strategy that only works in TRENDING markets will fail in RANGING environments.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_MIN_REGIME_TRADES = 10
_MIN_REGIMES       = 2


def compute_regime_robustness(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < 20:
            return _insufficient(ts_ms, n)

        # Group by regime
        regime_buckets: dict[str, list] = {}
        for t in trades:
            regime = str(t.get("regime", t.get("market_regime", "UNKNOWN"))).upper()
            if not regime or regime == "NONE" or regime == "":
                regime = "UNKNOWN"
            regime_buckets.setdefault(regime, []).append(float(t.get("pnl", 0)))

        regime_stats = {}
        for regime, pnls in regime_buckets.items():
            if len(pnls) < 1:
                continue
            wins     = sum(1 for p in pnls if p > 0)
            win_rate = wins / len(pnls)
            mean_pnl = sum(pnls) / len(pnls)
            regime_stats[regime] = {
                "n": len(pnls), "win_rate": round(win_rate, 4),
                "mean_pnl": round(mean_pnl, 4),
                "profitable": win_rate > 0.5 and mean_pnl > 0,
            }

        # Qualifying regimes: ≥ min trades AND profitable
        qualifying = {r: s for r, s in regime_stats.items()
                      if s["n"] >= _MIN_REGIME_TRADES and s["profitable"]}

        n_qualifying = len(qualifying)
        n_regimes    = len(regime_stats)

        # Concentration: what fraction of trades in best regime?
        best_n = max((s["n"] for s in regime_stats.values()), default=0)
        concentration = best_n / n if n > 0 else 1.0

        state = (
            "ROBUST"      if n_qualifying >= 3 and concentration < 0.70 else
            "ADEQUATE"    if n_qualifying >= 2 and concentration < 0.85 else
            "CONCENTRATED"if n_qualifying >= 1                           else
            "FRAGILE"
        )

        payload    = f"I4|{ts_ms}|{n_qualifying}|{round(concentration,4)}|{state}"
        lineage_id = "ALPHA-I4-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "I.4_REGIME_ROBUSTNESS",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "regimes_observed":    n_regimes,
            "regimes_qualifying":  n_qualifying,
            "regime_stats":        regime_stats,
            "best_regime_concentration": round(concentration, 4),
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "live_deployment_authorized": False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "I.4_REGIME_ROBUSTNESS", "state": "FRAGILE",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "live_deployment_authorized": False, "lineage_preserved": True,
        }


def _insufficient(ts_ms: int, n: int) -> dict:
    return {
        "engine": "I.4_REGIME_ROBUSTNESS", "state": "FRAGILE",
        "trade_count": n, "min_required": 20,
        "diagnostic_only": True, "auto_authorized": False,
        "live_deployment_authorized": False, "lineage_preserved": True,
    }

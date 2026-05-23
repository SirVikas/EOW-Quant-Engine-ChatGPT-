"""
F.6 Discipline Cost Engine.

Quantifies the economic cost of behavioral biases:
 - Over-caution: too much capital preservation when conditions favour trading
 - Under-discipline: trading against adverse signals, eroding edge

Detected via comparing high-signal-quality vs low-signal-quality trade outcomes.
Signal quality is proxied by trade confidence if available, else by regime label.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_FAVOURABLE_REGIMES = {"TRENDING", "MOMENTUM", "BREAKOUT", "CONTINUATION"}


def compute_discipline_cost(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < 5:
            return _no_data(ts_ms, n)

        pnls = [float(t.get("pnl", 0)) for t in trades]

        # Partition by confidence or regime
        high_conf, low_conf = [], []
        for t in trades:
            conf    = float(t.get("confidence", t.get("signal_confidence", 0.0)))
            regime  = str(t.get("regime", t.get("market_regime", ""))).upper()
            pnl     = float(t.get("pnl", 0))
            if conf >= 0.6 or regime in _FAVOURABLE_REGIMES:
                high_conf.append(pnl)
            else:
                low_conf.append(pnl)

        # If we can't partition meaningfully, split chronologically
        if len(high_conf) < 2 or len(low_conf) < 2:
            mid       = n // 2
            high_conf = pnls[:mid]
            low_conf  = pnls[mid:]

        high_mean = sum(high_conf) / len(high_conf)
        low_mean  = sum(low_conf)  / len(low_conf)

        # Over-caution signal: high-confidence trades underperform expectation
        # Under-discipline signal: low-confidence trades erode gains
        cost_over_caution    = max(0.0, -high_mean)   # forfeit of positive edge
        cost_under_discipline = max(0.0, -low_mean)    # loss during weak signal

        total_cost = cost_over_caution + cost_under_discipline
        # Normalize cost as fraction of total absolute PnL traded
        abs_total = sum(abs(p) for p in pnls) or 1.0
        cost_ratio = total_cost / abs_total

        state = (
            "COST_MINIMAL"      if cost_ratio < 0.10 else
            "COST_MODERATE"     if cost_ratio < 0.25 else
            "COST_SIGNIFICANT"  if cost_ratio < 0.50 else
            "COST_SEVERE"
        )

        payload = f"EQ-F6|{ts_ms}|{round(cost_ratio, 4)}|{state}"
        lineage_id = "EQ-F6-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":               "F.6_DISCIPLINE_COST",
            "lineage_id":           lineage_id,
            "trade_count":          n,
            "high_signal_trades":   len(high_conf),
            "low_signal_trades":    len(low_conf),
            "high_signal_mean_pnl": round(high_mean, 4),
            "low_signal_mean_pnl":  round(low_mean, 4),
            "cost_over_caution":    round(cost_over_caution, 4),
            "cost_under_discipline":round(cost_under_discipline, 4),
            "cost_ratio":           round(cost_ratio, 4),
            "state":                state,
            "diagnostic_only":      True,
            "auto_authorized":      False,
            "lineage_preserved":    True,
        }
    except Exception as exc:
        return {
            "engine": "F.6_DISCIPLINE_COST", "state": "COST_SEVERE",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }


def _no_data(ts_ms: int, n: int) -> dict:
    return {
        "engine": "F.6_DISCIPLINE_COST", "state": "COST_MINIMAL",
        "trade_count": n, "insufficient_data": True,
        "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
    }

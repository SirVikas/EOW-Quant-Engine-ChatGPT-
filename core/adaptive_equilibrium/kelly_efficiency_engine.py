"""
F.1 Kelly Efficiency Engine.

Compares actual position sizing against Kelly-optimal fraction.
Measures how efficiently capital is risked relative to the mathematical edge.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_STATES = ("OPTIMAL", "ADEQUATE", "SUBOPTIMAL", "NEGLIGENT")


def compute_kelly_efficiency(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        wins  = [t for t in trades if float(t.get("pnl", 0)) > 0]
        loses = [t for t in trades if float(t.get("pnl", 0)) < 0]
        n     = len(trades)

        if n < 5:
            return _no_data(ts_ms, n)

        win_rate = len(wins) / n if n else 0.0
        avg_win  = sum(float(t["pnl"]) for t in wins)  / len(wins)  if wins  else 0.0
        avg_loss = sum(abs(float(t["pnl"])) for t in loses) / len(loses) if loses else 1.0

        # Discrete Kelly fraction: W - (1-W)/R  where R = avg_win / avg_loss
        R = avg_win / avg_loss if avg_loss > 0 else 0.0
        kelly_fraction = max(0.0, win_rate - (1.0 - win_rate) / R) if R > 0 else 0.0

        # Estimate actual risk fraction via pnl std / mean equity proxy
        pnls = [float(t.get("pnl", 0)) for t in trades]
        mean_pnl = sum(pnls) / n
        pnl_std  = (sum((p - mean_pnl) ** 2 for p in pnls) / n) ** 0.5

        # Normalized efficiency: how close actual volatility is to kelly-implied
        kelly_implied_vol = kelly_fraction * avg_loss if avg_loss > 0 else 0.0
        if kelly_implied_vol > 0 and pnl_std > 0:
            ratio = min(pnl_std, kelly_implied_vol) / max(pnl_std, kelly_implied_vol)
            efficiency_score = round(ratio * 100, 1)
        elif kelly_fraction == 0:
            efficiency_score = 0.0
        else:
            efficiency_score = 50.0

        state = (
            "OPTIMAL"    if efficiency_score >= 80 else
            "ADEQUATE"   if efficiency_score >= 60 else
            "SUBOPTIMAL" if efficiency_score >= 40 else
            "NEGLIGENT"
        )

        payload = f"EQ-F1|{ts_ms}|{round(kelly_fraction, 4)}|{round(efficiency_score, 1)}"
        lineage_id = "EQ-F1-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":             "F.1_KELLY_EFFICIENCY",
            "lineage_id":         lineage_id,
            "trade_count":        n,
            "win_rate":           round(win_rate, 4),
            "avg_win":            round(avg_win, 4),
            "avg_loss":           round(avg_loss, 4),
            "kelly_fraction":     round(kelly_fraction, 4),
            "efficiency_score":   efficiency_score,
            "state":              state,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "lineage_preserved":  True,
        }
    except Exception as exc:
        return {
            "engine": "F.1_KELLY_EFFICIENCY", "state": "NEGLIGENT",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }


def _no_data(ts_ms: int, n: int) -> dict:
    return {
        "engine": "F.1_KELLY_EFFICIENCY", "state": "NEGLIGENT",
        "trade_count": n, "insufficient_data": True,
        "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
    }

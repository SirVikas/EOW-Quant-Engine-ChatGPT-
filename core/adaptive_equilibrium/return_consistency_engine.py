"""
F.3 Return Consistency Engine.

Measures how consistent returns are across rolling windows and regimes.
Low consistency = high outcome variance independent of direction.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_WINDOW = 10


def compute_return_consistency(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < _WINDOW:
            return _no_data(ts_ms, n)

        pnls = [float(t.get("pnl", 0)) for t in trades]

        # Rolling window consistency scores
        window_scores = []
        for i in range(0, n - _WINDOW + 1, max(1, _WINDOW // 2)):
            w = pnls[i: i + _WINDOW]
            m = sum(w) / len(w)
            v = (sum((x - m) ** 2 for x in w) / len(w)) ** 0.5
            # Consistency ratio: |mean| / std — higher is more consistent
            score = abs(m) / v if v > 1e-9 else (10.0 if abs(m) > 0 else 0.0)
            window_scores.append(min(score, 10.0))

        avg_consistency = sum(window_scores) / len(window_scores) if window_scores else 0.0
        # Normalize to 0–100
        consistency_score = round(min(avg_consistency * 10.0, 100.0), 1)

        # Positive ratio: fraction of windows with positive mean
        positive_windows = sum(1 for w in range(0, n - _WINDOW + 1, max(1, _WINDOW // 2))
                               if sum(pnls[w: w + _WINDOW]) > 0)
        total_windows = len(window_scores)
        positive_ratio = positive_windows / total_windows if total_windows else 0.0

        # Streak detection: longest consecutive same-sign run
        max_streak = 1
        cur_streak = 1
        for i in range(1, n):
            if (pnls[i] >= 0) == (pnls[i - 1] >= 0):
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
            else:
                cur_streak = 1

        state = (
            "CONSISTENT" if consistency_score >= 60 else
            "ADEQUATE"   if consistency_score >= 35 else
            "VARIABLE"   if consistency_score >= 15 else
            "ERRATIC"
        )

        payload = f"EQ-F3|{ts_ms}|{round(consistency_score, 1)}|{round(positive_ratio, 4)}"
        lineage_id = "EQ-F3-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":             "F.3_RETURN_CONSISTENCY",
            "lineage_id":         lineage_id,
            "trade_count":        n,
            "consistency_score":  consistency_score,
            "positive_ratio":     round(positive_ratio, 4),
            "max_streak":         max_streak,
            "windows_evaluated":  total_windows,
            "state":              state,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "lineage_preserved":  True,
        }
    except Exception as exc:
        return {
            "engine": "F.3_RETURN_CONSISTENCY", "state": "ERRATIC",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }


def _no_data(ts_ms: int, n: int) -> dict:
    return {
        "engine": "F.3_RETURN_CONSISTENCY", "state": "ERRATIC",
        "trade_count": n, "insufficient_data": True,
        "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
    }

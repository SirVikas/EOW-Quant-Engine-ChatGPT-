"""Metrics normalization helpers for dashboard safety."""
from __future__ import annotations

import math
from typing import Iterable

from core.analytics import sharpe_ratio, sortino_ratio, calmar_ratio


def safe_value(value: float, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        f = float(value)
    except Exception:
        return default
    if math.isnan(f) or math.isinf(f):
        return default
    return f


def rolling_ratios(
    pnl_values: Iterable[float],
    initial_capital: float,
    max_drawdown_pct: float,
    window: int = 200,
) -> dict:
    vals = [safe_value(v, 0.0) for v in pnl_values]
    if window > 0:
        vals = vals[-window:]

    init = max(safe_value(initial_capital, 0.0), 1e-9)
    returns = [v / init for v in vals]

    return {
        "sharpe_ratio": round(safe_value(sharpe_ratio(returns), 0.0), 3),
        "sortino_ratio": round(safe_value(sortino_ratio(returns), 0.0), 3),
        "calmar_ratio": round(
            safe_value(calmar_ratio(vals, init, safe_value(max_drawdown_pct, 0.0)), 0.0),
            3,
        ),
    }

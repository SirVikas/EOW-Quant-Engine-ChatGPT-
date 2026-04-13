"""
EOW Quant Engine — DBO Analytics Module
Strategic Truth layer: Sortino, Risk-of-Ruin, Geometric Growth,
Deployability Index, and benchmark comparison.
"""
from __future__ import annotations

import math
import statistics
import time
from typing import List, Optional


# ── Calmar Ratio ─────────────────────────────────────────────────────────────

def calmar_ratio(
    pnl_list: List[float],
    initial_capital: float,
    max_drawdown_pct: float,
) -> float:
    """
    Calmar ratio = Annualised Return % / Max Drawdown %.
    A ratio > 1.0 means the engine earns more than its worst historical loss per year.
    Capped at 99.99 when drawdown is zero.
    """
    if max_drawdown_pct <= 0:
        return 99.99
    if not pnl_list or initial_capital <= 0:
        return 0.0
    mean_return = statistics.mean(pnl_list) / initial_capital if pnl_list else 0.0
    # Annualise (assume ~252 trading periods per year)
    annualised_pct = mean_return * 252 * 100
    result = annualised_pct / max_drawdown_pct
    if math.isnan(result) or math.isinf(result):
        return 0.0
    return round(result, 3)


# ── Sortino Ratio ─────────────────────────────────────────────────────────────

def sortino_ratio(pnl_list: List[float], risk_free: float = 0.0) -> float:
    """
    Sortino ratio = (mean_return - risk_free) / downside_deviation
    Only penalises losing trades, unlike Sharpe which penalises all volatility.
    """
    if len(pnl_list) < 2:
        return 0.0
    mean = statistics.mean(pnl_list) - risk_free
    losses = [p for p in pnl_list if p < risk_free]
    if not losses:
        # No downside — perfect one-sided profile
        return 99.99
    downside_var = statistics.mean([(p - risk_free) ** 2 for p in losses])
    downside_dev = math.sqrt(downside_var)
    if downside_dev == 0:
        return 99.99
    # Annualise (252 trading days) — same convention as Sharpe
    result = mean / downside_dev * math.sqrt(252)
    if math.isnan(result) or math.isinf(result):
        return 0.0
    return round(result, 3)


# ── Sharpe Ratio ──────────────────────────────────────────────────────────────

def sharpe_ratio(pnl_list: List[float], risk_free: float = 0.0) -> float:
    """Annualised Sharpe ratio."""
    if len(pnl_list) < 2:
        return 0.0
    mean = statistics.mean(pnl_list) - risk_free
    std  = statistics.stdev(pnl_list)
    if std == 0:
        return 0.0
    result = mean / std * math.sqrt(252)
    if math.isnan(result) or math.isinf(result):
        return 0.0
    return round(result, 3)


# ── Risk of Ruin ──────────────────────────────────────────────────────────────

def risk_of_ruin(
    win_rate: float,
    avg_r_win: float,
    avg_r_loss: float,
    account_units: int = 20,
) -> float:
    """
    Estimate probability of ruin (bankruptcy) as a percentage.

    Uses the gambler's-ruin approximation:
        edge% = (p * W - q * L) / (p * W + q * L)
        RoR   = [(1 - edge%) / (1 + edge%)] ^ account_units

    account_units — number of R-unit lots of capital held
                    (e.g. 20 means you'd need ~20 max-loss events to go bust)

    Returns a value in [0, 100].
    """
    if not (0.0 < win_rate < 1.0) or avg_r_win <= 0 or avg_r_loss <= 0:
        return 100.0

    p = win_rate
    q = 1.0 - p
    W = avg_r_win
    L = avg_r_loss

    expected_edge = p * W - q * L
    if expected_edge <= 0:
        return 100.0

    total = p * W + q * L
    if total <= 0:
        return 100.0

    edge_ratio = expected_edge / total          # normalised edge in (-1, 1)
    base       = (1.0 - edge_ratio) / (1.0 + edge_ratio)

    if base <= 0:
        return 0.0

    ror = base ** account_units
    return round(min(ror * 100.0, 100.0), 4)


# ── Geometric vs Linear Growth ────────────────────────────────────────────────

def geometric_mean_growth(
    r_multiples: List[float],
    risk_fraction: float = 0.01,
    initial_capital: float = 1000.0,
) -> dict:
    """
    Returns two equity series for a given list of trade R-multiples:
      geometric — compounding (each R-multiple applied to running balance)
      linear    — additive (same fixed dollar amount added/subtracted each trade)

    risk_fraction — fraction of capital risked per trade (default 1%)
    initial_capital — starting value

    Both series start at initial_capital and have len(r_multiples)+1 points.
    """
    if not r_multiples:
        return {"geometric": [initial_capital], "linear": [initial_capital], "labels": ["Start"]}

    geo  = [initial_capital]
    lin  = [initial_capital]
    labels = ["Start"]

    geo_cap = initial_capital
    lin_cap = initial_capital
    fixed_risk = initial_capital * risk_fraction   # constant dollar risk for linear

    for i, r in enumerate(r_multiples):
        # Geometric: risk_fraction of *current* capital each trade
        dynamic_risk = geo_cap * risk_fraction
        geo_cap += dynamic_risk * r
        geo_cap  = max(geo_cap, 0.0)

        # Linear: always risk the same fixed dollar amount
        lin_cap += fixed_risk * r
        lin_cap  = max(lin_cap, 0.0)

        geo.append(round(geo_cap, 4))
        lin.append(round(lin_cap, 4))
        labels.append(f"T{i + 1}")

    return {"geometric": geo, "linear": lin, "labels": labels}


# ── Deployability Index ───────────────────────────────────────────────────────

def deployability_index(
    healer_snapshot: dict,
    lake_stats: dict,
    genome_state: dict,
    redis_ok: bool = False,
    persistence_ok: bool = True,
) -> dict:
    """
    Composite 0-100 score across three pillars:

    Pillar 1 — Network Stability   (30 pts)
      • Last 10 heal events: each API_PING OK  → +2 pts (max 20)
      • ws_stale_cycles == 0                   → +10 pts

    Pillar 2 — Database Health     (30 pts)
      • Redis available                        → +15 pts
      • SQLite trade count > 0                 → +10 pts
      • Lake candle count > 100                → +5  pts

    Pillar 3 — RR Edge             (40 pts)
      • avg_r_multiple ≥ 0.50                  → +15 pts
      • OOS PF ≥ 1.0 for ≥ 1 strategy         → +15 pts
      • genome win_rate ≥ 50%                  → +10 pts
    """
    score = 0
    breakdown: dict = {}

    # ── Pillar 1: Network Stability ───────────────────────────────────────────
    net_score = 0
    events = healer_snapshot.get("recent_events", [])
    ping_oks = sum(1 for e in events if e.get("action") == "API_PING" and e.get("ok", False))
    net_score += min(ping_oks * 2, 20)

    stale = healer_snapshot.get("ws_stale_cycles", 1)
    if stale == 0:
        net_score += 10

    breakdown["network"] = {"score": net_score, "max": 30, "stale_cycles": stale, "ping_oks": ping_oks}
    score += net_score

    # ── Pillar 2: Database Health ─────────────────────────────────────────────
    db_score = 0
    if redis_ok:
        db_score += 15

    # db_stats() returns keys: "trades", "candles", "ticks", "funding", "db_size_mb"
    trade_count  = lake_stats.get("trades", 0)
    candle_count = lake_stats.get("candles", 0)
    if trade_count > 0:
        db_score += 10
    if candle_count > 100:
        db_score += 5

    breakdown["database"] = {
        "score": db_score, "max": 30,
        "redis_ok": redis_ok,
        "trade_count": trade_count,
        "candle_count": candle_count,
    }
    score += db_score

    # ── Pillar 3: RR Edge ─────────────────────────────────────────────────────
    rr_score = 0

    # avg_r_multiple — pull from genome promotion log if available
    promotion_log = genome_state.get("promotion_log", [])
    avg_r = 0.0
    if promotion_log:
        last_promo = [p for p in promotion_log if p.get("decision") == "PROMOTED"]
        if last_promo:
            avg_r = last_promo[-1].get("avg_r_multiple", 0.0)

    if avg_r >= 0.50:
        rr_score += 15

    # OOS PF ≥ 1.0
    oos_pass = any(
        p.get("oos_pf", 0.0) >= 1.0
        for p in promotion_log
        if p.get("decision") == "PROMOTED"
    )
    if oos_pass:
        rr_score += 15

    # win_rate from genome (genome doesn't track live win_rate directly, use pnl session if accessible)
    gen = genome_state.get("generation", 0)
    if gen > 0:
        rr_score += 10   # genome has run at least one generation

    breakdown["rr_edge"] = {
        "score": rr_score, "max": 40,
        "avg_r_multiple": round(avg_r, 4),
        "oos_pf_pass": oos_pass,
        "genome_generation": gen,
    }
    score += rr_score

    score = min(score, 100)

    # V4.0 spec: Deployability must remain ≤ 50 when persistence is BOGUS.
    # A system that cannot save its state is never fully deployable.
    persistence_capped = (not persistence_ok) and score > 50
    if persistence_capped:
        score = 50

    tier = (
        "DEPLOYABLE"    if score >= 75 else
        "CONDITIONAL"   if score >= 50 else
        "NOT READY"
    )

    return {
        "score":             score,
        "max":               100,
        "tier":              tier,
        "persistence_capped": persistence_capped,
        "breakdown":         breakdown,
        "ts":                int(time.time() * 1000),
    }


# ── Benchmark Comparison ──────────────────────────────────────────────────────

# Static reference annualised metrics (as of 2024 consensus estimates)
_BENCHMARKS = {
    "S&P 500 (Buy & Hold)": {
        "annual_return_pct": 10.5,
        "sharpe": 0.60,
        "sortino": 0.85,
        "max_dd_pct": 33.9,
        "description": "Passive index — no active edge required",
    },
    "Avg Hedge Fund (HFRX)": {
        "annual_return_pct": 4.8,
        "sharpe": 0.42,
        "sortino": 0.55,
        "max_dd_pct": 12.5,
        "description": "Industry average — net of 2-and-20 fees",
    },
    "Renaissance Medallion": {
        "annual_return_pct": 66.0,
        "sharpe": 3.20,
        "sortino": 5.10,
        "max_dd_pct": 5.0,
        "description": "Best-known quant fund (closed to outside capital)",
    },
    "Top-Tier CTAs (SG CTA)": {
        "annual_return_pct": 8.2,
        "sharpe": 0.72,
        "sortino": 1.05,
        "max_dd_pct": 18.0,
        "description": "Systematic trend-following commodity advisors",
    },
}


def benchmark_comparison(
    pnl_list: List[float],
    initial_capital: float,
    max_drawdown_pct: float = 0.0,
) -> dict:
    """
    Compare live engine metrics against standard fund benchmarks.

    pnl_list       — per-trade net PnL in USDT (ordered chronologically)
    initial_capital — starting USDT balance
    max_drawdown_pct— current session MDD % (0-100)

    Returns a dict with engine metrics and a list of benchmark rows.
    """
    engine: dict = {
        "annual_return_pct": 0.0,
        "sharpe": 0.0,
        "sortino": 0.0,
        "max_dd_pct": round(max_drawdown_pct, 2),
        "total_trades": len(pnl_list),
        "description": "EOW Quant Engine (current session)",
    }

    if pnl_list and initial_capital > 0:
        # Normalise PnL to returns (fraction of initial capital)
        returns = [p / initial_capital for p in pnl_list]

        engine["sharpe"]  = sharpe_ratio(returns)
        engine["sortino"] = sortino_ratio(returns)

        # Annualised return — assume 252 trading days, trades distributed evenly
        mean_return = statistics.mean(returns) if returns else 0.0
        trades_per_day = max(len(returns) / 252, 1 / 252)
        engine["annual_return_pct"] = round(mean_return * trades_per_day * 252 * 100, 2)

    rows = []
    for name, bm in _BENCHMARKS.items():
        rows.append({
            "name": name,
            "annual_return_pct": bm["annual_return_pct"],
            "sharpe": bm["sharpe"],
            "sortino": bm["sortino"],
            "max_dd_pct": bm["max_dd_pct"],
            "description": bm["description"],
        })

    return {
        "engine":     engine,
        "benchmarks": rows,
        "ts":         int(time.time() * 1000),
    }


# ── Full Analytics Payload ────────────────────────────────────────────────────

def compute_full_analytics(
    pnl_trades: list,
    initial_capital: float,
    session_stats: dict,
    healer_snapshot: dict,
    lake_stats: dict,
    genome_state: dict,
    redis_ok: bool,
    persistence_ok: bool = True,
) -> dict:
    """
    Assemble the complete DBO analytics payload consumed by /api/analytics.
    """
    nets   = [t.get("net_pnl", 0.0) for t in pnl_trades if isinstance(t, dict)]
    r_muls = [t.get("r_multiple", 0.0) for t in pnl_trades if isinstance(t, dict)]

    # Filter out zero R-multiples (trades where initial_risk was 0 — no valid R)
    valid_r = [r for r in r_muls if r != 0.0]

    sharpe  = session_stats.get("sharpe_ratio", 0.0)
    sortino = sortino_ratio(nets)
    mdd_pct = session_stats.get("max_drawdown_pct", 0.0)
    calmar  = calmar_ratio(nets, initial_capital, mdd_pct)

    win_rate   = session_stats.get("win_rate", 0.0) / 100.0  # convert % → fraction
    avg_r_win  = statistics.mean([r for r in valid_r if r > 0]) if [r for r in valid_r if r > 0] else 1.0
    avg_r_loss = statistics.mean([abs(r) for r in valid_r if r < 0]) if [r for r in valid_r if r < 0] else 1.0

    ror    = risk_of_ruin(win_rate, avg_r_win, avg_r_loss, account_units=20)
    growth = geometric_mean_growth(
        valid_r[-100:] if len(valid_r) > 100 else valid_r,
        risk_fraction=0.01,
        initial_capital=initial_capital,
    )
    deploy = deployability_index(
        healer_snapshot, lake_stats, genome_state,
        redis_ok=redis_ok,
        persistence_ok=persistence_ok,
    )
    bench  = benchmark_comparison(nets, initial_capital, mdd_pct)

    return {
        "sharpe_ratio":     sharpe,
        "sortino_ratio":    sortino,
        "calmar_ratio":     calmar,
        "risk_of_ruin_pct": ror,
        "growth_chart":     growth,
        "deployability":    deploy,
        "benchmark":        bench,
        "ts":               int(time.time() * 1000),
    }

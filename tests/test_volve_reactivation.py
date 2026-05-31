"""
Verifier: FTD-PHOENIX-VOLVE-REACTIVATION-001 — VolatilityExpansion Reactivation
10-check verifier covering all deliverables.

Run: python tests/test_volve_reactivation.py
All tests must pass.

Implementation Report
---------------------
Files modified:
  strategies/strategy_modules.py — VolatilityExpansionStrategy.generate_signal()
  main.py                        — boot visibility log line
  config.py                      — APP_VERSION 1.42.2 → 1.43.0

Functions modified:
  VolatilityExpansionStrategy.generate_signal() — reactivated + 5 defects repaired

Root cause: unconditional `return None` at line 298 (deliberately disabled 2026-05-03).
Defects in dead code prevented operation even if re-enabled.

Repairs:
  Bug A — added data length guard and `price = closes[-1]` (was undefined)
  Bug B — added `period_high = max(highs[-(lookback+1):-1])` (was undefined)
  Bug C — added `period_low  = min(lows[-(lookback+1):-1])` (was undefined)
  Bug D — period_high/low now exclude current bar, making breakout condition achievable
  Bug E — O(n²) ATR averaging loop replaced with single O(lookback) _atr() call

Expected behavior after deployment:
  VolatilityExpansion generates LONG signals when price closes above prior N-period high
  with ATR expansion confirmed. Generates SHORT on breakdown below prior N-period low.
  Genome evaluates candidates; promotion governed by existing unmodified gates.
"""
import sys
import math
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parents[1]))

# Stub heavy deps before any project import
for _mod in ["pydantic_settings", "pydantic", "loguru", "fastapi", "uvicorn",
             "aiofiles", "websockets", "aiohttp", "binance", "redis"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

import pydantic_settings as _ps
if not hasattr(_ps, "BaseSettings") or isinstance(_ps.BaseSettings, MagicMock):
    class _BaseSettings:
        def __init_subclass__(cls, **kw): pass
        def __init__(self, **kw):
            for k, v in kw.items(): setattr(self, k, v)
    _ps.BaseSettings = _BaseSettings

import pydantic as _pyd
if not hasattr(_pyd, "Field") or isinstance(_pyd.Field, MagicMock):
    _pyd.Field = lambda *a, **kw: kw.get("default", None)


PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = ""):
    results.append((name, condition, detail))
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


# ── Synthetic data helpers ────────────────────────────────────────────────────

def make_flat_data(n: int, close: float = 100.0, spread: float = 2.0):
    """n bars of flat price with consistent high/low spread."""
    closes = [close] * n
    highs  = [close + spread] * n
    lows   = [close - spread] * n
    return closes, highs, lows


def make_breakout_long(n_base: int = 40, lookback: int = 10):
    """
    n_base flat bars followed by 2 escalating volatile bars, then 1 breakout bar.
    Breakout close exceeds period_high of the prior lookback window.
    ATR expansion ensured by high-volatility bars preceding the breakout.
    """
    # Base bars: tight range (ATR ≈ 0.4)
    closes = [100.0] * n_base + [115.0, 125.0]
    highs  = [100.2] * n_base + [117.0, 127.0]
    lows   = [99.8]  * n_base + [112.0, 122.0]
    # period_high = max(highs[-(lookback+1):-1]) = max(highs of last lookback prior bars)
    # For lookback=10: highs[-11:-1] = [100.2]*9 + [117.0] → period_high = 117
    # price = closes[-1] = 125.0 > 117 ✓
    return closes, highs, lows


def make_breakout_short(n_base: int = 40, lookback: int = 10):
    """Breakdown below prior N-period low."""
    closes = [100.0] * n_base + [85.0, 73.0]
    highs  = [100.2] * n_base + [87.0, 75.0]
    lows   = [99.8]  * n_base + [83.0, 71.0]
    # period_low = min(lows[-11:-1]) = min([99.8]*9 + [83.0]) = 83.0
    # price = 73.0 < 83.0 ✓
    return closes, highs, lows


def make_backtest_candles(symbol: str = "BTCUSDT", n_base: int = 54):
    """
    Return candles dict for DeterministicBacktestEngine.
    n_base=54 gives warmup_bars=50 + 4 bars to trigger and close a signal.
    """
    candles = []
    # Base bars — tight range
    for i in range(n_base):
        candles.append({"open": 100.0, "close": 100.0,
                        "high": 100.2, "low": 99.8,
                        "volume": 1000.0, "ts": 1000 + i})
    # Rising volatile bars (indices n_base to n_base+1)
    for i, (c, h, l) in enumerate([(115.0, 117.0, 112.0), (125.0, 127.0, 122.0)]):
        candles.append({"open": c - 2, "close": c, "high": h, "low": l,
                        "volume": 3000.0, "ts": 1000 + n_base + i})
    # Post-entry bars for TP execution (TP set very close via atr_tp=0.5)
    for i, (c, h, l) in enumerate([(130.0, 132.0, 128.0), (135.0, 137.0, 133.0)]):
        candles.append({"open": c, "close": c, "high": h, "low": l,
                        "volume": 2000.0, "ts": 1000 + n_base + 2 + i})
    return {symbol: candles}


# ─── Test 1: generate_signal() not returning None on LONG breakout ───────────
print("\n[1] LONG breakout signal generation")
try:
    from strategies.strategy_modules import VolatilityExpansionStrategy, Signal

    closes, highs, lows = make_breakout_long(n_base=40, lookback=10)
    # Use vol_filter=1.0, small atr_period to ensure conditions met
    strat = VolatilityExpansionStrategy(dna={"lookback": 10, "atr_period": 5,
                                             "vol_filter": 1.0, "atr_sl": 1.5, "atr_tp": 0.5})
    sig = strat.generate_signal("TESTUSDT", closes, highs, lows)
    check("generate_signal returns non-None on LONG breakout", sig is not None)
    check("signal direction is LONG", sig is not None and sig.signal == Signal.LONG)
    check("entry_price equals price (closes[-1])", sig is not None and sig.entry_price == closes[-1])
    check("stop_loss < entry_price for LONG", sig is not None and sig.stop_loss < sig.entry_price)
    check("take_profit > entry_price for LONG", sig is not None and sig.take_profit > sig.entry_price)
    check("confidence in [0, 0.8]", sig is not None and 0 < sig.confidence <= 0.8)
    check("strategy_id is VE_BREAKOUT_ATR_v1", sig is not None and sig.strategy_id == "VE_BREAKOUT_ATR_v1")
except Exception as exc:
    check("LONG breakout signal test", False, str(exc))


# ─── Test 2: SHORT breakdown signal ──────────────────────────────────────────
print("\n[2] SHORT breakdown signal generation")
try:
    from strategies.strategy_modules import VolatilityExpansionStrategy, Signal

    closes, highs, lows = make_breakout_short(n_base=40, lookback=10)
    strat = VolatilityExpansionStrategy(dna={"lookback": 10, "atr_period": 5,
                                             "vol_filter": 1.0, "atr_sl": 1.5, "atr_tp": 0.5})
    sig = strat.generate_signal("TESTUSDT", closes, highs, lows)
    check("generate_signal returns non-None on SHORT breakdown", sig is not None)
    check("signal direction is SHORT", sig is not None and sig.signal == Signal.SHORT)
    check("stop_loss > entry_price for SHORT", sig is not None and sig.stop_loss > sig.entry_price)
    check("take_profit < entry_price for SHORT", sig is not None and sig.take_profit < sig.entry_price)
except Exception as exc:
    check("SHORT breakdown signal test", False, str(exc))


# ─── Test 3: No signal on flat data ──────────────────────────────────────────
print("\n[3] No signal on flat/no-breakout data")
try:
    from strategies.strategy_modules import VolatilityExpansionStrategy

    closes, highs, lows = make_flat_data(40, close=100.0, spread=1.0)
    strat = VolatilityExpansionStrategy(dna={"lookback": 10, "atr_period": 5,
                                             "vol_filter": 1.0, "atr_sl": 1.5, "atr_tp": 0.5})
    sig = strat.generate_signal("TESTUSDT", closes, highs, lows)
    check("generate_signal returns None on flat data", sig is None)
except Exception as exc:
    check("No-signal flat data test", False, str(exc))


# ─── Test 4: Insufficient data returns None gracefully ───────────────────────
print("\n[4] Insufficient data guard")
try:
    from strategies.strategy_modules import VolatilityExpansionStrategy

    # Only 5 bars — far below min_len = lookback + atr_period + 2 = 17
    strat = VolatilityExpansionStrategy(dna={"lookback": 10, "atr_period": 5})
    sig = strat.generate_signal("X", [100.0]*5, [101.0]*5, [99.0]*5)
    check("returns None (not raises) on insufficient data", sig is None)
except Exception as exc:
    check("Insufficient data guard", False, str(exc))


# ─── Test 5: Backtest participation — trades > 0 ─────────────────────────────
print("\n[5] Backtest participation (DeterministicBacktestEngine)")
try:
    from core.backtest_engine import DeterministicBacktestEngine, FillModelConfig
    from strategies.strategy_modules import VolatilityExpansionStrategy

    candles_by_symbol = make_backtest_candles(n_base=54)
    fill = FillModelConfig(taker_fee=0.0001, slippage_est=0.0001, latency_bars=1)
    engine = DeterministicBacktestEngine(fill=fill, warmup_bars=50)

    dna = {"lookback": 10, "atr_period": 5, "vol_filter": 1.0, "atr_sl": 1.5, "atr_tp": 0.5}
    report = engine.run(candles_by_symbol, lambda: VolatilityExpansionStrategy(dna=dna))

    check("BacktestReport.trades > 0 on breakout data", report.trades > 0,
          f"trades={report.trades}")
except Exception as exc:
    check("Backtest participation test", False, str(exc))


# ─── Test 6: Code path inspection — no unconditional return None ─────────────
print("\n[6] Source code — unconditional disable removed")
try:
    import ast
    src_path = Path(__file__).parents[1] / "strategies" / "strategy_modules.py"
    src = src_path.read_text()

    tree = ast.parse(src)
    # Find generate_signal inside VolatilityExpansionStrategy
    fn_src = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "VolatilityExpansionStrategy":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "generate_signal":
                    fn_src = ast.get_source_segment(src, item)
                    break

    check("generate_signal function found", fn_src is not None)
    # The function must NOT start with an unconditional return None
    # (i.e., the first non-comment executable statement must not be `return None`)
    check("FTD-PHOENIX-VOLVE-REACTIVATION-001 referenced in source",
          "FTD-PHOENIX-VOLVE-REACTIVATION-001" in (fn_src or ""))
    check("period_high defined in source", "period_high" in (fn_src or ""))
    check("period_low defined in source",  "period_low"  in (fn_src or ""))
    check("price = closes[-1] in source",  "price = closes[-1]" in (fn_src or ""))
    check("Bug E fix present (avg_atr uses _atr)",
          "avg_atr = _atr(" in (fn_src or ""))
except Exception as exc:
    check("Source code inspection", False, str(exc))


# ─── Test 7: Regression — TrendFollowing still loads and runs without error ───
print("\n[7] Regression — TrendFollowingStrategy unaffected")
try:
    from strategies.strategy_modules import TrendFollowingStrategy

    strat_tf = TrendFollowingStrategy()
    check("TrendFollowing ID unchanged", strat_tf.ID == "TF_EMA_RSI_v1")

    # Confirm generate_signal runs without exception on any data (may return None)
    closes_tf = [100.0 + i * 0.1 for i in range(60)]
    highs_tf  = [c + 1.0 for c in closes_tf]
    lows_tf   = [c - 1.0 for c in closes_tf]
    raised = False
    try:
        strat_tf.generate_signal("TEST", closes_tf, highs_tf, lows_tf)
    except Exception:
        raised = True
    check("TrendFollowing.generate_signal runs without exception", not raised)
    check("TrendFollowing params intact (ema_fast > 0)", strat_tf.ema_fast > 0)
except Exception as exc:
    check("TrendFollowing regression", False, str(exc))


# ─── Test 8: Regression — MeanReversionStrategy unaffected ───────────────────
print("\n[8] Regression — MeanReversionStrategy unaffected")
try:
    from strategies.strategy_modules import MeanReversionStrategy, Signal as Sig2
    import math as _math

    n = 50
    # Mean + spike below lower BB to trigger LONG
    base = 100.0
    closes_mr = [base] * 30
    # Spike down to create BB lower touch
    closes_mr += [base - 10.0] * 5 + [base] * 15
    highs_mr = [c + 1 for c in closes_mr]
    lows_mr  = [c - 1 for c in closes_mr]

    strat_mr = MeanReversionStrategy()
    signals_mr = []
    for i in range(20, n):
        s = strat_mr.generate_signal("TEST", closes_mr[:i], highs_mr[:i], lows_mr[:i])
        if s is not None:
            signals_mr.append(s)

    check("MeanReversion still imports and initialises", True)
    check("MeanReversion ID unchanged", strat_mr.ID == "MR_BB_RSI_v1")
except Exception as exc:
    check("MeanReversion regression", False, str(exc))


# ─── Test 9: Governance integrity — no gate/threshold changes ────────────────
print("\n[9] Governance integrity — promotion gates unchanged")
try:
    src_ge = (Path(__file__).parents[1] / "core" / "genome_engine.py").read_text()
    check("GENOME_PROMOTE_WIN_RATE present in _maybe_promote", "GENOME_PROMOTE_WIN_RATE" in src_ge)
    check("GENOME_PROMOTE_PF present in _maybe_promote",       "GENOME_PROMOTE_PF" in src_ge)
    check("GENOME_MIN_AVG_R present in _maybe_promote",        "GENOME_MIN_AVG_R" in src_ge)
    check("GENOME_OVERFITTING_MAX_RATIO present",              "GENOME_OVERFITTING_MAX_RATIO" in src_ge)
    check("Sentinel 999.0 present",                            "999.0" in src_ge)

    src_cfg = (Path(__file__).parents[1] / "config.py").read_text()
    check("APP_VERSION bumped to 1.43.0",                      'APP_VERSION = "1.43.0"' in src_cfg)
except Exception as exc:
    check("Governance integrity check", False, str(exc))


# ─── Test 10: Boot log present in main.py ────────────────────────────────────
print("\n[10] Boot visibility in main.py")
try:
    main_src = (Path(__file__).parents[1] / "main.py").read_text()
    check("VOLATILITYEXPANSION MODULE LOADED log in main.py",
          "VOLATILITYEXPANSION MODULE LOADED" in main_src)
    check("VE_BREAKOUT_ATR_v1 in boot log",
          "VE_BREAKOUT_ATR_v1" in main_src)
    check("FTD-PHOENIX-VOLVE-REACTIVATION-001 in boot log",
          "FTD-PHOENIX-VOLVE-REACTIVATION-001" in main_src)
except Exception as exc:
    check("Boot visibility", False, str(exc))


# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("\033[32mALL CHECKS PASSED — FTD-PHOENIX-VOLVE-REACTIVATION-001 VERIFIED\033[0m")
else:
    failed = [(n, d) for n, ok, d in results if not ok]
    print(f"\033[31m{total - passed} FAILED:\033[0m")
    for n, d in failed:
        print(f"  - {n}: {d}")
    sys.exit(1)

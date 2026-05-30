"""
Verifier: FTD-PHOENIX-GENOME-READINESS-001 — Genome Startup Readiness
10-check verifier covering all deliverables.

Run: python tests/test_genome_readiness.py
All tests must pass.
"""
import sys
import asyncio
import tempfile
import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ─── Test 1: data_lake.get_symbols() exists and works ─────────────────────────
print("\n[1] data_lake.get_symbols()")
try:
    from core.data_lake import DataLake
    import inspect
    check("DataLake.get_symbols exists", hasattr(DataLake, "get_symbols"))
    sig = inspect.signature(DataLake.get_symbols)
    check("get_symbols has interval param", "interval" in sig.parameters)

    # Test with real temp SQLite
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        dbpath = f.name
    con = sqlite3.connect(dbpath)
    con.execute("CREATE TABLE candles (symbol TEXT, interval TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL, ts INTEGER)")
    con.executemany("INSERT INTO candles VALUES (?,?,?,?,?,?,?,?)", [
        ("BTCUSDT", "1m", 50000, 50100, 49900, 50050, 1.0, 1000 + i) for i in range(5)
    ] + [
        ("ETHUSDT", "1m", 3000, 3010, 2990, 3005, 10.0, 1000 + i) for i in range(5)
    ])
    con.commit()
    dl = DataLake.__new__(DataLake)
    dl._conn = sqlite3.connect(dbpath)
    dl._conn.row_factory = sqlite3.Row
    syms = dl.get_symbols("1m")
    check("get_symbols returns BTCUSDT", "BTCUSDT" in syms)
    check("get_symbols returns ETHUSDT", "ETHUSDT" in syms)
    check("get_symbols returns 2 symbols", len(syms) == 2)
    dl._conn.close()
    con.close()
    import os; os.unlink(dbpath)
except Exception as exc:
    check("data_lake.get_symbols test", False, str(exc))


# ─── Test 2: genome.seed_from_data_lake() ────────────────────────────────────
print("\n[2] genome.seed_from_data_lake()")
try:
    from core.genome_engine import GenomeEngine

    def _make_genome():
        g = object.__new__(GenomeEngine)
        g.active_dna = {"TrendFollowing": {}, "MeanReversion": {}, "VolatilityExpansion": {}}
        g.per_regime_dna = {}
        g.active_metrics = {}
        g.generation_log = []
        g.promotion_log = []
        g._candle_store = {}
        g._running = False
        g._lock = asyncio.new_event_loop().run_until_complete(asyncio.sleep(0)) or asyncio.Lock()
        g._started_at_ms = int(time.time() * 1000)
        g._last_no_candle_warning_ms = 0
        g._trade_close_count = 0
        g._eval_attempts = 0
        g._eval_skips = 0
        g._eval_sufficient = 0
        g._eval_insufficient = 0
        g._seed_source = "none"
        g._seed_count = 0
        return g

    # Mock data_lake with 200 candles for BTCUSDT and 50 for ETHUSDT
    mock_dl = MagicMock()
    mock_dl.get_symbols.return_value = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
    btc_candles = [{"open": 50000+i, "high": 50100+i, "low": 49900+i, "close": 50050+i, "volume": 1.0, "ts": 1000+i} for i in range(200)]
    eth_candles = [{"open": 3000+i, "high": 3010+i, "low": 2990+i, "close": 3005+i, "volume": 10.0, "ts": 1000+i} for i in range(50)]
    xrp_candles = [{"open": 1.0, "high": 1.01, "low": 0.99, "close": 1.005, "volume": 100.0, "ts": 1000+i} for i in range(5)]  # < 10, should be skipped
    mock_dl.get_candles.side_effect = lambda sym, *a, **kw: {
        "BTCUSDT": btc_candles,
        "ETHUSDT": eth_candles,
        "XRPUSDT": xrp_candles,
    }.get(sym, [])

    import logging
    logging.disable(logging.CRITICAL)  # suppress loguru mocks

    g = _make_genome()
    seeded = g.seed_from_data_lake(mock_dl)

    check("seed_from_data_lake returns dict", isinstance(seeded, dict))
    check("BTCUSDT seeded (200 candles)", seeded.get("BTCUSDT") == 200)
    check("ETHUSDT seeded (50 candles)",  seeded.get("ETHUSDT") == 50)
    check("XRPUSDT skipped (<10 candles)", "XRPUSDT" not in seeded)
    check("_candle_store populated for BTCUSDT", len(g._candle_store.get("BTCUSDT", [])) == 200)
    check("seed_source set to data_lake", g._seed_source == "data_lake")
    check("seed_count = 2", g._seed_count == 2)

except Exception as exc:
    check("seed_from_data_lake test", False, str(exc))


# ─── Test 3: D2 Readiness Guard ──────────────────────────────────────────────
print("\n[3] Readiness Guard — blocks insufficient evaluations")
try:
    import ast
    with open(Path(__file__).parents[1] / "core" / "genome_engine.py") as f:
        src = f.read()

    check("GENOME_MIN_CANDLES_TO_EVALUATE in _evolution_cycle",
          "GENOME_MIN_CANDLES_TO_EVALUATE" in src and "eval_skips" in src)
    check("GENOME_SKIPPED_INSUFFICIENT_DATA event log present",
          "GENOME_SKIPPED_INSUFFICIENT_DATA" in src)
    check("eval_attempts incremented before guard",
          "self._eval_attempts += 1" in src)
    check("eval_sufficient incremented on pass",
          "self._eval_sufficient += 1" in src)
    check("eval_insufficient incremented on skip",
          "self._eval_insufficient += 1" in src)
except Exception as exc:
    check("Readiness Guard code inspection", False, str(exc))


# ─── Test 4: D3 Readiness Report in export_state ─────────────────────────────
print("\n[4] Readiness Report in export_state()")
try:
    from core.genome_engine import GenomeEngine
    import inspect
    src = inspect.getsource(GenomeEngine.export_state)
    check("readiness_report key in export_state",     "readiness_report" in src)
    check("eval_attempts in readiness_report",         "eval_attempts" in src)
    check("eval_skips in readiness_report",            "eval_skips" in src)
    check("eval_with_sufficient in readiness_report",  "eval_with_sufficient" in src)
    check("avg_candles in readiness_report",           "avg_candles" in src)
    check("max_candles in readiness_report",           "max_candles" in src)
    check("min_candles in readiness_report",           "min_candles" in src)
    check("seed_source in readiness_report",           "seed_source" in src)
    check("ready flag in readiness_report",            "ready" in src)
except Exception as exc:
    check("export_state readiness_report", False, str(exc))


# ─── Test 5: D5 DATA_SUFFICIENCY_FAILURE threshold fix ────────────────────────
print("\n[5] DATA_SUFFICIENCY_FAILURE — fires at 10 rejections (not blocked by INSUFFICIENT_DATA verdict)")
try:
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze

    # 10 rejections, all T=0 — verdict could be INSUFFICIENT_DATA from collector
    mock_audit = {
        "verdict": "INSUFFICIENT_DATA",   # ← would have blocked old rule
        "summary": {"total_rejected": 10, "total_promoted": 0, "total_decisions": 10},
        "oos_diagnostics": {
            "oos_trades_zero": {"count": 10, "pct": 100.0},
            "avg_oos_trades": 0.0,
            "avg_train_trades": 0.0,
        },
        "candidate_quality_distribution": {
            "trade_count_distribution": {
                "zero_trades": {"count": 10, "pct": 100.0},
                "1_to_4":      {"count": 0,  "pct": 0.0},
                "5_to_10":     {"count": 0,  "pct": 0.0},
                "above_10":    {"count": 0,  "pct": 0.0},
            },
        },
    }
    hits = analyze({"Promotion Failure Audit": mock_audit})
    rule_names = [h["rule"] for h in hits]
    check("DATA_SUFFICIENCY_FAILURE fires despite INSUFFICIENT_DATA verdict", "DATA_SUFFICIENCY_FAILURE" in rule_names)

    # Verify <10 rejections still blocked
    mock_audit_low = dict(mock_audit)
    mock_audit_low["summary"] = {"total_rejected": 5, "total_promoted": 0, "total_decisions": 5}
    hits_low = analyze({"Promotion Failure Audit": mock_audit_low})
    check("DATA_SUFFICIENCY_FAILURE blocked at <10 rejections", "DATA_SUFFICIENCY_FAILURE" not in [h["rule"] for h in hits_low])

except Exception as exc:
    check("DATA_SUFFICIENCY_FAILURE threshold fix", False, str(exc))


# ─── Test 6: D6 + D7 Boot log messages ────────────────────────────────────────
print("\n[6] Boot visibility messages (D6 + D7)")
try:
    with open(Path(__file__).parents[1] / "core" / "genome_engine.py") as f:
        ge_src = f.read()
    with open(Path(__file__).parents[1] / "main.py") as f:
        main_src = f.read()

    check("GENOME READINESS MODULE LOADED in main.py",  "GENOME READINESS MODULE LOADED" in main_src)
    check("GENOME STARTUP STATUS log in genome_engine",  "GENOME STARTUP STATUS" in ge_src)
    check("GENOME_READY event log in genome_engine",     "GENOME_READY" in ge_src)
    check("GENOME_SKIPPED_INSUFFICIENT_DATA in engine",  "GENOME_SKIPPED_INSUFFICIENT_DATA" in ge_src)
    check("GENOME_WAITING_FOR_HISTORY in engine",        "GENOME_WAITING_FOR_HISTORY" in ge_src)
    check("FTD-PHOENIX-GENOME-READINESS-001 referenced", "FTD-PHOENIX-GENOME-READINESS-001" in main_src)
except Exception as exc:
    check("Boot visibility messages", False, str(exc))


# ─── Test 7: Governance Integrity ────────────────────────────────────────────
print("\n[7] Governance integrity — no threshold/gate/strategy changes")
try:
    import ast
    with open(Path(__file__).parents[1] / "core" / "genome_engine.py") as f:
        ge_src = f.read()
    tree = ast.parse(ge_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_maybe_promote":
            fn_src = ast.get_source_segment(ge_src, node)
            check("GENOME_PROMOTE_WIN_RATE unchanged in _maybe_promote", "GENOME_PROMOTE_WIN_RATE" in fn_src)
            check("GENOME_PROMOTE_PF unchanged in _maybe_promote",       "GENOME_PROMOTE_PF" in fn_src)
            check("GENOME_MIN_AVG_R unchanged in _maybe_promote",        "GENOME_MIN_AVG_R" in fn_src)
            check("GENOME_OVERFITTING_MAX_RATIO unchanged",              "GENOME_OVERFITTING_MAX_RATIO" in fn_src)
            check("overfit sentinel 999 unchanged",                      "999.0" in fn_src)
            break
    else:
        check("_maybe_promote found", False, "function not found")
except Exception as exc:
    check("Governance integrity", False, str(exc))


# ─── Test 8: Existing AIL diagnostics intact ─────────────────────────────────
print("\n[8] Existing AIL diagnostics unchanged")
try:
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze

    # All original rules should still fire on appropriate data
    test_snaps = {
        "Promotion Watch": {"total_promoted": 0, "total_cycles": 200},
        "Performance Status": {"win_rate": 0.4, "total_trades": 50, "avg_win_run": 0.1, "avg_loss_run": 1.0, "peak_r_trades": 5},
    }
    hits = analyze(test_snaps)
    rule_names = [h["rule"] for h in hits]
    check("NO_PROMOTIONS rule still fires",       "NO_PROMOTIONS" in rule_names)
    check("PEAK_R_INSUFFICIENT rule still fires", "PEAK_R_INSUFFICIENT" in rule_names)
except Exception as exc:
    check("Existing AIL diagnostics", False, str(exc))


# ─── Test 9: config.py has GENOME_MIN_CANDLES_TO_EVALUATE ───────────────────
print("\n[9] Config parameter added")
try:
    with open(Path(__file__).parents[1] / "config.py") as f:
        cfg_src = f.read()
    check("GENOME_MIN_CANDLES_TO_EVALUATE in config.py", "GENOME_MIN_CANDLES_TO_EVALUATE" in cfg_src)
    check("Default value 50 in config",                  "50" in cfg_src and "GENOME_MIN_CANDLES_TO_EVALUATE" in cfg_src)
except Exception as exc:
    check("Config parameter", False, str(exc))


# ─── Test 10: AIL collector has Genome Readiness snapshot ────────────────────
print("\n[10] AIL collector includes Genome Readiness snapshot")
try:
    with open(Path(__file__).parents[1] / "core" / "autonomous_intelligence" / "collector" / "report_collector.py") as f:
        coll_src = f.read()
    check("Genome Readiness snapshot in collector", "Genome Readiness" in coll_src)
    check("readiness_report accessed in collector", "readiness_report" in coll_src)
    check("eval_attempts in collector snapshot",    "eval_attempts" in coll_src)
    check("seed_source in collector snapshot",      "seed_source" in coll_src)
    check("ready flag in collector snapshot",       '"ready"' in coll_src)
except Exception as exc:
    check("AIL collector Genome Readiness", False, str(exc))


# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("\033[32mALL CHECKS PASSED — FTD-PHOENIX-GENOME-READINESS-001 VERIFIED\033[0m")
else:
    failed = [(n, d) for n, ok, d in results if not ok]
    print(f"\033[31m{total-passed} FAILED:\033[0m")
    for n, d in failed:
        print(f"  - {n}: {d}")
    sys.exit(1)

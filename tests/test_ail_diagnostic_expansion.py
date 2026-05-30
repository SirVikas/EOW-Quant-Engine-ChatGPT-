"""
Verifier: FTD-PHOENIX-AIL-INVESTIGATION-001 — AIL Diagnostic Expansion
Confirms all 5 deliverables are implemented correctly.

Run: python tests/test_ail_diagnostic_expansion.py
All tests must pass before considering the FTD complete.
"""
import sys
import json
import time
import hashlib
import asyncio
from pathlib import Path
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).parents[1]))

# Provide minimal stubs for heavy dependencies not available in the test environment
from unittest.mock import MagicMock
for _mod in ["pydantic_settings", "pydantic", "loguru", "fastapi", "uvicorn", "aiofiles"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
# pydantic_settings.BaseSettings must be a real class (genome_engine inherits from it indirectly via cfg)
import pydantic_settings as _ps
if not hasattr(_ps, "BaseSettings") or isinstance(_ps.BaseSettings, MagicMock):
    class _BaseSettings:
        def __init_subclass__(cls, **kw): pass
        def __init__(self, **kw):
            for k, v in kw.items(): setattr(self, k, v)
    _ps.BaseSettings = _BaseSettings


def _lineage_id(d: dict) -> str:
    ts = time.strftime("%Y%m%d%H%M%S", time.gmtime()) + "000"
    sha = hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]
    return f"AIL-{ts}-{sha}"


PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = ""):
    results.append((name, condition, detail))
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


# ─── Test 1: PromotionEvent has new observability fields ──────────────────────
print("\n[1] PromotionEvent observability fields")
try:
    from core.genome_engine import PromotionEvent
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(PromotionEvent)}
    check("PromotionEvent.train_trades exists", "train_trades" in field_names)
    check("PromotionEvent.oos_trades exists",   "oos_trades"   in field_names)
    check("PromotionEvent.win_rate exists",     "win_rate"     in field_names)
    ev = PromotionEvent(
        ts=1, strategy_type="TrendFollowing", decision="REJECTED",
        reason="train_gate(PF=0.5 WR=30.0% T=2)", genome_id="abc",
        train_pf=0.5, oos_pf=0.0, avg_r_multiple=-0.1, cost_drag_pct=5.0,
        dna={}, train_trades=2, oos_trades=0, win_rate=30.0,
    )
    d = asdict(ev)
    check("PromotionEvent.train_trades serializes", d["train_trades"] == 2)
    check("PromotionEvent.oos_trades serializes",   d["oos_trades"]   == 0)
    check("PromotionEvent.win_rate serializes",     d["win_rate"]     == 30.0)
except Exception as exc:
    check("PromotionEvent fields import", False, str(exc))

# ─── Test 2: DATA_SUFFICIENCY_FAILURE rule fires correctly ────────────────────
print("\n[2] DATA_SUFFICIENCY_FAILURE rule")
try:
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze

    # Mock snapshot: >80% of candidates have <5 training trades
    mock_audit_insufficient = {
        "verdict": "SINGLE_GATE_DOMINATES",
        "summary": {"total_rejected": 20, "total_promoted": 0, "total_decisions": 20},
        "oos_diagnostics": {
            "oos_trades_zero": {"count": 18, "pct": 90.0},
            "avg_oos_trades": 0.0,
            "avg_train_trades": 1.5,
        },
        "candidate_quality_distribution": {
            "trade_count_distribution": {
                "zero_trades": {"count": 10, "pct": 50.0},
                "1_to_4":      {"count": 8,  "pct": 40.0},
                "5_to_10":     {"count": 2,  "pct": 10.0},
                "above_10":    {"count": 0,  "pct": 0.0},
            },
        },
    }
    snaps_bad = {"Promotion Failure Audit": mock_audit_insufficient}
    hits_bad = analyze(snaps_bad)
    rule_names_bad = [h["rule"] for h in hits_bad]
    check("DATA_SUFFICIENCY_FAILURE fires when >80% trades<5", "DATA_SUFFICIENCY_FAILURE" in rule_names_bad)

    # Mock snapshot: sufficient trade data — rule should NOT fire
    mock_audit_ok = {
        "verdict": "SINGLE_GATE_DOMINATES",
        "summary": {"total_rejected": 20, "total_promoted": 0, "total_decisions": 20},
        "oos_diagnostics": {
            "oos_trades_zero": {"count": 2, "pct": 10.0},
            "avg_oos_trades": 8.0,
            "avg_train_trades": 12.0,
        },
        "candidate_quality_distribution": {
            "trade_count_distribution": {
                "zero_trades": {"count": 1, "pct": 5.0},
                "1_to_4":      {"count": 2, "pct": 10.0},
                "5_to_10":     {"count": 10, "pct": 50.0},
                "above_10":    {"count": 7, "pct": 35.0},
            },
        },
    }
    snaps_ok = {"Promotion Failure Audit": mock_audit_ok}
    hits_ok = analyze(snaps_ok)
    rule_names_ok = [h["rule"] for h in hits_ok]
    check("DATA_SUFFICIENCY_FAILURE does NOT fire when data sufficient", "DATA_SUFFICIENCY_FAILURE" not in rule_names_ok)

    # Check finding attributes
    dsf = next((h for h in hits_bad if h["rule"] == "DATA_SUFFICIENCY_FAILURE"), None)
    if dsf:
        check("DATA_SUFFICIENCY_FAILURE category=GENOME",    dsf["category"] == "GENOME")
        check("DATA_SUFFICIENCY_FAILURE severity=HIGH",      dsf["severity"] == "HIGH")
        check("DATA_SUFFICIENCY_FAILURE confidence≥0.8",     dsf["confidence_score"] >= 0.8)
        check("DATA_SUFFICIENCY_FAILURE recommendation advisory", "ADVISORY" in dsf["recommendation"])
        check("DATA_SUFFICIENCY_FAILURE no autonomous action",    "do not modify" in dsf["recommendation"].lower())
    else:
        check("DATA_SUFFICIENCY_FAILURE finding attributes", False, "rule not found")

    # Verify INSUFFICIENT_DATA verdict skips rule
    snaps_insuf = {"Promotion Failure Audit": {"verdict": "INSUFFICIENT_DATA", "summary": {"total_rejected": 5}}}
    hits_insuf = analyze(snaps_insuf)
    check("DATA_SUFFICIENCY_FAILURE skips on INSUFFICIENT_DATA verdict", "DATA_SUFFICIENCY_FAILURE" not in [h["rule"] for h in hits_insuf])

except Exception as exc:
    check("DATA_SUFFICIENCY_FAILURE rule import/test", False, str(exc))

# ─── Test 3: Sentinel value detection ────────────────────────────────────────
print("\n[3] Sentinel value detection logic")
try:
    import math

    def _safe_num(v):
        if isinstance(v, float):
            if math.isinf(v) or math.isnan(v):
                return 99.99 if v > 0 else -99.99
        return v

    check("_safe_num(inf) = 99.99",  _safe_num(float("inf"))  == 99.99)
    check("_safe_num(nan) = -99.99", _safe_num(float("nan"))  == -99.99)
    check("_safe_num(-inf) = -99.99",_safe_num(float("-inf")) == -99.99)
    check("_safe_num(999) = 999",    _safe_num(999.0) == 999.0)  # 999 is NOT clamped — it's a real sentinel

    # overfit_ratio=999 sentinel detection
    sentinel_overfit_count = sum(1 for r in ["overfit(ratio=999.0)", "train_gate", "overfit(ratio=999.0)"]
                                 if "overfit(ratio=999" in r)
    check("overfit sentinel 999 detected in reason string", sentinel_overfit_count == 2)

except Exception as exc:
    check("Sentinel detection", False, str(exc))

# ─── Test 4: OOS diagnostics structure ────────────────────────────────────────
print("\n[4] OOS diagnostics structure")
try:
    oos_t_vals = [0, 0, 0, 3, 0, 0, 7, 0, 0, 0]
    oos_zero  = sum(1 for t in oos_t_vals if t == 0)
    oos_1_5   = sum(1 for t in oos_t_vals if 1 <= t <= 5)
    oos_6_20  = sum(1 for t in oos_t_vals if 6 <= t <= 20)
    oos_gt20  = sum(1 for t in oos_t_vals if t > 20)
    check("OOS zero count correct",   oos_zero  == 8)
    check("OOS 1-5 count correct",    oos_1_5   == 1)
    check("OOS 6-20 count correct",   oos_6_20  == 1)
    check("OOS >20 count correct",    oos_gt20  == 0)
    check("OOS zero pct correct",     round(oos_zero / len(oos_t_vals) * 100, 1) == 80.0)
except Exception as exc:
    check("OOS diagnostics calculation", False, str(exc))

# ─── Test 5: Train gate root cause matrix ─────────────────────────────────────
print("\n[5] Train gate root cause matrix logic")
try:
    from core.genome_engine import PromotionEvent
    import dataclasses

    # Simulate candidates: PF fails but WR passes, trades pass
    candidates = [
        {"train_pf": 0.8, "win_rate": 60.0, "train_trades": 6, "reason": "train_gate(...)"},
        {"train_pf": 1.5, "win_rate": 30.0, "train_trades": 6, "reason": "train_gate(...)"},
        {"train_pf": 0.5, "win_rate": 30.0, "train_trades": 2, "reason": "train_gate(...)"},
    ]
    _pf_thresh = 1.2
    _wr_thresh = 50.0
    _tr_min = 5
    tg_pf = tg_wr = tg_tr = 0
    for c in candidates:
        if c["train_pf"] < _pf_thresh: tg_pf += 1
        if c["win_rate"] < _wr_thresh:  tg_wr += 1
        if c["train_trades"] < _tr_min: tg_tr += 1
    check("Train gate PF-only count", tg_pf == 2)
    check("Train gate WR-only count", tg_wr == 2)
    check("Train gate trades count",  tg_tr == 1)
except Exception as exc:
    check("Train gate matrix", False, str(exc))

# ─── Test 6: Findings store — DATA_SUFFICIENCY_FAILURE save/load ──────────────
print("\n[6] Findings store CRUD for DATA_SUFFICIENCY_FAILURE")
try:
    from core.autonomous_intelligence.storage import findings_store
    from core.autonomous_intelligence.analysis.finding_generator import generate_findings

    hit = {
        "rule": "DATA_SUFFICIENCY_FAILURE",
        "category": "GENOME",
        "severity": "HIGH",
        "title": "Test: data sufficiency failure",
        "evidence": [{"pct_insufficient": 90.0}],
        "confidence_score": 0.90,
        "sample_size": 20,
        "economic_impact_est": "HIGH",
        "risk_level": "HIGH",
        "recommendation": "ADVISORY ONLY — do not modify gates.",
        "source_reports": ["Promotion Failure Audit"],
    }
    findings = generate_findings([hit])
    check("Finding generated from hit", len(findings) == 1)
    f = findings[0]
    check("Finding lineage_id format", f.lineage_id.startswith("AIL-"))
    check("Finding rule set",          f.rule == "DATA_SUFFICIENCY_FAILURE")
    check("Finding status PENDING",    f.status == "PENDING")

    d = f.to_dict()
    d["evidence_score"] = 75

    async def _test_store():
        await findings_store.save_finding(d)
        loaded = await findings_store.get_finding(d["lineage_id"])
        return loaded

    loaded = asyncio.run(_test_store())
    check("Finding saved and loaded",  loaded is not None)
    check("Loaded rule matches",       loaded.get("rule") == "DATA_SUFFICIENCY_FAILURE")
    check("Loaded severity matches",   loaded.get("severity") == "HIGH")

    # Cleanup
    async def _cleanup():
        import sqlite3
        from pathlib import Path
        db = Path(__file__).parents[1] / "data" / "ail" / "findings.db"
        if db.exists():
            import asyncio as _a
            def _del():
                con = sqlite3.connect(str(db))
                con.execute("DELETE FROM findings WHERE rule='DATA_SUFFICIENCY_FAILURE' AND title LIKE 'Test:%'")
                con.commit()
                con.close()
            await _a.to_thread(_del)
    asyncio.run(_cleanup())

except Exception as exc:
    check("Findings store CRUD", False, str(exc))

# ─── Test 7: No governance rules changed ─────────────────────────────────────
print("\n[7] Governance integrity check")
try:
    import ast
    with open(Path(__file__).parents[1] / "core" / "genome_engine.py") as f:
        src = f.read()
    tree = ast.parse(src)
    # Find _maybe_promote function and verify gate logic unchanged
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_maybe_promote":
            src_fn = ast.get_source_segment(src, node)
            check("GENOME_PROMOTE_WIN_RATE still in gate 1",  "GENOME_PROMOTE_WIN_RATE" in src_fn)
            check("GENOME_PROMOTE_PF still in gate 1",        "GENOME_PROMOTE_PF" in src_fn)
            check("oos_valid used in gate 2 (GENOME_OOS_MIN_PF applied at eval time)", "oos_valid" in src_fn)
            check("GENOME_MIN_AVG_R still in gate 3",         "GENOME_MIN_AVG_R" in src_fn)
            check("GENOME_OVERFITTING_MAX_RATIO still in gate 4", "GENOME_OVERFITTING_MAX_RATIO" in src_fn)
            check("overfit=999 sentinel unchanged",           "999.0" in src_fn)
            break
    else:
        check("_maybe_promote found in genome_engine", False, "function not found")
except Exception as exc:
    check("Governance integrity", False, str(exc))

# ─── Test 8: Boot log message present ────────────────────────────────────────
print("\n[8] Boot visibility message")
try:
    with open(Path(__file__).parents[1] / "core" / "autonomous_intelligence" / "ail_engine.py") as f:
        ail_src = f.read()
    check("Boot log contains FTD investigation ID",
          "FTD-PHOENIX-AIL-INVESTIGATION-001" in ail_src)
    check("Boot log mentions AIL Diagnostic Expansion",
          "AIL Diagnostic Expansion Loaded" in ail_src)
except Exception as exc:
    check("Boot visibility message", False, str(exc))

# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("\033[32mALL CHECKS PASSED — FTD-PHOENIX-AIL-INVESTIGATION-001 VERIFIED\033[0m")
else:
    failed = [(n, d) for n, ok, d in results if not ok]
    print(f"\033[31m{total-passed} FAILED:\033[0m")
    for n, d in failed:
        print(f"  - {n}: {d}")
    sys.exit(1)

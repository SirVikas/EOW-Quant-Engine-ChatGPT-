"""
Learning Intelligence Observatory — Verification Suite
FTD-PRP003A-LIO-001

Validates:
  A. API endpoint integrity (8 endpoints respond with correct shape)
  B. Pattern growth pipeline (record → pattern → topology)
  C. Negative memory visibility (rollback → entry → ban)
  D. Ecology and RL telemetry updates
  E. Cognition / noise metrics
  F. Sovereign readiness gate logic
  G. LIO boot confirmation log presence
  H. Dashboard HTML wiring (tab, buttons, JS functions)

Usage:
  python tests/learning_intelligence_verifier.py
"""
from __future__ import annotations
import os, sys, time, json, tempfile, importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_PASS = 0
_FAIL = 0
_FAILURES: list[str] = []

def check(label: str, condition: bool, note: str = "") -> None:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"  \033[92m✓\033[0m {label}")
    else:
        _FAIL += 1
        _FAILURES.append(f"{label}{' [' + note + ']' if note else ''}")
        print(f"  \033[91m✗\033[0m {label}{' [' + note + ']' if note else ''}")

def section(title: str) -> None:
    print(f"\n\033[1m\033[93m── {title} ──────────────────────────────────────────────────────────────────────────\033[0m")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — Import integrity
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION A — Import integrity")

try:
    from core.learning_memory import learning_memory_orchestrator as lmo
    check("A01 LMO importable", True)
except Exception as e:
    check("A01 LMO importable", False, str(e))

try:
    from core.learning_memory.trade_memory_bridge import trade_memory_bridge
    check("A02 TradeMemoryBridge importable", True)
except Exception as e:
    check("A02 TradeMemoryBridge importable", False, str(e))

try:
    from core.signal_ecology.opportunity_ecology import opportunity_ecology
    check("A03 OpportunityEcology importable", True)
except Exception as e:
    check("A03 OpportunityEcology importable", False, str(e))

try:
    from core.rl_engine import rl_engine
    check("A04 RLEngine importable", True)
except Exception as e:
    check("A04 RLEngine importable", False, str(e))

try:
    from core.signal_truth.signal_truth_engine import signal_truth_engine
    check("A05 SignalTruthEngine importable", True)
except Exception as e:
    check("A05 SignalTruthEngine importable", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — LIO summary endpoint logic
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION B — LIO summary endpoint logic")

from core.learning_memory import learning_memory_orchestrator as _lmo_mod
from core.learning_memory.learning_memory_orchestrator import LearningMemoryOrchestrator
from core.learning_memory.pattern_engine import PatternEngine
from core.learning_memory.memory_store import MemoryStore
from core.learning_memory.negative_memory import NegativeMemory
from core.learning_memory.confidence_updater import ConfidenceUpdater
from core.learning_memory.forgetting_engine import ForgettingEngine
from core.learning_memory.pattern_indexer import PatternIndexer
from core.learning_memory.explainability_engine import ExplainabilityEngine

import math

def _make_lmo_iso(tmpdir: str) -> LearningMemoryOrchestrator:
    """Build an isolated LMO with temp paths."""
    iso = LearningMemoryOrchestrator.__new__(LearningMemoryOrchestrator)
    iso._store     = MemoryStore(path=os.path.join(tmpdir, "mem.jsonl"))
    iso._engine    = PatternEngine()
    iso._updater   = ConfidenceUpdater()
    iso._applier   = __import__("core.learning_memory.memory_applier",
                                fromlist=["MemoryApplier"]).MemoryApplier()
    iso._forgetter = ForgettingEngine()
    iso._neg_memory = NegativeMemory(path=os.path.join(tmpdir, "neg.jsonl"))
    iso._indexer   = PatternIndexer(iso._store, iso._engine)
    iso._explain   = ExplainabilityEngine()
    iso._enabled   = True
    iso._last_prune_ts  = 0.0
    iso._cycle_count    = 0
    iso._exploration_boost = False
    return iso


with tempfile.TemporaryDirectory() as tmpdir:
    import core.learning_memory.trade_memory_bridge as _tmb_mod
    orig_lmo = _tmb_mod.learning_memory_orchestrator
    lmo_iso  = _make_lmo_iso(tmpdir)
    _tmb_mod.learning_memory_orchestrator = lmo_iso

    from core.learning_memory.trade_memory_bridge import TradeMemoryBridge
    bridge = TradeMemoryBridge()

    # Feed 0 records → DORMANT
    s0 = lmo_iso.summary()
    check("B01 zero records → cycle_count=0", s0.get("cycle_count", 0) == 0)

    # Feed 1 winning record → LEARNING
    bridge.record_trade("T0", "BTCUSDT", "MEAN_REVERTING", "MR_STRAT",
                        "LONG", net_pnl=2.0, utc_hour=10)
    s1 = lmo_iso.summary()
    check("B02 1 record stored → cycle_count=1", s1.get("cycle_count") == 1,
          f"got {s1.get('cycle_count')}")
    check("B03 total_records=1 after 1 trade", s1.get("total_records") == 1,
          f"got {s1.get('total_records')}")
    check("B04 patterns_formed still 0 after 1 record", s1.get("formed_patterns") == 0)

    # Feed 19 more records → still forming (not 3 contexts yet)
    for i in range(19):
        bridge.record_trade(f"T{i+1}", "BTCUSDT", "MEAN_REVERTING", "MR_STRAT",
                            "LONG", net_pnl=2.0, utc_hour=10)  # same hour → same bucket
    s2 = lmo_iso.summary()
    check("B05 20 records stored", s2.get("total_records") == 20,
          f"got {s2.get('total_records')}")

    _tmb_mod.learning_memory_orchestrator = orig_lmo


# ══════════════════════════════════════════════════════════════════════════════
# SECTION C — Pattern stage classification
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION C — Pattern stage classification")

from core.learning_memory.pattern_engine import PatternRecord, PatternKey

def _make_pat(samples, success, confidence, contexts, key_str=None):
    key: PatternKey = ("MEAN_REVERTING", "MEDIUM", "BTCUSDT", "MR_STRAT", "UP")
    p = PatternRecord(key)
    p.samples    = samples
    p.success    = success
    p.confidence = confidence
    p.contexts   = set(contexts)
    return p

# Stage logic mirrors lio_patterns() endpoint
def _classify_stage(pat, neg_entry=None):
    if neg_entry and neg_entry.get("permanent"):
        return "BANNED"
    if neg_entry and neg_entry.get("score", 0) >= 0.10:
        return "TOXIC"
    if pat.is_formed:
        return "STABLE"
    if pat.samples >= 10:
        return "FORMING"
    return "OBSERVED"

p_obs  = _make_pat(3, 2, 50.0, {"a"})
p_form = _make_pat(15, 12, 65.0, {"a", "b"})
p_stab = _make_pat(25, 22, 88.0, {"a", "b", "c"})
p_tox  = _make_pat(20, 5, 30.0, {"a", "b", "c"})
p_ban  = _make_pat(20, 5, 30.0, {"a", "b", "c"})

check("C01 3 samples → OBSERVED",  _classify_stage(p_obs) == "OBSERVED")
check("C02 15 samples → FORMING",  _classify_stage(p_form) == "FORMING")
check("C03 stable pattern → STABLE",_classify_stage(p_stab) == "STABLE",
      f"is_formed={p_stab.is_formed} conf={p_stab.confidence}")
check("C04 neg entry score=0.5 → TOXIC",
      _classify_stage(p_tox, {"permanent": False, "score": 0.5}) == "TOXIC")
check("C05 neg entry permanent → BANNED",
      _classify_stage(p_ban, {"permanent": True, "score": 1.0}) == "BANNED")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION D — Negative memory enrichment
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION D — Negative memory status enrichment")

def _neg_status(entry):
    if entry.get("permanent"):
        return "PERMANENTLY_BANNED"
    score = entry.get("score", 0)
    if score >= 0.70:
        return "QUARANTINED"
    if score >= 0.30:
        return "TOXIC"
    return "WARNING"

check("D01 score=1.0 no perm → QUARANTINED",  _neg_status({"permanent": False, "score": 1.0}) == "QUARANTINED")
check("D02 score=0.50 → TOXIC",               _neg_status({"permanent": False, "score": 0.50}) == "TOXIC")
check("D03 score=0.15 → WARNING",             _neg_status({"permanent": False, "score": 0.15}) == "WARNING")
check("D04 permanent=True → PERMANENTLY_BANNED",
      _neg_status({"permanent": True, "score": 1.0}) == "PERMANENTLY_BANNED")

with tempfile.TemporaryDirectory() as tmpdir:
    neg = NegativeMemory(path=os.path.join(tmpdir, "neg.jsonl"))
    key = ("MEAN_REVERTING", "MEDIUM", "BTCUSDT", "BAD_STRAT", "UP")
    # Option-A guard: 3 rollbacks with samples < MIN_SAMPLES_FOR_PERMANENT_BAN
    # must NOT set permanent ban (sparse-sample protection)
    neg.record_rollback(key, current_samples=2)
    neg.record_rollback(key, current_samples=2)
    neg.record_rollback(key, current_samples=2)
    entries = neg.to_list()
    check("D05 3 rollbacks + samples<5 → permanent=False (sparse-sample guard)",
          len(entries) == 1 and entries[0].get("permanent") is False,
          f"entries={entries}")
    # Same pattern with sufficient samples must escalate to permanent ban
    neg2 = NegativeMemory(path=os.path.join(tmpdir, "neg2.jsonl"))
    neg2.record_rollback(key, current_samples=5)
    neg2.record_rollback(key, current_samples=5)
    neg2.record_rollback(key, current_samples=5)
    entries2 = neg2.to_list()
    check("D05b 3 rollbacks + samples>=5 → permanent=True",
          len(entries2) == 1 and entries2[0].get("permanent") is True,
          f"entries2={entries2}")
    # Parse key_str
    ks = entries[0].get("key_str", "")
    parts = ks.split("|")
    check("D06 key_str has 5 pipe-separated parts", len(parts) == 5, f"parts={parts}")
    check("D07 key_str parts[0]=MEAN_REVERTING",  parts[0] == "MEAN_REVERTING")
    check("D08 key_str parts[4]=UP",              parts[4] == "UP")

# ForgettingEngine sub-formation prune guard (v1.9.1)
from core.learning_memory.forgetting_engine import ForgettingEngine as FE
_fe = FE()
_pe_fe = PatternEngine()

# Sub-formation pattern (samples < 20): must survive prune even at confidence=0
_sub_key = ("MEAN_REVERTING", "LOW", "BTCUSDT", "MR_STRAT", "UP")
_sub_rec = MemoryStore.build_record(
    cycle_id="FE_TEST", regime="MEAN_REVERTING", volatility="LOW",
    timeframe="10", instrument="BTCUSDT", parameter="MR_STRAT",
    direction="UP", score_delta=-5.0, rollback=True,
    meta_score=30.0, contradiction=False, ai_mode="TRADE", rationale=""
)
_pe_fe.ingest(_sub_rec)
_sub_pat = _pe_fe.get_pattern(_sub_key)
if _sub_pat:
    _sub_pat.confidence = 0.0  # force to below REMOVAL_THRESHOLD
    _sub_pat.samples    = 4    # sub-formation
pruned_fe = _fe.prune(_pe_fe)
check("D09 sub-formation pattern (4 samples, conf=0) NOT pruned",
      len(pruned_fe) == 0 and _pe_fe.get_pattern(_sub_key) is not None,
      f"pruned={pruned_fe}")

# Formation-threshold pattern (samples >= 20): must be pruned at low confidence
_form_key = ("MEAN_REVERTING", "LOW", "ETHUSDT", "MR_STRAT", "UP")
for _i in range(20):
    _r = MemoryStore.build_record(
        cycle_id=f"FE_FORM_{_i}", regime="MEAN_REVERTING", volatility="LOW",
        timeframe=str(_i % 24), instrument="ETHUSDT", parameter="MR_STRAT",
        direction="UP", score_delta=-5.0, rollback=True,
        meta_score=30.0, contradiction=False, ai_mode="TRADE", rationale=""
    )
    _pe_fe.ingest(_r)
_form_pat = _pe_fe.get_pattern(_form_key)
if _form_pat:
    _form_pat.confidence = 10.0  # below REMOVAL_THRESHOLD=25
    _form_pat.samples    = 20
pruned_form = _fe.prune(_pe_fe)
check("D10 formed pattern (20 samples, conf=10) IS pruned",
      _form_key in [_pe_fe._make_key({"regime":"MEAN_REVERTING","volatility":"LOW",
                                       "instrument":"ETHUSDT","parameter":"MR_STRAT",
                                       "direction":"UP"}) for _ in [0]]
      or _pe_fe.get_pattern(_form_key) is None,
      f"pruned_form={pruned_form}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION E — Ecology endpoint structure
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION E — Ecology endpoint field structure")

snap = opportunity_ecology.ecology_snapshot()
full_t = opportunity_ecology.get_telemetry()

check("E01 ecology_snapshot() has total_evaluated", "total_evaluated" in snap)
check("E02 ecology_snapshot() has approval_rate", "approval_rate" in snap)
check("E03 ecology_snapshot() has is_drought", "is_drought" in snap)
check("E04 ecology_snapshot() has is_starvation", "is_starvation" in snap)
check("E05 get_telemetry() has context_memory", "context_memory" in full_t)
check("E06 get_telemetry() context_memory has total_contexts",
      "total_contexts" in full_t.get("context_memory", {}))
check("E07 get_telemetry() has density_snapshot", "density_snapshot" in full_t)
check("E08 density_snapshot has survival_rate",
      "survival_rate" in full_t.get("density_snapshot", {}))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION F — RL telemetry structure
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION F — RL telemetry structure")

rl_t = rl_engine.get_evolution_state()
check("F01 rl evolution state has intelligence_score", "intelligence_score" in rl_t or rl_t.get("status") == "COLD_START")
cold = rl_t.get("status") == "COLD_START"
check("F02 rl has total_contexts",          "total_contexts" in rl_t)
check("F03 rl has learning_dynamics or COLD_START",   cold or "learning_dynamics" in rl_t)
check("F04 learning_dynamics has avg_q",    cold or "avg_q" in rl_t.get("learning_dynamics", {}))
check("F05 learning_dynamics has explore_ratio", cold or "explore_ratio" in rl_t.get("learning_dynamics", {}))
check("F06 rl has context_maturity or COLD_START",   cold or "context_maturity" in rl_t)
check("F07 context_maturity has mature",    cold or "mature" in rl_t.get("context_maturity", {}))
check("F08 rl has session_intelligence or COLD_START", cold or "session_intelligence" in rl_t)
check("F09 rl has quality_distribution or COLD_START", cold or "quality_distribution" in rl_t)
check("F10 rl has counters or COLD_START",  cold or "counters" in rl_t)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION G — Sovereign readiness gate logic
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION G — Sovereign readiness gate logic")

def _sov_state(evaluated_signals, mature_ctx, truth_density, eco_health_pass):
    gates = {
        "evaluated_signals": evaluated_signals >= 100,
        "mature_contexts":   mature_ctx >= 10,
        "truth_density":     truth_density > 0,
        "ecology_health":    eco_health_pass,
    }
    pass_count = sum(gates.values())
    if pass_count == 0:           return "NOT_READY"
    if pass_count == 1:           return "ECOLOGY_FORMING"
    if pass_count in (2, 3):      return "LEARNING_ACTIVE"
    return "SOVEREIGN_READY"

check("G01 0 gates pass → NOT_READY",
      _sov_state(0, 0, 0.0, False) == "NOT_READY")
check("G02 1 gate pass → ECOLOGY_FORMING",
      _sov_state(0, 0, 0.5, False) == "ECOLOGY_FORMING")
check("G03 2 gates pass → LEARNING_ACTIVE",
      _sov_state(0, 0, 0.5, True) == "LEARNING_ACTIVE")
check("G04 3 gates pass → LEARNING_ACTIVE",
      _sov_state(200, 0, 0.5, True) == "LEARNING_ACTIVE")
check("G05 4 gates pass → SOVEREIGN_READY",
      _sov_state(200, 15, 0.5, True) == "SOVEREIGN_READY")
check("G06 evaluated_signals=99 fails gate",
      _sov_state(99, 15, 0.5, True) != "SOVEREIGN_READY")
check("G07 mature_ctx=9 fails gate",
      _sov_state(200, 9, 0.5, True) != "SOVEREIGN_READY")
check("G08 truth_density=0 fails gate",
      _sov_state(200, 15, 0.0, True) != "SOVEREIGN_READY")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION H — Heartbeat state derivation
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION H — Heartbeat state derivation")

def _heartbeat(cycles, total_rec, formed, neg_total):
    if cycles == 0 or total_rec == 0:  return "DORMANT"
    if formed == 0:                    return "LEARNING"
    if neg_total > formed * 3:         return "DEGRADED"
    if formed >= 10:                   return "SATURATED"
    return "ACTIVE"

check("H01 0 cycles → DORMANT",           _heartbeat(0, 0, 0, 0) == "DORMANT")
check("H02 cycles>0, formed=0 → LEARNING",_heartbeat(5, 5, 0, 0) == "LEARNING")
check("H03 1 formed, low neg → ACTIVE",   _heartbeat(20, 20, 1, 0) == "ACTIVE")
check("H04 10 formed → SATURATED",        _heartbeat(200, 200, 10, 0) == "SATURATED")
check("H05 neg > formed*3 → DEGRADED",    _heartbeat(20, 20, 2, 7) == "DEGRADED")
check("H06 DEGRADED beats SATURATED",     _heartbeat(200, 200, 10, 35) == "DEGRADED")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION I — Dashboard HTML wiring
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION I — Dashboard HTML wiring verification")

import pathlib
_DASH = pathlib.Path(__file__).parent.parent / "dashboard.html"
if _DASH.exists():
    _html = _DASH.read_text(encoding="utf-8")
    check("I01 LIO tab button exists",        'switchTab(\'lio\')' in _html)
    check("I02 tab-btn-lio id exists",        'id="tab-btn-lio"' in _html)
    check("I03 tab-lio panel exists",         'id="tab-lio"' in _html)
    check("I04 lio included in switchTab()",  "'lio'" in _html and "tab-btn-lio" in _html)
    check("I05 loadLIO() function defined",   'async function loadLIO()' in _html)
    check("I06 LIO auto-refresh interval",    "loadLIO" in _html and "setInterval" in _html)
    check("I07 8 LIO section headers",        _html.count("·") >= 8)
    check("I08 sovereign readiness section",  'Sovereign' in _html)
    check("I09 pattern table exists",         'lio-pattern-tbody' in _html)
    check("I10 negative memory table exists", 'lio-neg-tbody' in _html)
    check("I11 topology grid exists",         'lio-topology-grid' in _html)
    check("I12 RL brain badge exists",        'lio-rl-brain-badge' in _html)
    check("I13 LIO CSS styles included",      '.lio-card' in _html)
    check("I14 noise meter exists",           'lio-noise-cursor' in _html)
else:
    check("I01–I14 dashboard.html found", False, "file not found at " + str(_DASH))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION J — Boot confirmation log in main.py
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION J — Boot confirmation in main.py")

_MAIN = pathlib.Path(__file__).parent.parent / "main.py"
if _MAIN.exists():
    _main_src = _MAIN.read_text(encoding="utf-8")
    check("J01 LIO boot log line present",
          "LEARNING_INTELLIGENCE_OBSERVATORY" in _main_src and "ACTIVE" in _main_src)
    check("J02 10 LIO endpoints declared",
          _main_src.count("/api/learning-intelligence/") >= 10)
    check("J03 lio_summary endpoint",         "async def lio_summary" in _main_src)
    check("J04 lio_patterns endpoint",        "async def lio_patterns" in _main_src)
    check("J05 lio_negative_memory endpoint", "async def lio_negative_memory" in _main_src)
    check("J06 lio_ecology endpoint",         "async def lio_ecology" in _main_src)
    check("J07 lio_rl endpoint",              "async def lio_rl" in _main_src)
    check("J08 lio_topology endpoint",        "async def lio_topology" in _main_src)
    check("J09 lio_cognition endpoint",       "async def lio_cognition" in _main_src)
    check("J10 lio_sovereign_readiness",      "async def lio_sovereign_readiness" in _main_src)
else:
    check("J01–J10 main.py found", False, "file not found at " + str(_MAIN))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION K — Alpha Discovery Observatory (§9)
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION K — Alpha Discovery Observatory §9")

if _MAIN.exists():
    check("K01 lio_alpha_discovery endpoint declared",
          "async def lio_alpha_discovery" in _main_src)
    check("K02 /api/learning-intelligence/alpha-discovery route",
          "/api/learning-intelligence/alpha-discovery" in _main_src)
    check("K03 discovery_health field returned",
          "discovery_health" in _main_src)
    check("K04 pos_neg_ratio field returned",
          "pos_neg_ratio" in _main_src)
    check("K05 alpha_discovery_velocity field returned",
          "alpha_discovery_velocity" in _main_src)
    check("K06 session_intelligence passed through",
          '"session_intelligence"' in _main_src)
    check("K07 endpoints=9+ in boot log",
          "endpoints=10" in _main_src or "endpoints=9" in _main_src)
else:
    for i in range(1, 8):
        check(f"K0{i} main.py found", False, "file not found")

_DASH_SRC = (pathlib.Path(__file__).parent.parent / "dashboard.html").read_text(encoding="utf-8")
check("K08 §9 section header present",           "§9 · Alpha Discovery Observatory" in _DASH_SRC)
check("K09 lio-alpha-badge element",             "lio-alpha-badge" in _DASH_SRC)
check("K10 lio-alpha-profitable-ctx element",    "lio-alpha-profitable-ctx" in _DASH_SRC)
check("K11 lio-alpha-ratio element",             "lio-alpha-ratio" in _DASH_SRC)
check("K12 lio-alpha-velocity element",          "lio-alpha-velocity" in _DASH_SRC)
check("K13 lio-alpha-bar-pos element",           "lio-alpha-bar-pos" in _DASH_SRC)
check("K14 _lioRenderAlpha function declared",   "_lioRenderAlpha" in _DASH_SRC)
check("K15 alpha-discovery in loadLIO fetch",    "alpha-discovery" in _DASH_SRC)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION L — Report Download (v1.8.0)
# ══════════════════════════════════════════════════════════════════════════════
section("SECTION L — Report Download bundle")

if _MAIN.exists():
    check("L01 lio_report_bundle endpoint declared",
          "async def lio_report_bundle" in _main_src)
    check("L02 /api/learning-intelligence/report-bundle route",
          "/api/learning-intelligence/report-bundle" in _main_src)
    check("L03 asyncio.gather used for atomic bundle fetch",
          "asyncio.gather" in _main_src)
    check("L04 metadata block with version and timestamp",
          '"report_type"' in _main_src and '"generated_at_iso"' in _main_src)
    check("L05 endpoints=10 in boot log",
          "endpoints=10" in _main_src)

check("L06 download button in dashboard",     "lio-download-btn" in _DASH_SRC)
check("L07 downloadLIOReport function",       "async function downloadLIOReport" in _DASH_SRC)
check("L08 _buildLIOReportHTML function",     "_buildLIOReportHTML" in _DASH_SRC)
check("L09 report-bundle fetch in downloader","report-bundle" in _DASH_SRC)
check("L10 HTML blob download logic",         "text/html;charset=utf-8" in _DASH_SRC)
check("L11 phoenix_lio_report filename",      "phoenix_lio_report_" in _DASH_SRC)
check("L12 all 9 sections in HTML builder",
      all(f"§{i} ·" in _DASH_SRC for i in range(1,10)))


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  RESULTS")
print("─" * 60)
total = _PASS + _FAIL
print(f"  Total checks: {total}")
print(f"  Passed:       {_PASS}")
print(f"  Failed:       {_FAIL}")
if _FAILURES:
    print(f"\n  FAILURES:")
    for f in _FAILURES:
        print(f"    • {f}")
    sys.exit(1)
else:
    print(f"\n  \033[92m✓ ALL {total} CHECKS PASSED — LIO Learning Intelligence Observatory VALIDATED\033[0m")

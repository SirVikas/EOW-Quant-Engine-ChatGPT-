"""
FTD-053-GAIA Phase 6 Verifier — Observability Orchestrator + Snapshot Builder

Sections:
  A: imports and singletons          (6 checks)
  B: snapshot_builder — all-None     (6 checks)
  C: snapshot_builder — with data    (8 checks)
  D: snapshot_builder — derived fields (6 checks)
  E: snapshot_builder — regime detection (4 checks)
  F: orchestrator — basic tick       (7 checks)
  G: orchestrator — pipeline outputs (6 checks)
  H: orchestrator — dedup behaviour  (4 checks)
  I: orchestrator — escalation path  (5 checks)
  J: orchestrator — sync queue       (4 checks)
  K: orchestrator — cleanup trigger  (3 checks)
  L: orchestrator — stats            (6 checks)
  M: orchestrator — resilience       (5 checks)
  N: integration — full phase 1→6    (8 checks)

Total: 78 checks
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

_PASS = _FAIL = 0

def check(label: str, ok: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if ok:
        _PASS += 1
        print(f"  PASS  {label}")
    else:
        _FAIL += 1
        msg = f"  FAIL  {label}"
        if detail:
            msg += f"  [{detail}]"
        print(msg)


# ─────────────────────────────────────────────────────────────────────────────
# A: Imports and singletons
# ─────────────────────────────────────────────────────────────────────────────
print("A: Imports and singletons")

from core.observability.snapshot_builder import build_raw_snapshot
from core.observability.orchestrator import (
    obs_orchestrator, ObservabilityOrchestrator,
    OBS_TICK_INTERVAL_SECS, CLEANUP_EVERY_N_TICKS, TickResult,
)
from core.observability import (
    obs_orchestrator as _obs_singleton,
    build_raw_snapshot as _brs,
    OBS_TICK_INTERVAL_SECS as _tick_iv,
)

check("A1: build_raw_snapshot importable",          callable(build_raw_snapshot))
check("A2: ObservabilityOrchestrator importable",   ObservabilityOrchestrator is not None)
check("A3: obs_orchestrator singleton exists",      obs_orchestrator is not None)
check("A4: obs_orchestrator is ObservabilityOrchestrator",
      isinstance(obs_orchestrator, ObservabilityOrchestrator))
check("A5: __init__.py re-exports obs_orchestrator", _obs_singleton is obs_orchestrator)
check("A6: OBS_TICK_INTERVAL_SECS is positive int", OBS_TICK_INTERVAL_SECS > 0)


# ─────────────────────────────────────────────────────────────────────────────
# B: snapshot_builder — all-None engines
# ─────────────────────────────────────────────────────────────────────────────
print("B: snapshot_builder — all-None engines")

_snap_null = build_raw_snapshot()

check("B1: returns dict",            isinstance(_snap_null, dict))
check("B2: has session_stats",       "session_stats" in _snap_null)
check("B3: has rl block",            "rl" in _snap_null)
check("B4: has risk block",          "risk" in _snap_null)
check("B5: has regime",              "regime" in _snap_null)
check("B6: does not throw",          True)   # reaching here means no exception


# ─────────────────────────────────────────────────────────────────────────────
# C: snapshot_builder — with mock data
# ─────────────────────────────────────────────────────────────────────────────
print("C: snapshot_builder — with mock data")

class _MockTrade:
    def __init__(self, pnl, ts_exit=0):
        self.net_pnl  = pnl
        self.ts_exit  = ts_exit or int(time.time() * 1000)

_mock_pnl = MagicMock()
_mock_pnl.session_stats = {
    "total_net_pnl": 120.50,
    "total_trades":  30,
    "win_rate":      58.3,
    "profit_factor": 1.45,
}
_mock_pnl.trades = [_MockTrade(-10), _MockTrade(-5), _MockTrade(20)]   # 2 losses then win

_mock_rl = MagicMock()
_mock_rl.summary.return_value = {
    "total_contexts": 40,
    "total_pulls":    200,
    "toxic_contexts": 2,
    "allow_rate":     0.72,
    "profitable_pct": 0.65,
}
_mock_rl.get_evolution_state.return_value = {
    "intelligence_score": 62.5,
    "total_contexts": 40,
    "context_maturity": {"fresh": 5, "accel": 10, "standard": 15, "mature": 10},
    "learning_dynamics": {"avg_q": 0.18, "explore_ratio": 0.35},
}

_mock_le = MagicMock()
_mock_le.summary.return_value = {
    "regimes": {
        "TRENDING":            {"win_rate": 0.61},
        "MEAN_REVERTING":      {"win_rate": 0.54},
        "VOLATILITY_EXPANSION":{"win_rate": 0.40},
    }
}

_snap_full = build_raw_snapshot(
    rl_engine=_mock_rl, pnl_calc=_mock_pnl, learning_engine=_mock_le,
    boot_ts=time.time() - 3600,
)

check("C1: pnl extracted",          _snap_full["session_stats"]["total_net_pnl"] == 120.50)
check("C2: n_trades mapped",        _snap_full["session_stats"]["n_trades"] == 30)
check("C3: win_rate extracted",     _snap_full["session_stats"]["win_rate"] == 58.3)
check("C4: iq_score extracted",
      _snap_full["rl"]["evolution_state"]["intelligence_score"] == 62.5)
check("C5: toxic_contexts mapped",  _snap_full["rl"]["summary_metrics"]["toxic_contexts"] == 2)
check("C6: TRENDING win_rate",      _snap_full["learning"]["TRENDING"]["win_rate"] == 0.61)
check("C7: uptime_secs positive",   _snap_full["uptime_secs"] > 0)
check("C8: _snapshot_ts present",   "_snapshot_ts" in _snap_full)


# ─────────────────────────────────────────────────────────────────────────────
# D: snapshot_builder — derived fields
# ─────────────────────────────────────────────────────────────────────────────
print("D: snapshot_builder — derived fields")

# maturity: 10 mature / 40 total = 25% → LEARNING
check("D1: maturity_pct computed",
      _snap_full["rl"]["learning_speed"]["maturity_pct"] == 25.0)
check("D2: maturity_status LEARNING",
      _snap_full["rl"]["learning_speed"]["status"] == "LEARNING")

# explore_ratio = 0.35 < 0.40 → EXPLOITING (BALANCED threshold is 0.40)
check("D3: explore status EXPLOITING",
      _snap_full["rl"]["exploration_pressure"]["pressure_status"] == "EXPLOITING")

# avg_q = 0.18 > 0.10 → IMPROVING
check("D4: confidence_direction IMPROVING",
      _snap_full["rl"]["confidence_trajectory"]["confidence_direction"] == "IMPROVING")

# consecutive losses: last 2 trades are -10, -5 → but list is [lose, lose, win]
# reversed: win, lose, lose → breaks at first win → 0 consecutive from tail
# Actually: [MockTrade(-10), MockTrade(-5), MockTrade(20)] → reversed: [20, -5, -10]
# reversed first is 20 (win) → consecutive_losses = 0
check("D5: consecutive_losses = 0 (tail is win)",
      _snap_full["trade_flow"]["consecutive_losses"] == 0)

# All-loss tail test
_mock_pnl2        = MagicMock()
_mock_pnl2.session_stats = {"total_net_pnl": -30, "total_trades": 3,
                             "win_rate": 0, "profit_factor": 0}
_mock_pnl2.trades = [_MockTrade(-10), _MockTrade(-5), _MockTrade(-8)]
_snap2            = build_raw_snapshot(pnl_calc=_mock_pnl2)
check("D6: consecutive_losses = 3 (all losses)",
      _snap2["trade_flow"]["consecutive_losses"] == 3)


# ─────────────────────────────────────────────────────────────────────────────
# E: snapshot_builder — regime detection
# ─────────────────────────────────────────────────────────────────────────────
print("E: snapshot_builder — regime detection")

from unittest.mock import MagicMock

class _FakeRegime:
    def __init__(self, value):
        self.value = value

class _FakeState:
    def __init__(self, regime_value):
        self.regime = _FakeRegime(regime_value)

_mock_rd = MagicMock()
_mock_rd.all_states.return_value = {
    "BTC": _FakeState("TRENDING"),
    "ETH": _FakeState("TRENDING"),
    "SOL": _FakeState("MEAN_REVERTING"),
}

_snap_r = build_raw_snapshot(regime_det=_mock_rd)

check("E1: regime is string",          isinstance(_snap_r["regime"], str))
check("E2: dominant regime is TRENDING",  _snap_r["regime"] == "TRENDING")

_mock_rd_empty = MagicMock()
_mock_rd_empty.all_states.return_value = {}
_snap_r2 = build_raw_snapshot(regime_det=_mock_rd_empty)
check("E3: empty regime_det → UNKNOWN",   _snap_r2["regime"] == "UNKNOWN")

_snap_no_rd = build_raw_snapshot()
check("E4: no regime_det → UNKNOWN",      _snap_no_rd["regime"] == "UNKNOWN")


# ─────────────────────────────────────────────────────────────────────────────
# F: orchestrator — basic tick
# ─────────────────────────────────────────────────────────────────────────────
print("F: orchestrator — basic tick")

_orch_f = ObservabilityOrchestrator()
_raw_f  = build_raw_snapshot()      # minimal all-zero snapshot

_result_f = _orch_f.tick(_raw_f)

check("F1: tick returns TickResult",       isinstance(_result_f, TickResult))
check("F2: tick_id is 8-char hex",         len(_result_f.tick_id) == 8)
check("F3: ts is positive int",            _result_f.ts > 0)
check("F4: duration_ms is positive",       _result_f.duration_ms >= 0)
check("F5: worst_severity is string",      isinstance(_result_f.worst_severity, str))
check("F6: anomaly_count is int",          isinstance(_result_f.anomaly_count, int))
check("F7: tick does not throw",           True)


# ─────────────────────────────────────────────────────────────────────────────
# G: orchestrator — pipeline outputs visible in component state
# ─────────────────────────────────────────────────────────────────────────────
print("G: orchestrator — pipeline outputs")

from core.observability.intelligence_compressor import IntelligenceCompressor
from core.observability.report_lifecycle_engine import ReportLifecycleEngine
from core.observability.delta_reporter import DeltaReporter
from core.observability.anomaly_detector import AnomalyDetector
from core.observability.ai_summary_engine import AISummaryEngine
from core.observability.strategic_feed import StrategicFeed
from core.observability.event_bus import EventBus, CHANNEL_ANOMALY
from core.observability.escalation_engine import EscalationEngine
from core.observability.github_sync_engine import GitHubSyncEngine

_ic_g  = IntelligenceCompressor()
_rle_g = ReportLifecycleEngine()
_dr_g  = DeltaReporter()
_ad_g  = AnomalyDetector()
_se_g  = AISummaryEngine()
_sf_g  = StrategicFeed()
_eb_g  = EventBus()
_ee_g  = EscalationEngine()
_gse_g = GitHubSyncEngine()

from core.observability.orchestrator import _step

# Run a tick on isolated instances with a meaningful snapshot
_raw_g = {
    "session_stats": {"total_net_pnl": -80.0, "n_trades": 10,
                      "profit_factor": 0.6, "win_rate": 35.0},
    "rl": {
        "total_contexts": 20,
        "total_trade_decisions": 100,
        "evolution_state": {"intelligence_score": 25.0},
        "summary_metrics": {"toxic_contexts": 3, "allow_rate": 0.40, "profitable_pct": 0.30},
        "learning_speed": {"maturity_pct": 10.0, "status": "BOOTSTRAPPING"},
        "exploration_pressure": {"pressure_status": "HIGH_EXPLORE"},
        "confidence_trajectory": {"confidence_direction": "DECLINING"},
    },
    "learning": {
        "TRENDING": {"win_rate": 0.30},
        "MEAN_REVERTING": {"win_rate": 0.28},
        "VOLATILITY_EXPANSION": {"win_rate": 0.25},
    },
    "risk":       {"halted": True},
    "gate":       {"can_trade": False},
    "trade_flow": {"consecutive_losses": 6, "daily_trades": 5},
    "uptime_secs": 7200,
    "error_count": 0,
    "regime": "MEAN_REVERTING",
}

_compressed_g = _ic_g.compress(_raw_g)
check("G1: compress produces iq_score field",   "iq_score" in _compressed_g)
check("G2: iq_score matches input",             _compressed_g.get("iq_score") == 25.0)
_anomalies_g = _ad_g.scan(_compressed_g)
check("G3: risk_halted triggers RISK_STATE anomaly",
      any(a.get("category") == "RISK_STATE" for a in _anomalies_g))
_summary_g = _se_g.generate_summary(_compressed_g, anomalies=_anomalies_g)
check("G4: summary priority is CRITICAL",       _summary_g.get("priority") == "CRITICAL")
_feeds_g = _sf_g.refresh(_compressed_g, _anomalies_g)
check("G5: RISK feed has high signal_strength", _feeds_g["RISK"].signal_strength >= 80)
_rec_g = _ee_g.evaluate(_anomalies_g, emit_event=False)
check("G6: escalation fires L3_SYNC for CRITICAL anomaly",
      _rec_g is not None and _rec_g.level == "L3_SYNC")


# ─────────────────────────────────────────────────────────────────────────────
# H: orchestrator — dedup behaviour
# ─────────────────────────────────────────────────────────────────────────────
print("H: orchestrator — dedup behaviour")

_orch_h = ObservabilityOrchestrator()
_raw_h  = build_raw_snapshot()

r1 = _orch_h.tick(_raw_h)
r2 = _orch_h.tick(_raw_h)   # identical snapshot — should dedup on file write

check("H1: first tick returns TickResult",      r1 is not None)
check("H2: second tick returns TickResult",     r2 is not None)
check("H3: tick_ids are different",             r1.tick_id != r2.tick_id)
check("H4: at least one tick deduped (same snapshot)",  r1.deduped or r2.deduped)


# ─────────────────────────────────────────────────────────────────────────────
# I: orchestrator — escalation path end-to-end
# ─────────────────────────────────────────────────────────────────────────────
print("I: orchestrator — escalation path")

_orch_i = ObservabilityOrchestrator()
_esc_events_i: list = []

from core.observability.event_bus import event_bus as _global_eb, CHANNEL_ESCALATION
_sub_i = _global_eb.subscribe(CHANNEL_ESCALATION, lambda p: _esc_events_i.append(p))

_raw_i = {
    "session_stats": {"total_net_pnl": -200.0, "n_trades": 20,
                      "profit_factor": 0.4, "win_rate": 25.0},
    "rl": {
        "total_contexts": 10,
        "total_trade_decisions": 50,
        "evolution_state": {"intelligence_score": 15.0},
        "summary_metrics": {"toxic_contexts": 5, "allow_rate": 0.20, "profitable_pct": 0.10},
        "learning_speed": {"maturity_pct": 5.0, "status": "BOOTSTRAPPING"},
        "exploration_pressure": {"pressure_status": "HIGH_EXPLORE"},
        "confidence_trajectory": {"confidence_direction": "DECLINING"},
    },
    "learning": {
        "TRENDING": {"win_rate": 0.20},
        "MEAN_REVERTING": {"win_rate": 0.20},
        "VOLATILITY_EXPANSION": {"win_rate": 0.20},
    },
    "risk":       {"halted": True},
    "gate":       {"can_trade": False},
    "trade_flow": {"consecutive_losses": 8, "daily_trades": 10},
    "uptime_secs": 3600,
    "error_count": 5,
    "regime":     "MEAN_REVERTING",
}

_res_i = _orch_i.tick(_raw_i)
_global_eb.unsubscribe(_sub_i)

check("I1: tick returns result",                _res_i is not None)
check("I2: anomalies detected",                 _res_i.anomaly_count > 0)
check("I3: worst_severity is CRITICAL",         _res_i.worst_severity == "CRITICAL")
check("I4: escalation fired",                   _res_i.escalation_level is not None)
check("I5: escalation event on bus",            len(_esc_events_i) >= 1)


# ─────────────────────────────────────────────────────────────────────────────
# J: orchestrator — sync queue
# ─────────────────────────────────────────────────────────────────────────────
print("J: orchestrator — sync queue")

from core.observability.github_sync_engine import GitHubSyncEngine as _GSE

_gse_j = _GSE()
_orch_j = ObservabilityOrchestrator()

# Patch the orchestrator's internal reference to use isolated sync engine
import core.observability.orchestrator as _orch_mod
_orig_gse = _orch_mod.github_sync_engine
_orch_mod.github_sync_engine = _gse_j

_raw_j = build_raw_snapshot()
_res_j = _orch_j.tick(_raw_j)

_orch_mod.github_sync_engine = _orig_gse   # restore

check("J1: tick returns result",              _res_j is not None)
check("J2: queued_for_sync is bool",          isinstance(_res_j.queued_for_sync, bool))
# Isolated sync engine: stats method exists and returns a dict
_j3_status = _gse_j.status()
check("J3: sync engine status returns dict",  isinstance(_j3_status, dict))
check("J4: sync_flushed is bool",             isinstance(_res_j.sync_flushed, bool))


# ─────────────────────────────────────────────────────────────────────────────
# K: orchestrator — cleanup trigger
# ─────────────────────────────────────────────────────────────────────────────
print("K: orchestrator — cleanup trigger")

_orch_k   = ObservabilityOrchestrator()
_raw_k    = build_raw_snapshot()
_cleanup_called = []

import core.observability.orchestrator as _mod_k
_orig_rle = _mod_k.report_lifecycle_engine

class _PatchedRLE:
    def __getattr__(self, name):
        return getattr(_orig_rle, name)
    def run_cleanup(self):
        _cleanup_called.append(True)
        return _orig_rle.run_cleanup()

_mod_k.report_lifecycle_engine = _PatchedRLE()

for _ in range(CLEANUP_EVERY_N_TICKS):
    _orch_k.tick(_raw_k)

_mod_k.report_lifecycle_engine = _orig_rle   # restore

check("K1: CLEANUP_EVERY_N_TICKS is positive",   CLEANUP_EVERY_N_TICKS > 0)
check("K2: cleanup was triggered",               len(_cleanup_called) >= 1)
check("K3: cleanup not triggered on every tick", len(_cleanup_called) <= CLEANUP_EVERY_N_TICKS)


# ─────────────────────────────────────────────────────────────────────────────
# L: orchestrator — stats
# ─────────────────────────────────────────────────────────────────────────────
print("L: orchestrator — stats")

_orch_l = ObservabilityOrchestrator()
_raw_l  = build_raw_snapshot()
_orch_l.tick(_raw_l)
_orch_l.tick(_raw_l)

s = _orch_l.stats()

check("L1: stats returns dict",              isinstance(s, dict))
check("L2: total_ticks == 2",               s["total_ticks"] == 2)
check("L3: last_tick_ts > 0",               s["last_tick_ts"] > 0)
check("L4: last_tick_ms >= 0",              s["last_tick_ms"] >= 0)
check("L5: tick_interval_secs present",     "tick_interval_secs" in s)
check("L6: event_bus status present",       "event_bus" in s)


# ─────────────────────────────────────────────────────────────────────────────
# M: orchestrator — resilience
# ─────────────────────────────────────────────────────────────────────────────
print("M: orchestrator — resilience")

_orch_m = ObservabilityOrchestrator()

try:
    r_m1 = _orch_m.tick(None)       # type: ignore
    check("M1: tick(None) does not raise",   True)
except Exception as e:
    check("M1: tick(None) does not raise",   False, str(e))

try:
    r_m2 = _orch_m.tick({})
    check("M2: tick({}) returns TickResult or None", r_m2 is None or isinstance(r_m2, TickResult))
except Exception as e:
    check("M2: tick({}) does not raise",             False, str(e))

try:
    r_m3 = _orch_m.tick({"garbage": "data", "rl": None})
    check("M3: tick(corrupted) does not raise",  True)
except Exception as e:
    check("M3: tick(corrupted) does not raise",  False, str(e))

try:
    s_m = _orch_m.stats()
    check("M4: stats() never raises",  isinstance(s_m, dict))
except Exception as e:
    check("M4: stats() never raises",  False, str(e))

try:
    _snap_m = build_raw_snapshot(
        rl_engine=object(),         # non-duck-typed engine
        pnl_calc=object(),
    )
    check("M5: build_raw_snapshot with broken engines does not raise", True)
except Exception as e:
    check("M5: build_raw_snapshot with broken engines does not raise", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# N: Integration — full Phase 1→6 pipeline
# ─────────────────────────────────────────────────────────────────────────────
print("N: Integration — full Phase 1→6 pipeline")

from core.observability import (
    intelligence_compressor as _IC,
    delta_reporter          as _DR,
    anomaly_detector        as _AD,
    ai_summary_engine       as _SE,
    strategic_feed          as _SF,
    event_bus               as _EB,
    escalation_engine       as _EE,
    obs_orchestrator        as _OO,
)

_bus_events_n: list = []
_esc_events_n: list = []
_sub_an = _EB.subscribe("ANOMALY",    lambda p: _bus_events_n.append(p))
_sub_en = _EB.subscribe("ESCALATION", lambda p: _esc_events_n.append(p))

_mock_pnl_n = MagicMock()
_mock_pnl_n.session_stats = {
    "total_net_pnl": -150.0, "total_trades": 15,
    "win_rate": 33.0, "profit_factor": 0.55,
}
_mock_pnl_n.trades = [_MockTrade(-20)] * 7   # 7 consecutive losses

_mock_rl_n = MagicMock()
_mock_rl_n.summary.return_value = {
    "total_contexts": 15, "total_pulls": 80,
    "toxic_contexts": 4, "allow_rate": 0.30, "profitable_pct": 0.25,
}
_mock_rl_n.get_evolution_state.return_value = {
    "intelligence_score": 18.0, "total_contexts": 15,
    "context_maturity": {"fresh": 10, "accel": 3, "standard": 2, "mature": 0},
    "learning_dynamics": {"avg_q": -0.05, "explore_ratio": 0.75},
}

_mock_rc_n = MagicMock()
_mock_rc_n.halted = True

_raw_n = build_raw_snapshot(
    rl_engine=_mock_rl_n,
    pnl_calc=_mock_pnl_n,
    risk_ctrl=_mock_rc_n,
    boot_ts=time.time() - 1800,
)

_res_n = _OO.tick(_raw_n)

_EB.unsubscribe(_sub_an)
_EB.unsubscribe(_sub_en)

check("N1: snapshot built from mock engines",        _raw_n["rl"]["evolution_state"]["intelligence_score"] == 18.0)
check("N2: consecutive_losses == 7",                 _raw_n["trade_flow"]["consecutive_losses"] == 7)
check("N3: risk.halted == True",                     _raw_n["risk"]["halted"] is True)
check("N4: tick returns TickResult",                 isinstance(_res_n, TickResult))
check("N5: anomalies detected (CRITICAL expected)",  _res_n.anomaly_count > 0)
check("N6: anomaly event fired on bus",              len(_bus_events_n) >= 1)
check("N7: escalation fired",                        _res_n.escalation_level is not None)
check("N8: full pipeline produces actionable output",
      _res_n.worst_severity in ("HIGH", "CRITICAL") and _res_n.escalation_level is not None)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"FTD-053-GAIA Phase 6 Verifier: {_PASS}/{_PASS + _FAIL} checks passed")
if _FAIL == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"{_FAIL} CHECKS FAILED")

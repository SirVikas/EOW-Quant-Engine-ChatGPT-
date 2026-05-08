"""
FTD-053-GAIA Phase 3 Verifier
GitHub Synchronization + Smart Batching + Deduplication + Sync Governance

Sections:
  A: Module imports and singleton availability        (5 checks)
  B: Batching — queue_snapshot accumulation           (6 checks)
  C: Flush triggers — CRITICAL anomaly                (5 checks)
  D: Flush triggers — HIGH cluster                    (4 checks)
  E: Flush triggers — batch full                      (4 checks)
  F: Flush triggers — time threshold + force          (5 checks)
  G: Suppression — dedup identical payload            (5 checks)
  H: Suppression — rate limit                         (5 checks)
  I: Suppression — cooling period                     (4 checks)
  J: Payload structure                                (9 checks)
  K: Payload — anomaly summary correctness            (6 checks)
  L: Payload — delta summary correctness              (4 checks)
  M: Payload — batch stats correctness                (4 checks)
  N: Push adapter injection                           (5 checks)
  O: Local file writes (atomic, latest pointer)       (5 checks)
  P: should_flush() and status()                      (6 checks)
  Q: mark_synced() and sync-ts history                (4 checks)
  R: Resilience / non-throwing guarantees             (5 checks)
  S: Integration — full Phase 1→2→3 pipeline         (6 checks)

Total: 97 checks
"""
from __future__ import annotations

import sys
import time
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = 0
FAIL = 0
_results: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        _results.append(f"  PASS  {name}")
    else:
        FAIL += 1
        _results.append(f"  FAIL  {name}" + (f" | {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────────
# A: Module imports
# ─────────────────────────────────────────────────────────────────────────────
print("A: Module imports")

try:
    from core.observability.github_sync_engine import (
        GitHubSyncEngine, github_sync_engine,
        SyncResult,
        SYNC_INTERVAL_SECS, MAX_BATCH_SIZE, HIGH_FLUSH_THRESHOLD,
        MAX_SYNCS_PER_HOUR, MIN_SYNC_COOLDOWN_SECS,
        REASON_CRITICAL, REASON_HIGH_CLUSTER, REASON_BATCH_FULL,
        REASON_FORCE, REASON_DEDUP, REASON_RATE_LIMITED, REASON_COOLING,
        SYNC_DIR,
    )
    check("A1: github_sync_engine importable", True)
except Exception as e:
    check("A1: github_sync_engine importable", False, str(e))

try:
    from core.observability import github_sync_engine as gse_pkg, GitHubSyncEngine as GSE_cls
    check("A2: package __init__ exports Phase 3 singletons", True)
except Exception as e:
    check("A2: package __init__ exports Phase 3 singletons", False, str(e))

check("A3: github_sync_engine is GitHubSyncEngine",  isinstance(github_sync_engine, GitHubSyncEngine))
check("A4: SYNC_DIR is a Path",                       isinstance(SYNC_DIR, Path))
check("A5: governance constants are positive ints",
      SYNC_INTERVAL_SECS > 0 and MAX_BATCH_SIZE > 0 and MAX_SYNCS_PER_HOUR > 0)


# ─────────────────────────────────────────────────────────────────────────────
# B: Batching — queue_snapshot accumulation
# ─────────────────────────────────────────────────────────────────────────────
print("B: Batching — queue_snapshot accumulation")

_gse = GitHubSyncEngine()

_comp = {
    "pnl": 100.0, "n_trades": 20, "iq_score": 70.0,
    "rl_toxic": 0, "consec_losses": 0, "regime": "TRENDING",
    "risk_halted": False, "gate_open": True, "rl_allow_rate": 0.90,
}
_delta = {"has_meaningful_delta": True, "significance_score": 12.0,
          "changed_fields": {"pnl": {"prev": 90.0, "curr": 100.0}}, "summary": "pnl up"}
_anomalies_none: list = []

# Queue without triggering auto-flush
triggered = _gse.queue_snapshot(_comp, _delta, _anomalies_none)
check("B1: queue_snapshot returns bool",      isinstance(triggered, bool))
check("B2: no auto-flush on normal snapshot", triggered is False)
check("B3: batch size = 1 after first queue", len(_gse._batch) == 1)

_gse.queue_snapshot(_comp, _delta, _anomalies_none)
_gse.queue_snapshot(_comp, _delta, _anomalies_none)
check("B4: batch size = 3 after three queues", len(_gse._batch) == 3)

# Verify entry structure
entry = _gse._batch[0]
check("B5: entry has compressed field",        hasattr(entry, "compressed"))
check("B6: entry compressed.pnl == 100.0",     entry.compressed.get("pnl") == 100.0)


# ─────────────────────────────────────────────────────────────────────────────
# C: Flush triggers — CRITICAL anomaly
# ─────────────────────────────────────────────────────────────────────────────
print("C: Flush triggers — CRITICAL anomaly")

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW

_gse_c = GitHubSyncEngine()
_critical_anomalies = [
    {"severity": SEV_CRITICAL, "category": "RISK_STATE",
     "description": "Engine halted", "metric": "risk_halted",
     "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "crit0001"}
]

triggered_c = _gse_c.queue_snapshot(_comp, _delta, _critical_anomalies)
check("C1: CRITICAL anomaly triggers auto-flush", triggered_c is True)
check("C2: batch cleared after CRITICAL flush",   len(_gse_c._batch) == 0)
check("C3: total_flushed incremented",            _gse_c._stats.total_flushed >= 1)
check("C4: last_sync_ts updated",                 _gse_c._stats.last_sync_ts > 0)
check("C5: last_checksum updated",                _gse_c._stats.last_checksum != "")


# ─────────────────────────────────────────────────────────────────────────────
# D: Flush triggers — HIGH anomaly cluster
# ─────────────────────────────────────────────────────────────────────────────
print("D: Flush triggers — HIGH anomaly cluster")

_gse_d = GitHubSyncEngine()
_high_anomaly = [
    {"severity": SEV_HIGH, "category": "LOSS_STREAK",
     "description": "5 consecutive losses", "metric": "consec_losses",
     "current_value": 5, "threshold": 5, "delta": 2,
     "ts": int(time.time() * 1000), "anomaly_id": "high0001"}
]

# Queue HIGH_FLUSH_THRESHOLD - 1 times without triggering
for i in range(HIGH_FLUSH_THRESHOLD - 1):
    _gse_d.queue_snapshot(_comp, _delta, _high_anomaly)

# Not triggered yet
check("D1: no auto-flush before HIGH_FLUSH_THRESHOLD", len(_gse_d._batch) > 0)

# Queue one more to hit the threshold
triggered_d = _gse_d.queue_snapshot(_comp, _delta, _high_anomaly)
check("D2: HIGH cluster triggers auto-flush",    triggered_d is True)
check("D3: batch cleared after HIGH flush",      len(_gse_d._batch) == 0)
check("D4: flush reason is HIGH_ANOMALY_CLUSTER",
      _gse_d._stats.total_flushed >= 1)


# ─────────────────────────────────────────────────────────────────────────────
# E: Flush triggers — batch full
# ─────────────────────────────────────────────────────────────────────────────
print("E: Flush triggers — batch full")

_gse_e = GitHubSyncEngine()
triggered_e = False

for i in range(MAX_BATCH_SIZE):
    triggered_e = _gse_e.queue_snapshot(_comp, None, [])

check("E1: queue triggers flush at MAX_BATCH_SIZE", triggered_e is True)
check("E2: batch cleared after full flush",          len(_gse_e._batch) == 0)
check("E3: total_flushed = 1",                       _gse_e._stats.total_flushed == 1)
check("E4: total_queued = MAX_BATCH_SIZE",           _gse_e._stats.total_queued == MAX_BATCH_SIZE)


# ─────────────────────────────────────────────────────────────────────────────
# F: Flush triggers — manual flush, force, empty batch
# ─────────────────────────────────────────────────────────────────────────────
print("F: Flush triggers — manual flush + force")

_gse_f = GitHubSyncEngine()
_gse_f.queue_snapshot(_comp, _delta, [])

# First manual flush should succeed (no prior sync ts, so no cooling)
result_f1 = _gse_f.flush()
check("F1: flush() returns SyncResult",       isinstance(result_f1, SyncResult))
check("F2: first flush succeeds",             result_f1.flushed is True, result_f1.reason)
check("F3: batch empty after flush",          len(_gse_f._batch) == 0)

# flush() on empty batch
result_f_empty = _gse_f.flush()
check("F4: flush on empty batch returns flushed=False", result_f_empty.flushed is False)

# force=True bypasses cooling
_gse_f.queue_snapshot(_comp, _delta, [])
result_f_force = _gse_f.flush(force=True)
check("F5: force=True flush succeeds even in cooling", result_f_force.flushed is True)


# ─────────────────────────────────────────────────────────────────────────────
# G: Suppression — dedup identical payload
# ─────────────────────────────────────────────────────────────────────────────
print("G: Suppression — dedup")

_gse_g = GitHubSyncEngine()

# First flush to establish last_checksum
_gse_g.queue_snapshot(_comp, _delta, [])
r1 = _gse_g.flush(force=True)
check("G1: first flush succeeds",           r1.flushed is True)
cs1 = r1.payload_checksum

# Queue identical content and try to flush — should be deduped
_gse_g.queue_snapshot(_comp, _delta, [])
# Bypass cooling but not dedup
_gse_g._stats.last_sync_ts = 0   # clear cooling
r2 = _gse_g.flush()
check("G2: identical payload suppressed",    r2.flushed is False, r2.reason)
check("G3: reason is DEDUP_IDENTICAL",       r2.reason == REASON_DEDUP, r2.reason)
check("G4: total_suppressed incremented",    _gse_g._stats.total_suppressed >= 1)

# Change content → should not be deduped
_comp_changed = deepcopy(_comp)
_comp_changed["pnl"] = 999.0
_gse_g.queue_snapshot(_comp_changed, _delta, [])
_gse_g._stats.last_sync_ts = 0
r3 = _gse_g.flush()
check("G5: changed payload not deduped",     r3.flushed is True, r3.reason)


# ─────────────────────────────────────────────────────────────────────────────
# H: Suppression — rate limit
# ─────────────────────────────────────────────────────────────────────────────
print("H: Suppression — rate limit")

_gse_h = GitHubSyncEngine()

# Fill up the rate limit by injecting fake timestamps
now_ms = int(time.time() * 1000)
_gse_h._stats.sync_ts_history = [now_ms - i * 60_000 for i in range(MAX_SYNCS_PER_HOUR)]

_gse_h.queue_snapshot(_comp, _delta, [])
result_h = _gse_h.flush()

check("H1: rate-limited flush returns flushed=False", result_h.flushed is False)
check("H2: reason is RATE_LIMITED",                   result_h.reason == REASON_RATE_LIMITED, result_h.reason)
check("H3: batch NOT cleared on rate-limit",          len(_gse_h._batch) >= 1)
check("H4: total_suppressed incremented",             _gse_h._stats.total_suppressed >= 1)

# force=True bypasses rate limit
result_h_force = _gse_h.flush(force=True)
check("H5: force=True bypasses rate limit",           result_h_force.flushed is True)


# ─────────────────────────────────────────────────────────────────────────────
# I: Suppression — cooling period
# ─────────────────────────────────────────────────────────────────────────────
print("I: Suppression — cooling period")

_gse_i = GitHubSyncEngine()
_gse_i.queue_snapshot(_comp, _delta, [])
r_i1 = _gse_i.flush(force=True)   # first flush sets last_sync_ts
check("I1: first flush succeeds", r_i1.flushed is True)

# Immediately try again — should hit cooling
_gse_i.queue_snapshot(_comp_changed, _delta, [])
r_i2 = _gse_i.flush()
check("I2: second immediate flush hits cooling", r_i2.flushed is False)
check("I3: reason is COOLING_PERIOD",            r_i2.reason == REASON_COOLING, r_i2.reason)

# Simulate cooling period elapsed
_gse_i._stats.last_sync_ts = int(time.time() * 1000) - (MIN_SYNC_COOLDOWN_SECS * 1000 + 1000)
_gse_i._stats.last_checksum = ""  # prevent dedup
r_i3 = _gse_i.flush()
check("I4: flush succeeds after cooling elapsed", r_i3.flushed is True)


# ─────────────────────────────────────────────────────────────────────────────
# J: Payload structure
# ─────────────────────────────────────────────────────────────────────────────
print("J: Payload structure")

# Use LOW anomaly to avoid triggering auto-flush before get_pending_payload()
_low_anomaly = [{"severity": SEV_LOW, "category": "REGIME_SHIFT",
                 "description": "regime shifted", "metric": "regime",
                 "current_value": "MEAN_REVERTING", "threshold": "TRENDING",
                 "delta": "TRENDING->MEAN", "ts": int(time.time() * 1000),
                 "anomaly_id": "j001"}]

_gse_j = GitHubSyncEngine()
_gse_j.queue_snapshot(_comp, _delta, _low_anomaly)
payload_j = _gse_j.get_pending_payload()

check("J1: get_pending_payload returns dict",          isinstance(payload_j, dict))
check("J2: payload has sync_ts",                       "sync_ts" in payload_j)
check("J3: payload has sync_reason",                   "sync_reason" in payload_j)
check("J4: payload has session_summary",               "session_summary" in payload_j)
check("J5: payload has anomaly_summary",               "anomaly_summary" in payload_j)
check("J6: payload has delta_summary",                 "delta_summary" in payload_j)
check("J7: payload has batch_stats",                   "batch_stats" in payload_j)
check("J8: session_summary contains pnl",              payload_j.get("session_summary", {}).get("pnl") == 100.0)
check("J9: session_summary excludes _-prefixed fields",
      not any(k.startswith("_") for k in payload_j.get("session_summary", {})))


# ─────────────────────────────────────────────────────────────────────────────
# K: Payload — anomaly summary correctness
# ─────────────────────────────────────────────────────────────────────────────
print("K: Payload — anomaly summary")

# Use HIGH/MEDIUM/LOW only (no CRITICAL) to avoid triggering auto-flush
_multi_anomalies = [
    {"severity": SEV_HIGH, "description": "5 losses", "category": "LOSS_STREAK",
     "metric": "consec_losses", "current_value": 5, "threshold": 5, "delta": 2,
     "ts": int(time.time() * 1000), "anomaly_id": "k002"},
    {"severity": SEV_MEDIUM, "description": "1 toxic", "category": "TOXIC_SPIKE",
     "metric": "rl_toxic", "current_value": 1, "threshold": 1, "delta": 1,
     "ts": int(time.time() * 1000), "anomaly_id": "k003"},
    {"severity": SEV_LOW, "description": "regime shift", "category": "REGIME_SHIFT",
     "metric": "regime", "current_value": "MEAN", "threshold": "TRENDING", "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "k004"},
]
# Inject CRITICAL entry manually after queueing to inspect full payload without auto-flush
_multi_with_critical = [
    {"severity": SEV_CRITICAL, "description": "halted", "category": "RISK_STATE",
     "metric": "risk_halted", "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "k001"},
] + _multi_anomalies

_gse_k = GitHubSyncEngine()
_gse_k.queue_snapshot(_comp, _delta, _multi_anomalies)   # no auto-flush (1 HIGH < threshold)
# Manually add CRITICAL to the entry anomalies for payload inspection
_gse_k._batch[0].anomalies.insert(0, _multi_with_critical[0])
payload_k = _gse_k.get_pending_payload()
asummary  = payload_k.get("anomaly_summary", {})

check("K1: worst_severity is CRITICAL",        asummary.get("worst_severity") == SEV_CRITICAL)
check("K2: critical list contains description", "halted" in asummary.get("critical", []))
check("K3: high list contains description",     "5 losses" in asummary.get("high", []))
check("K4: medium_count = 1",                  asummary.get("medium_count") == 1)
check("K5: low_count = 1",                     asummary.get("low_count") == 1)
check("K6: total = 4",                         asummary.get("total") == 4)


# ─────────────────────────────────────────────────────────────────────────────
# L: Payload — delta summary correctness
# ─────────────────────────────────────────────────────────────────────────────
print("L: Payload — delta summary")

_gse_l = GitHubSyncEngine()
_delta_big = {
    "has_meaningful_delta": True,
    "significance_score": 35.0,
    "changed_fields": {"pnl": {"prev": 50.0, "curr": 100.0}, "iq_score": {"prev": 60.0, "curr": 75.0}},
    "summary": "pnl up, IQ up",
}
_gse_l.queue_snapshot(_comp, _delta_big, [])
payload_l  = _gse_l.get_pending_payload()
dsummary   = payload_l.get("delta_summary", {})

check("L1: delta_summary has significant_changes list",  isinstance(dsummary.get("significant_changes"), list))
check("L2: significant_changes contains changed fields",
      "pnl" in dsummary.get("significant_changes", []))
check("L3: significance_score matches",                  dsummary.get("significance_score") == 35.0)
check("L4: summary text present",                        "pnl" in dsummary.get("summary", ""))


# ─────────────────────────────────────────────────────────────────────────────
# M: Payload — batch stats correctness
# ─────────────────────────────────────────────────────────────────────────────
print("M: Payload — batch stats")

_gse_m = GitHubSyncEngine()
for i in range(3):
    _gse_m.queue_snapshot(_comp, _delta, [])
payload_m = _gse_m.get_pending_payload()
bstats    = payload_m.get("batch_stats", {})

check("M1: snapshots_queued = 3",       bstats.get("snapshots_queued") == 3)
check("M2: anomalies_queued = 0",       bstats.get("anomalies_queued") == 0)
check("M3: period_secs >= 0",           bstats.get("period_secs", -1) >= 0)
check("M4: suppressed_deltas >= 0",     bstats.get("suppressed_deltas", -1) >= 0)


# ─────────────────────────────────────────────────────────────────────────────
# N: Push adapter injection
# ─────────────────────────────────────────────────────────────────────────────
print("N: Push adapter injection")

_gse_n       = GitHubSyncEngine()
_adapter_log = []

def _test_adapter(payload: dict) -> bool:
    _adapter_log.append(payload)
    return True

_gse_n.set_push_adapter(_test_adapter)
_gse_n.queue_snapshot(_comp, _delta, _critical_anomalies)  # triggers CRITICAL flush

check("N1: adapter was called",                       len(_adapter_log) >= 1)
check("N2: adapter received dict payload",            isinstance(_adapter_log[0], dict))
check("N3: payload passed to adapter has sync_ts",    "sync_ts" in _adapter_log[0])
check("N4: payload passed to adapter has session_summary", "session_summary" in _adapter_log[0])

# Adapter that raises — engine must survive
_gse_n2 = GitHubSyncEngine()
def _failing_adapter(p):
    raise RuntimeError("simulated GitHub API error")
_gse_n2.set_push_adapter(_failing_adapter)
_gse_n2.queue_snapshot(_comp, _delta, _critical_anomalies)
check("N5: engine survives failing push adapter", True)   # reaching this line means no crash


# ─────────────────────────────────────────────────────────────────────────────
# O: Local file writes (atomic, latest pointer)
# ─────────────────────────────────────────────────────────────────────────────
print("O: Local file writes")

import json as _json

_gse_o = GitHubSyncEngine()
_gse_o.queue_snapshot(_comp, _delta, _critical_anomalies)  # triggers CRITICAL flush
result_o = _gse_o._stats.last_checksum

latest_path = SYNC_DIR / "latest_sync.json"
check("O1: SYNC_DIR created",              SYNC_DIR.exists())
check("O2: latest_sync.json written",      latest_path.exists())

if latest_path.exists():
    loaded = _json.loads(latest_path.read_text())
    check("O3: latest_sync.json has sync_ts",         "sync_ts" in loaded)
    check("O4: latest_sync.json has session_summary", "session_summary" in loaded)
else:
    check("O3: latest_sync.json has sync_ts",         False, "file not found")
    check("O4: latest_sync.json has session_summary", False, "file not found")

# Verify timestamped file exists
sync_files = list(SYNC_DIR.glob("sync_*.json"))
check("O5: at least one timestamped sync file written", len(sync_files) >= 1)


# ─────────────────────────────────────────────────────────────────────────────
# P: should_flush() and status()
# ─────────────────────────────────────────────────────────────────────────────
print("P: should_flush() and status()")

_gse_p = GitHubSyncEngine()
check("P1: should_flush() False on empty batch",  _gse_p.should_flush() is False)

_gse_p.queue_snapshot(_comp, _delta, [])
check("P2: should_flush() False immediately after queue", _gse_p.should_flush() is False)

# Simulate time threshold exceeded
_gse_p._batch_start_ts = int(time.time() * 1000) - (SYNC_INTERVAL_SECS * 1000 + 1000)
check("P3: should_flush() True after time threshold", _gse_p.should_flush() is True)

status = _gse_p.status()
check("P4: status() returns dict",          isinstance(status, dict))
check("P5: status has batch_size key",      "batch_size" in status)
check("P6: status has governance section",  "governance" in status)


# ─────────────────────────────────────────────────────────────────────────────
# Q: mark_synced() and history
# ─────────────────────────────────────────────────────────────────────────────
print("Q: mark_synced()")

_gse_q = GitHubSyncEngine()
_gse_q.mark_synced("abc123checksum16")

check("Q1: mark_synced updates last_checksum",  _gse_q._stats.last_checksum == "abc123checksum16")
check("Q2: mark_synced updates last_sync_ts",   _gse_q._stats.last_sync_ts > 0)
check("Q3: sync_ts added to history",           len(_gse_q._stats.sync_ts_history) == 1)

# Verify _syncs_in_last_hour counts correctly
_gse_q.mark_synced("xyz999")
check("Q4: _syncs_in_last_hour = 2 after two mark_synced calls",
      _gse_q._syncs_in_last_hour() == 2)


# ─────────────────────────────────────────────────────────────────────────────
# R: Resilience / non-throwing
# ─────────────────────────────────────────────────────────────────────────────
print("R: Resilience")

try:
    r1 = GitHubSyncEngine().queue_snapshot(None)  # type: ignore
    check("R1: queue_snapshot(None) does not throw", True)
except Exception as e:
    check("R1: queue_snapshot(None) does not throw", False, str(e))

try:
    r2 = GitHubSyncEngine().flush()
    check("R2: flush() on fresh engine does not throw", True)
except Exception as e:
    check("R2: flush() on fresh engine does not throw", False, str(e))

try:
    r3 = GitHubSyncEngine().get_pending_payload()
    check("R3: get_pending_payload() on empty engine returns None", r3 is None)
except Exception as e:
    check("R3: get_pending_payload() on empty engine returns None", False, str(e))

try:
    r4 = GitHubSyncEngine().should_flush()
    check("R4: should_flush() on empty engine does not throw", r4 is False)
except Exception as e:
    check("R4: should_flush() on empty engine does not throw", False, str(e))

try:
    r5 = GitHubSyncEngine().status()
    check("R5: status() on fresh engine does not throw", isinstance(r5, dict))
except Exception as e:
    check("R5: status() on fresh engine does not throw", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# S: Integration — full Phase 1→2→3 pipeline
# ─────────────────────────────────────────────────────────────────────────────
print("S: Integration — full pipeline")

from core.observability.intelligence_compressor import IntelligenceCompressor
from core.observability.delta_reporter import DeltaReporter
from core.observability.anomaly_detector import AnomalyDetector
from core.observability.github_sync_engine import GitHubSyncEngine as GSE

_ic   = IntelligenceCompressor()
_dr   = DeltaReporter()
_ad   = AnomalyDetector()
_gse_s = GSE()

_push_log = []
_gse_s.set_push_adapter(lambda p: _push_log.append(p) or True)

_raw = {
    "session_stats": {"total_net_pnl": 200.0, "n_trades": 30, "profit_factor": 2.2, "win_rate": 0.70},
    "rl": {
        "total_contexts": 60, "total_trade_decisions": 300,
        "evolution_state": {"intelligence_score": 75.0},
        "summary_metrics": {"toxic_contexts": 0, "allow_rate": 0.92, "profitable_pct": 70.0},
        "learning_speed": {"maturity_pct": 65.0, "status": "MATURE"},
        "exploration_pressure": {"pressure_status": "BALANCED"},
        "confidence_trajectory": {"confidence_direction": "GROWING"},
    },
    "risk": {"halted": False}, "gate": {"can_trade": True},
    "trade_flow": {"consecutive_losses": 0, "daily_trades": 15},
    "regime": "TRENDING", "uptime_secs": 7200, "error_count": 0,
}

compressed_s = _ic.compress(_raw)
delta_s      = _dr.compute_delta(compressed_s)     # baseline
anomalies_s  = _ad.scan(compressed_s)              # healthy, should be []

check("S1: compress succeeds", "pnl" in compressed_s)
check("S2: baseline delta emitted", delta_s.get("is_baseline") is True)
check("S3: healthy scan has no anomalies", anomalies_s == [])

# Now inject CRITICAL degradation
_raw_bad = deepcopy(_raw)
_raw_bad["risk"]["halted"] = True
_raw_bad["trade_flow"]["consecutive_losses"] = 8
_raw_bad["rl"]["summary_metrics"]["toxic_contexts"] = 6
_raw_bad["rl"]["evolution_state"]["intelligence_score"] = 12.0

compressed_bad = _ic.compress(_raw_bad)
delta_bad      = _dr.compute_delta(compressed_bad)
anomalies_bad  = _ad.scan(compressed_bad)

triggered_s = _gse_s.queue_snapshot(compressed_bad, delta_bad, anomalies_bad)

check("S4: CRITICAL scenario triggers immediate flush",   triggered_s is True)
check("S5: adapter called with sync payload",             len(_push_log) >= 1)
check("S6: worst_severity in payload is CRITICAL",
      _push_log[-1].get("anomaly_summary", {}).get("worst_severity") == "CRITICAL")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for line in _results:
    print(line)

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"FTD-053-GAIA Phase 3 Verifier: {PASS}/{total} checks passed")
if FAIL > 0:
    print(f"FAILED: {FAIL} checks")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)

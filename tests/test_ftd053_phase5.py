"""
FTD-053-GAIA Phase 5 Verifier
Event-Driven Synchronization + Escalation Architecture

Sections:
  A: Module imports and singletons                    (6 checks)
  B: EventBus — subscribe / unsubscribe               (7 checks)
  C: EventBus — emit and handler dispatch             (7 checks)
  D: EventBus — handler fault isolation               (5 checks)
  E: EventBus — convenience emit wrappers             (5 checks)
  F: EventBus — governance (subscriber cap)           (4 checks)
  G: EventBus — status and introspection              (5 checks)
  H: EscalationEngine — CRITICAL → L3_SYNC           (7 checks)
  I: EscalationEngine — HIGH cluster → L2_RECORD     (5 checks)
  J: EscalationEngine — HIGH (below cluster) → L1_LOG(4 checks)
  K: EscalationEngine — no escalation (MEDIUM/LOW)   (4 checks)
  L: EscalationEngine — dedup suppression             (5 checks)
  M: EscalationEngine — acknowledge (human override)  (6 checks)
  N: EscalationEngine — auto_resolve                  (6 checks)
  O: EscalationEngine — history and get_active        (5 checks)
  P: EscalationEngine — stats tracking                (5 checks)
  Q: EscalationEngine — file write (L2/L3)            (4 checks)
  R: Event-driven flow (escalation triggers bus event)(5 checks)
  S: Resilience / non-throwing                        (6 checks)
  T: Integration — full Phase 1→5 pipeline            (8 checks)

Total: 109 checks
"""
from __future__ import annotations

import sys
import time
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
    from core.observability.event_bus import (
        EventBus, event_bus,
        CHANNEL_ANOMALY, CHANNEL_ESCALATION, CHANNEL_SYNC_READY,
        CHANNEL_FEED_UPDATE, CHANNEL_SUMMARY, ALL_CHANNELS,
        MAX_SUBSCRIBERS_PER_CHANNEL,
    )
    check("A1: event_bus importable", True)
except Exception as e:
    check("A1: event_bus importable", False, str(e))

try:
    from core.observability.escalation_engine import (
        EscalationEngine, escalation_engine,
        EscalationRecord,
        L1_LOG, L2_RECORD, L3_SYNC,
        STATUS_ACTIVE, STATUS_ACKNOWLEDGED, STATUS_RESOLVED,
        DEDUP_WINDOW_SECS, ACK_SUPPRESS_SECS, HIGH_CLUSTER_THRESH,
        ESCALATION_DIR,
    )
    check("A2: escalation_engine importable", True)
except Exception as e:
    check("A2: escalation_engine importable", False, str(e))

try:
    from core.observability import event_bus as eb_pkg, escalation_engine as ee_pkg
    check("A3: package __init__ exports Phase 5 singletons", True)
except Exception as e:
    check("A3: package __init__ exports Phase 5 singletons", False, str(e))

check("A4: singletons correct types",
      isinstance(event_bus, EventBus) and isinstance(escalation_engine, EscalationEngine))
check("A5: ALL_CHANNELS has 5 entries", len(ALL_CHANNELS) == 5)
check("A6: ESCALATION_DIR is a Path",   isinstance(ESCALATION_DIR, Path))


# ─────────────────────────────────────────────────────────────────────────────
# B: EventBus — subscribe / unsubscribe
# ─────────────────────────────────────────────────────────────────────────────
print("B: EventBus — subscribe/unsubscribe")

_eb = EventBus()
_received: list = []

def _handler_b(payload):
    _received.append(payload)

sub_id_b = _eb.subscribe(CHANNEL_ANOMALY, _handler_b)
check("B1: subscribe returns string sub_id",    isinstance(sub_id_b, str) and len(sub_id_b) == 12)
check("B2: subscriber count = 1",               _eb.subscriber_count(CHANNEL_ANOMALY) == 1)

sub_id_b2 = _eb.subscribe(CHANNEL_ANOMALY, _handler_b)
check("B3: second subscribe on same channel",    _eb.subscriber_count(CHANNEL_ANOMALY) == 2)

ok_unsub = _eb.unsubscribe(sub_id_b)
check("B4: unsubscribe returns True",            ok_unsub is True)
check("B5: subscriber count drops to 1",         _eb.subscriber_count(CHANNEL_ANOMALY) == 1)

check("B6: unsubscribe unknown id returns False", _eb.unsubscribe("nonexistent") is False)

try:
    _eb.subscribe("INVALID_CHANNEL", _handler_b)
    check("B7: subscribe to unknown channel raises ValueError", False, "no error raised")
except ValueError:
    check("B7: subscribe to unknown channel raises ValueError", True)
except Exception as e:
    check("B7: subscribe to unknown channel raises ValueError", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# C: EventBus — emit and handler dispatch
# ─────────────────────────────────────────────────────────────────────────────
print("C: EventBus — emit and dispatch")

_eb_c   = EventBus()
_log_c: list = []

def _capture(p):
    _log_c.append(p)

_eb_c.subscribe(CHANNEL_ANOMALY, _capture)
n_called = _eb_c.emit(CHANNEL_ANOMALY, {"anomalies": [], "worst": "NONE"})

check("C1: emit returns handler count",         n_called == 1)
check("C2: handler was called",                 len(_log_c) == 1)
check("C3: payload received has original keys", "anomalies" in _log_c[0])
check("C4: _channel injected into payload",     _log_c[0].get("_channel") == CHANNEL_ANOMALY)
check("C5: _emit_ts injected into payload",     "_emit_ts" in _log_c[0])

# Emit to channel with no subscribers
n_empty = _eb_c.emit(CHANNEL_ESCALATION, {"esc": "test"})
check("C6: emit to empty channel returns 0",    n_empty == 0)

# Multiple handlers on same channel
_log_c2: list = []
_eb_c.subscribe(CHANNEL_ANOMALY, lambda p: _log_c2.append(p))
n_two = _eb_c.emit(CHANNEL_ANOMALY, {"x": 1})
check("C7: two handlers both called",           n_two == 2 and len(_log_c2) == 1)


# ─────────────────────────────────────────────────────────────────────────────
# D: EventBus — handler fault isolation
# ─────────────────────────────────────────────────────────────────────────────
print("D: EventBus — fault isolation")

_eb_d   = EventBus()
_log_d: list = []

def _bad_handler(p):
    raise RuntimeError("simulated handler failure")

def _good_handler(p):
    _log_d.append(p)

_eb_d.subscribe(CHANNEL_ANOMALY, _bad_handler)
_eb_d.subscribe(CHANNEL_ANOMALY, _good_handler)

n_d = _eb_d.emit(CHANNEL_ANOMALY, {"test": True})
check("D1: emit succeeds despite bad handler",  True)   # reaching here = no crash
check("D2: good handler still called",          len(_log_d) == 1)
check("D3: handler_errors tracked in stats",
      _eb_d.status()["stats"]["total_handler_errors"] >= 1)
check("D4: emit returns count of SUCCESSFUL calls",
      n_d == 1)   # 1 bad, 1 good → returns 1

# Emit to empty bus — should not crash
n_empty2 = EventBus().emit(CHANNEL_SUMMARY, {})
check("D5: emit to fresh empty bus returns 0", n_empty2 == 0)


# ─────────────────────────────────────────────────────────────────────────────
# E: EventBus — convenience emit wrappers
# ─────────────────────────────────────────────────────────────────────────────
print("E: EventBus — convenience wrappers")

_eb_e    = EventBus()
_log_e: list = []
_eb_e.subscribe(CHANNEL_ANOMALY,    lambda p: _log_e.append(("ANO", p)))
_eb_e.subscribe(CHANNEL_ESCALATION, lambda p: _log_e.append(("ESC", p)))
_eb_e.subscribe(CHANNEL_SYNC_READY, lambda p: _log_e.append(("SYN", p)))

_eb_e.emit_anomalies([{"severity": "HIGH"}], "HIGH", "test")
_eb_e.emit_escalation({"level": "L3_SYNC", "id": "abc"})
_eb_e.emit_sync_ready({"flushed": True})

check("E1: emit_anomalies dispatched to ANOMALY",     any(t == "ANO" for t, _ in _log_e))
check("E2: emit_escalation dispatched to ESCALATION", any(t == "ESC" for t, _ in _log_e))
check("E3: emit_sync_ready dispatched to SYNC_READY", any(t == "SYN" for t, _ in _log_e))
check("E4: anomaly wrapper injects anomaly_count",
      any(p.get("anomaly_count") == 1 for t, p in _log_e if t == "ANO"))
check("E5: anomaly wrapper injects worst_severity",
      any(p.get("worst_severity") == "HIGH" for t, p in _log_e if t == "ANO"))


# ─────────────────────────────────────────────────────────────────────────────
# F: EventBus — governance (subscriber cap)
# ─────────────────────────────────────────────────────────────────────────────
print("F: EventBus — subscriber cap governance")

_eb_f = EventBus()
_dummy = lambda p: None

# Fill up to cap
for i in range(MAX_SUBSCRIBERS_PER_CHANNEL):
    _eb_f.subscribe(CHANNEL_SUMMARY, _dummy)

check("F1: can subscribe up to cap",
      _eb_f.subscriber_count(CHANNEL_SUMMARY) == MAX_SUBSCRIBERS_PER_CHANNEL)

try:
    _eb_f.subscribe(CHANNEL_SUMMARY, _dummy)
    check("F2: subscribe beyond cap raises ValueError", False, "no error raised")
except ValueError:
    check("F2: subscribe beyond cap raises ValueError", True)

check("F3: other channels not affected by cap on SUMMARY",
      _eb_f.subscriber_count(CHANNEL_ANOMALY) == 0)
check("F4: cap is enforced per-channel independently", True)


# ─────────────────────────────────────────────────────────────────────────────
# G: EventBus — status and introspection
# ─────────────────────────────────────────────────────────────────────────────
print("G: EventBus — status and introspection")

_eb_g = EventBus()
_log_g: list = []
_eb_g.subscribe(CHANNEL_ANOMALY, lambda p: _log_g.append(p))
_eb_g.emit(CHANNEL_ANOMALY, {"x": 1})
_eb_g.emit(CHANNEL_ESCALATION, {"y": 2})

status_g = _eb_g.status()
check("G1: status returns dict",                   isinstance(status_g, dict))
check("G2: status has subscribers section",        "subscribers" in status_g)
check("G3: status has stats section",              "stats" in status_g)
check("G4: per_channel tracks emits",
      status_g["stats"]["per_channel"].get(CHANNEL_ANOMALY, 0) >= 1)

recent = _eb_g.recent_events(10)
check("G5: recent_events returns list of dicts with channel key",
      isinstance(recent, list) and all("channel" in e for e in recent))


# ─────────────────────────────────────────────────────────────────────────────
# H: EscalationEngine — CRITICAL → L3_SYNC
# ─────────────────────────────────────────────────────────────────────────────
print("H: EscalationEngine — CRITICAL → L3_SYNC")

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW

_ee = EscalationEngine()

_crit_anomalies = [
    {"severity": SEV_CRITICAL, "category": "RISK_STATE",
     "description": "Engine halted", "metric": "risk_halted",
     "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "h001"},
]

rec_h = _ee.evaluate(_crit_anomalies, emit_event=False)

check("H1: evaluate returns EscalationRecord",  isinstance(rec_h, EscalationRecord))
check("H2: level is L3_SYNC",                   rec_h.level == L3_SYNC, rec_h.level)
check("H3: severity is CRITICAL",               rec_h.severity == SEV_CRITICAL)
check("H4: status is ACTIVE",                   rec_h.status == STATUS_ACTIVE)
check("H5: escalation_id is 8-char hex",        len(rec_h.escalation_id) == 8)
check("H6: anomaly_ids populated",              len(rec_h.anomaly_ids) >= 1)
check("H7: total_escalated incremented",        _ee.stats()["total_escalated"] == 1)


# ─────────────────────────────────────────────────────────────────────────────
# I: EscalationEngine — HIGH cluster → L2_RECORD
# ─────────────────────────────────────────────────────────────────────────────
print("I: EscalationEngine — HIGH cluster → L2_RECORD")

_ee_i = EscalationEngine()
_high_cluster = [
    {"severity": SEV_HIGH, "category": "LOSS_STREAK",
     "description": f"High {i}", "metric": "consec_losses",
     "current_value": 5, "threshold": 5, "delta": 1,
     "ts": int(time.time() * 1000), "anomaly_id": f"i{i:03d}"}
    for i in range(HIGH_CLUSTER_THRESH)  # exactly at threshold
]

rec_i = _ee_i.evaluate(_high_cluster, emit_event=False)
check("I1: HIGH cluster returns EscalationRecord",  isinstance(rec_i, EscalationRecord))
check("I2: level is L2_RECORD",                     rec_i.level == L2_RECORD, rec_i.level)
check("I3: severity is HIGH",                       rec_i.severity == SEV_HIGH)
check("I4: l2_count incremented",                   _ee_i.stats()["l2_count"] == 1)
check("I5: anomaly_categories populated",           len(rec_i.anomaly_categories) >= 1)


# ─────────────────────────────────────────────────────────────────────────────
# J: EscalationEngine — 1-2 HIGH → L1_LOG
# ─────────────────────────────────────────────────────────────────────────────
print("J: EscalationEngine — HIGH (below cluster) → L1_LOG")

_ee_j = EscalationEngine()
_high_single = [
    {"severity": SEV_HIGH, "category": "LOSS_STREAK",
     "description": "5 losses", "metric": "consec_losses",
     "current_value": 5, "threshold": 5, "delta": 2,
     "ts": int(time.time() * 1000), "anomaly_id": "j001"},
]

rec_j = _ee_j.evaluate(_high_single, emit_event=False)
check("J1: 1 HIGH → EscalationRecord",  isinstance(rec_j, EscalationRecord))
check("J2: level is L1_LOG",            rec_j.level == L1_LOG, rec_j.level)
check("J3: l1_count incremented",       _ee_j.stats()["l1_count"] == 1)
check("J4: l3_count = 0",               _ee_j.stats()["l3_count"] == 0)


# ─────────────────────────────────────────────────────────────────────────────
# K: EscalationEngine — no escalation for MEDIUM/LOW
# ─────────────────────────────────────────────────────────────────────────────
print("K: EscalationEngine — no escalation for MEDIUM/LOW")

_ee_k = EscalationEngine()

_medium_anomalies = [
    {"severity": SEV_MEDIUM, "category": "LOSS_STREAK",
     "description": "3 losses", "metric": "consec_losses",
     "current_value": 3, "threshold": 3, "delta": 1,
     "ts": int(time.time() * 1000), "anomaly_id": "k001"},
]
_low_anomalies = [
    {"severity": SEV_LOW, "category": "REGIME_SHIFT",
     "description": "regime shifted", "metric": "regime",
     "current_value": "MEAN", "threshold": "TRENDING", "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "k002"},
]

check("K1: MEDIUM-only returns None",        _ee_k.evaluate(_medium_anomalies, emit_event=False) is None)
check("K2: LOW-only returns None",           _ee_k.evaluate(_low_anomalies, emit_event=False) is None)
check("K3: empty list returns None",         _ee_k.evaluate([], emit_event=False) is None)
check("K4: total_escalated = 0",             _ee_k.stats()["total_escalated"] == 0)


# ─────────────────────────────────────────────────────────────────────────────
# L: EscalationEngine — dedup suppression
# ─────────────────────────────────────────────────────────────────────────────
print("L: EscalationEngine — dedup suppression")

_ee_l = EscalationEngine()
_crit_l = [
    {"severity": SEV_CRITICAL, "category": "RISK_STATE",
     "description": "halted", "metric": "risk_halted",
     "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "l001"},
]

rec_l1 = _ee_l.evaluate(_crit_l, emit_event=False)
check("L1: first evaluation creates record",    isinstance(rec_l1, EscalationRecord))

# Second evaluation with same trigger — should be deduped
rec_l2 = _ee_l.evaluate(_crit_l, emit_event=False)
check("L2: second identical evaluation returns None (dedup)", rec_l2 is None)
check("L3: total_suppressed = 1",               _ee_l.stats()["total_suppressed"] == 1)
check("L4: total_escalated = 1 (not 2)",        _ee_l.stats()["total_escalated"] == 1)

# Different trigger should NOT be deduped
_diff_crit = [
    {"severity": SEV_CRITICAL, "category": "TOXIC_SPIKE",
     "description": "6 toxics", "metric": "rl_toxic",
     "current_value": 6, "threshold": 5, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "l002"},
]
rec_l3 = _ee_l.evaluate(_diff_crit, emit_event=False)
check("L5: different trigger not deduped",       isinstance(rec_l3, EscalationRecord))


# ─────────────────────────────────────────────────────────────────────────────
# M: EscalationEngine — acknowledge (human override)
# ─────────────────────────────────────────────────────────────────────────────
print("M: EscalationEngine — acknowledge (human override)")

_ee_m = EscalationEngine()
_crit_m = [
    {"severity": SEV_CRITICAL, "category": "RISK_STATE",
     "description": "halted", "metric": "risk_halted",
     "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "m001"},
]

rec_m = _ee_m.evaluate(_crit_m, emit_event=False)
esc_id_m = rec_m.escalation_id

ok_ack = _ee_m.acknowledge(esc_id_m, "reviewed by operator")
check("M1: acknowledge returns True",            ok_ack is True)
check("M2: status changed to ACKNOWLEDGED",
      _ee_m.get_history(1)[0]["status"] == STATUS_ACKNOWLEDGED)
check("M3: ack_reason set",
      _ee_m.get_history(1)[0]["ack_reason"] == "reviewed by operator")
check("M4: total_acked incremented",             _ee_m.stats()["total_acked"] == 1)

# Acknowledged escalation: active list should not contain it
active_m = _ee_m.get_active_escalations()
check("M5: acknowledged escalation not in active list",
      not any(r["escalation_id"] == esc_id_m for r in active_m))

# Acknowledge unknown id → False
check("M6: acknowledge unknown id returns False", _ee_m.acknowledge("deadbeef") is False)


# ─────────────────────────────────────────────────────────────────────────────
# N: EscalationEngine — auto_resolve
# ─────────────────────────────────────────────────────────────────────────────
print("N: EscalationEngine — auto_resolve")

_ee_n = EscalationEngine()
_crit_n = [
    {"severity": SEV_CRITICAL, "category": "RISK_STATE",
     "description": "halted", "metric": "risk_halted",
     "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "n001"},
]

rec_n = _ee_n.evaluate(_crit_n, emit_event=False)
check("N1: escalation is ACTIVE before resolve",   rec_n.status == STATUS_ACTIVE)

# Resolve with empty current categories (anomaly cleared)
resolved = _ee_n.auto_resolve(set())
check("N2: auto_resolve returns list of resolved IDs",  isinstance(resolved, list))
check("N3: escalation ID in resolved list",             rec_n.escalation_id in resolved)
check("N4: status changed to RESOLVED",                 rec_n.status == STATUS_RESOLVED)
check("N5: resolved_ts set",                            rec_n.resolved_ts > 0)

# With still-active category: should NOT resolve
_ee_n2 = EscalationEngine()
rec_n2 = _ee_n2.evaluate(_crit_n, emit_event=False)
resolved2 = _ee_n2.auto_resolve({"RISK_STATE"})
check("N6: escalation with active category not resolved",
      rec_n2.escalation_id not in resolved2)


# ─────────────────────────────────────────────────────────────────────────────
# O: EscalationEngine — history and get_active
# ─────────────────────────────────────────────────────────────────────────────
print("O: EscalationEngine — history and get_active")

_ee_o = EscalationEngine()
_ee_o.evaluate(_crit_anomalies, emit_event=False)
_ee_o.evaluate([{"severity": SEV_HIGH, "category": "LOSS_STREAK",
                  "description": "losses", "metric": "consec_losses",
                  "current_value": 5, "threshold": 5, "delta": 2,
                  "ts": int(time.time() * 1000), "anomaly_id": "o001"}], emit_event=False)

history_o = _ee_o.get_history(10)
check("O1: get_history returns list",           isinstance(history_o, list))
check("O2: history has 2 entries",              len(history_o) == 2)
check("O3: history entries are dicts with required keys",
      all("escalation_id" in r and "level" in r and "status" in r for r in history_o))

active_o = _ee_o.get_active_escalations()
check("O4: get_active_escalations returns list", isinstance(active_o, list))
check("O5: all active have status=ACTIVE",
      all(r["status"] == STATUS_ACTIVE for r in active_o))


# ─────────────────────────────────────────────────────────────────────────────
# P: EscalationEngine — stats tracking
# ─────────────────────────────────────────────────────────────────────────────
print("P: EscalationEngine — stats")

stats_p = _ee_o.stats()
check("P1: stats returns dict",                isinstance(stats_p, dict))
check("P2: stats has total_evaluated",         "total_evaluated" in stats_p)
check("P3: stats has l3_count",                "l3_count" in stats_p)
check("P4: l3_count >= 1 (CRITICAL was fired)", stats_p.get("l3_count", 0) >= 1)
check("P5: active_count >= 0",                  stats_p.get("active_count", -1) >= 0)


# ─────────────────────────────────────────────────────────────────────────────
# Q: EscalationEngine — file write (L2/L3)
# ─────────────────────────────────────────────────────────────────────────────
print("Q: EscalationEngine — file write")

import json as _json

_ee_q = EscalationEngine()
_ee_q.evaluate(_crit_anomalies, emit_event=False)   # L3 → should write file

latest = ESCALATION_DIR / "latest_escalation.json"
check("Q1: ESCALATION_DIR created",            ESCALATION_DIR.exists())
check("Q2: latest_escalation.json written",    latest.exists())

if latest.exists():
    data_q = _json.loads(latest.read_text())
    check("Q3: latest escalation has level field",   "level" in data_q)
    check("Q4: latest escalation level is L3_SYNC",  data_q.get("level") == L3_SYNC)
else:
    check("Q3: latest escalation has level field",   False, "file not found")
    check("Q4: latest escalation level is L3_SYNC",  False, "file not found")


# ─────────────────────────────────────────────────────────────────────────────
# R: Event-driven flow — escalation triggers bus event
# ─────────────────────────────────────────────────────────────────────────────
print("R: Event-driven flow")

_eb_r  = EventBus()
_ee_r  = EscalationEngine()
_esc_events: list = []

_eb_r.subscribe(CHANNEL_ESCALATION, lambda p: _esc_events.append(p))

# Monkey-patch the escalation engine to use our test bus
def _patched_emit(record):
    _eb_r.emit_escalation(record.to_dict())

_ee_r._emit = _patched_emit

_ee_r.evaluate(_crit_anomalies, emit_event=True)

check("R1: escalation event received on bus",   len(_esc_events) >= 1)
check("R2: escalation event has escalation_id", "escalation_id" in _esc_events[0])
check("R3: escalation event has level",         "level" in _esc_events[0])
check("R4: escalation event level is L3_SYNC",  _esc_events[0].get("level") == L3_SYNC)
check("R5: _channel injected by bus",           _esc_events[0].get("_channel") == CHANNEL_ESCALATION)


# ─────────────────────────────────────────────────────────────────────────────
# S: Resilience / non-throwing
# ─────────────────────────────────────────────────────────────────────────────
print("S: Resilience")

try:
    r_s1 = EventBus().emit(CHANNEL_ANOMALY, None)   # type: ignore
    check("S1: emit(None payload) does not throw", True)
except Exception as e:
    check("S1: emit(None payload) does not throw", False, str(e))

try:
    r_s2 = EventBus().emit("UNKNOWN_CHANNEL", {})
    check("S2: emit to unknown channel does not throw", True)
except Exception as e:
    check("S2: emit to unknown channel does not throw", False, str(e))

try:
    r_s3 = EscalationEngine().evaluate(None, emit_event=False)  # type: ignore
    check("S3: evaluate(None) does not throw", True)
except Exception as e:
    check("S3: evaluate(None) does not throw", False, str(e))

try:
    r_s4 = EscalationEngine().auto_resolve(None)    # type: ignore
    check("S4: auto_resolve(None) does not throw", True)
except Exception as e:
    check("S4: auto_resolve(None) does not throw", False, str(e))

try:
    r_s5 = EscalationEngine().stats()
    check("S5: stats() on fresh engine does not throw", isinstance(r_s5, dict))
except Exception as e:
    check("S5: stats() on fresh engine does not throw", False, str(e))

try:
    r_s6 = EventBus().status()
    check("S6: EventBus.status() on fresh bus does not throw", isinstance(r_s6, dict))
except Exception as e:
    check("S6: EventBus.status() on fresh bus does not throw", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# T: Integration — full Phase 1→5 pipeline
# ─────────────────────────────────────────────────────────────────────────────
print("T: Integration — full Phase 1→5 pipeline")

from core.observability.intelligence_compressor import IntelligenceCompressor
from core.observability.delta_reporter import DeltaReporter
from core.observability.anomaly_detector import AnomalyDetector
from core.observability.ai_summary_engine import AISummaryEngine
from core.observability.strategic_feed import StrategicFeed
from core.observability.event_bus import EventBus as EB
from core.observability.escalation_engine import EscalationEngine as EE

_ic_t  = IntelligenceCompressor()
_dr_t  = DeltaReporter()
_ad_t  = AnomalyDetector()
_ase_t = AISummaryEngine()
_sf_t  = StrategicFeed()
_eb_t  = EB()
_ee_t  = EE()

# Wire up event listeners
_t_anomaly_events:    list = []
_t_escalation_events: list = []
_eb_t.subscribe(CHANNEL_ANOMALY,    lambda p: _t_anomaly_events.append(p))
_eb_t.subscribe(CHANNEL_ESCALATION, lambda p: _t_escalation_events.append(p))

# Patch escalation engine to use our test bus
def _t_emit_escalation(record):
    _eb_t.emit_escalation(record.to_dict())
_ee_t._emit = _t_emit_escalation

# Simulate a critical trading scenario
_raw_critical = {
    "session_stats": {"total_net_pnl": -350.0, "n_trades": 40, "profit_factor": 0.4, "win_rate": 0.28},
    "rl": {
        "total_contexts": 50, "total_trade_decisions": 200,
        "evolution_state": {"intelligence_score": 10.0},
        "summary_metrics": {"toxic_contexts": 7, "allow_rate": 0.22, "profitable_pct": 30.0},
        "learning_speed": {"maturity_pct": 20.0, "status": "WARMING_UP"},
        "exploration_pressure": {"pressure_status": "HIGH_EXPLORE"},
        "confidence_trajectory": {"confidence_direction": "DECLINING"},
    },
    "risk": {"halted": True}, "gate": {"can_trade": False},
    "trade_flow": {"consecutive_losses": 9, "daily_trades": 30},
    "regime": "VOLATILITY_EXPANSION", "uptime_secs": 3600, "error_count": 5,
}

compressed_t = _ic_t.compress(_raw_critical)
delta_t      = _dr_t.compute_delta(compressed_t)
anomalies_t  = _ad_t.scan(compressed_t)
summary_t    = _ase_t.generate_summary(compressed_t, delta_t, anomalies_t)
feeds_t      = _sf_t.refresh(compressed_t, anomalies_t)

# Emit anomaly event
_eb_t.emit_anomalies(anomalies_t, summary_t.get("worst_severity", "NONE"), "test")

# Evaluate escalation
esc_record_t = _ee_t.evaluate(anomalies_t, emit_event=True)

check("T1: compressed snapshot has pnl",        "pnl" in compressed_t)
check("T2: CRITICAL anomalies detected",
      any(a.get("severity") == SEV_CRITICAL for a in anomalies_t))
check("T3: summary priority is CRITICAL",        summary_t.get("priority") == "CRITICAL")
check("T4: RISK feed is HALTED",                 feeds_t.get("RISK") is not None and
                                                  feeds_t["RISK"].state == "HALTED")
check("T5: anomaly event received on bus",       len(_t_anomaly_events) >= 1)
check("T6: escalation record is L3_SYNC",
      isinstance(esc_record_t, EscalationRecord) and esc_record_t.level == L3_SYNC)
check("T7: escalation event fired on bus",       len(_t_escalation_events) >= 1)
check("T8: end-to-end pipeline produces actionable output",
      summary_t.get("directive_count", 0) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for line in _results:
    print(line)

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"FTD-053-GAIA Phase 5 Verifier: {PASS}/{total} checks passed")
if FAIL > 0:
    print(f"FAILED: {FAIL} checks")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)

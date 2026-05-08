"""
FTD-053-GAIA Phase 2 Verifier
Delta Reporting + Anomaly Detection + Severity Classification + Intelligence Prioritization

Sections:
  A: Module imports and singleton availability          (5 checks)
  B: DeltaReporter — baseline (first snapshot)         (5 checks)
  C: DeltaReporter — meaningful delta detection        (8 checks)
  D: DeltaReporter — suppression (trivial changes)     (5 checks)
  E: DeltaReporter — always-significant fields         (4 checks)
  F: DeltaReporter — stats tracking                    (4 checks)
  G: DeltaReporter — reset()                           (3 checks)
  H: AnomalyDetector — CRITICAL severity triggers      (6 checks)
  I: AnomalyDetector — HIGH severity triggers          (8 checks)
  J: AnomalyDetector — MEDIUM severity triggers        (6 checks)
  K: AnomalyDetector — LOW severity triggers           (3 checks)
  L: AnomalyDetector — severity ordering               (4 checks)
  M: AnomalyDetector — IQ regression (absolute+peak)  (6 checks)
  N: AnomalyDetector — active summary                  (5 checks)
  O: AnomalyDetector — history management              (4 checks)
  P: AnomalyDetector — stats tracking                  (5 checks)
  Q: Resilience / non-throwing guarantees              (5 checks)
  R: Integration — compress → delta → anomaly pipeline (6 checks)

Total: 92 checks
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


def _find_first_sev(events: list, sev: str) -> int:
    for i, e in enumerate(events):
        if e["severity"] == sev:
            return i
    return 9999


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
    from core.observability.delta_reporter import (
        DeltaReporter, delta_reporter,
        MEANINGFUL_DELTA_THRESHOLD,
        _ALWAYS_SIGNIFICANT,
    )
    check("A1: delta_reporter importable", True)
except Exception as e:
    check("A1: delta_reporter importable", False, str(e))

try:
    from core.observability.anomaly_detector import (
        AnomalyDetector, anomaly_detector,
        SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW,
        CONSEC_LOSS_CRITICAL, CONSEC_LOSS_HIGH, CONSEC_LOSS_MEDIUM,
        TOXIC_CRITICAL, TOXIC_HIGH, TOXIC_MEDIUM,
        IQ_CRITICAL_FLOOR, IQ_HIGH_FLOOR, IQ_MEDIUM_FLOOR,
    )
    check("A2: anomaly_detector importable", True)
except Exception as e:
    check("A2: anomaly_detector importable", False, str(e))

try:
    from core.observability import delta_reporter as dr_pkg, anomaly_detector as ad_pkg
    check("A3: package __init__ exports Phase 2 singletons", True)
except Exception as e:
    check("A3: package __init__ exports Phase 2 singletons", False, str(e))

check("A4: delta_reporter is DeltaReporter instance",    isinstance(delta_reporter, DeltaReporter))
check("A5: anomaly_detector is AnomalyDetector instance", isinstance(anomaly_detector, AnomalyDetector))


# ─────────────────────────────────────────────────────────────────────────────
# B: DeltaReporter — baseline (first snapshot)
# ─────────────────────────────────────────────────────────────────────────────
print("B: DeltaReporter — baseline")

_dr = DeltaReporter()   # fresh instance

_snap1 = {
    "pnl": 50.0, "n_trades": 10, "iq_score": 65.0,
    "rl_toxic": 0, "consec_losses": 1, "regime": "TRENDING",
    "risk_halted": False, "gate_open": True, "rl_allow_rate": 0.88,
    "rl_confidence_dir": "GROWING",
    "_checksum": "abc001", "_compressed_ts": int(time.time() * 1000),
    "_schema_version": "1.0",
}

baseline = _dr.compute_delta(_snap1)
check("B1: baseline returns dict",                    isinstance(baseline, dict))
check("B2: baseline has_meaningful_delta=True",       baseline.get("has_meaningful_delta") is True)
check("B3: baseline is_baseline=True",                baseline.get("is_baseline") is True)
check("B4: baseline new_fields contains pnl",         "pnl" in baseline.get("new_fields", {}))
check("B5: baseline changed_fields is empty",         baseline.get("changed_fields") == {})


# ─────────────────────────────────────────────────────────────────────────────
# C: DeltaReporter — meaningful delta detection
# ─────────────────────────────────────────────────────────────────────────────
print("C: DeltaReporter — meaningful delta")

_snap2 = deepcopy(_snap1)
_snap2["pnl"]            = 80.0      # +$30 — well above $0.50 threshold
_snap2["iq_score"]       = 72.0      # +7 IQ — above 2pt threshold
_snap2["rl_toxic"]       = 2         # +2 toxics — above 1 threshold
_snap2["consec_losses"]  = 3         # +2 — above 1 threshold
_snap2["_checksum"]      = "abc002"
_snap2["_compressed_ts"] = int(time.time() * 1000)

delta_c = _dr.compute_delta(_snap2)
changed  = delta_c.get("changed_fields", {})

check("C1: has_meaningful_delta=True for big changes",   delta_c.get("has_meaningful_delta") is True)
check("C2: pnl in changed_fields",                       "pnl" in changed)
check("C3: iq_score in changed_fields",                  "iq_score" in changed)
check("C4: rl_toxic in changed_fields",                  "rl_toxic" in changed)
check("C5: pnl prev=50.0 in delta",                      changed.get("pnl", {}).get("prev") == 50.0)
check("C6: pnl curr=80.0 in delta",                      changed.get("pnl", {}).get("curr") == 80.0)
check("C7: pnl abs_delta=30.0",                          changed.get("pnl", {}).get("abs_delta") == 30.0)
check("C8: significance_score > MEANINGFUL_DELTA_THRESHOLD",
      delta_c.get("significance_score", 0) >= MEANINGFUL_DELTA_THRESHOLD)


# ─────────────────────────────────────────────────────────────────────────────
# D: DeltaReporter — suppression (trivial changes)
# ─────────────────────────────────────────────────────────────────────────────
print("D: DeltaReporter — suppression")

_snap3 = deepcopy(_snap2)
_snap3["pnl"]            = 80.20     # +$0.20 — below $0.50 threshold
_snap3["iq_score"]       = 72.5      # +0.5 IQ — below 2pt threshold
_snap3["uptime_secs"]    = 3900      # +300 secs — exactly at threshold (not above)
_snap3["_checksum"]      = "abc003"
_snap3["_compressed_ts"] = int(time.time() * 1000)

delta_d = _dr.compute_delta(_snap3)
changed_d = delta_d.get("changed_fields", {})

check("D1: trivial pnl change not in changed_fields",    "pnl" not in changed_d)
check("D2: trivial iq_score change not in changed_fields", "iq_score" not in changed_d)
check("D3: has_meaningful_delta=False for trivial changes",
      delta_d.get("has_meaningful_delta") is False,
      f"score={delta_d.get('significance_score')}")
check("D4: suppressed_count increments",                 delta_d.get("suppressed_count", 0) >= 1)
check("D5: force=True overrides suppression",
      _dr.compute_delta(_snap3, force=True).get("has_meaningful_delta") is True)


# ─────────────────────────────────────────────────────────────────────────────
# E: DeltaReporter — always-significant fields
# ─────────────────────────────────────────────────────────────────────────────
print("E: DeltaReporter — always-significant fields")

_snap4 = deepcopy(_snap3)
_snap4["risk_halted"]    = True      # changed from False — ALWAYS significant
_snap4["_checksum"]      = "abc004"
_snap4["_compressed_ts"] = int(time.time() * 1000)

delta_e = _dr.compute_delta(_snap4)
changed_e = delta_e.get("changed_fields", {})

check("E1: risk_halted change always detected",    "risk_halted" in changed_e)
check("E2: has_meaningful_delta=True for halted",  delta_e.get("has_meaningful_delta") is True)

_snap5 = deepcopy(_snap4)
_snap5["regime"]      = "MEAN_REVERTING"
_snap5["_checksum"]   = "abc005"
_snap5["_compressed_ts"] = int(time.time() * 1000)

delta_e2 = _dr.compute_delta(_snap5)
check("E3: regime change always detected",         "regime" in delta_e2.get("changed_fields", {}))
check("E4: _ALWAYS_SIGNIFICANT contains expected fields",
      "risk_halted" in _ALWAYS_SIGNIFICANT and "gate_open" in _ALWAYS_SIGNIFICANT)


# ─────────────────────────────────────────────────────────────────────────────
# F: DeltaReporter — stats
# ─────────────────────────────────────────────────────────────────────────────
print("F: DeltaReporter — stats")

stats_f = _dr.stats()
check("F1: stats has total_reports",    "total_reports" in stats_f)
check("F2: stats has total_suppressed", "total_suppressed" in stats_f)
check("F3: stats has total_meaningful", "total_meaningful" in stats_f)
check("F4: total_reports > 0",          stats_f.get("total_reports", 0) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# G: DeltaReporter — reset
# ─────────────────────────────────────────────────────────────────────────────
print("G: DeltaReporter — reset")

_dr.reset()
check("G1: after reset has_baseline=False", _dr.stats().get("has_baseline") is False)

fresh_after_reset = _dr.compute_delta(_snap1)
check("G2: first call after reset is baseline", fresh_after_reset.get("is_baseline") is True)
check("G3: has_baseline=True after first call",  _dr.stats().get("has_baseline") is True)


# ─────────────────────────────────────────────────────────────────────────────
# H: AnomalyDetector — CRITICAL severity triggers
# ─────────────────────────────────────────────────────────────────────────────
print("H: AnomalyDetector — CRITICAL severity")

_ad = AnomalyDetector()

# risk_halted = True → CRITICAL
_h1 = {"risk_halted": True, "gate_open": True, "rl_toxic": 0, "consec_losses": 0, "iq_score": 70.0}
evts_h1 = _ad.scan(_h1)
sev_h1  = [e["severity"] for e in evts_h1]
check("H1: risk_halted=True triggers CRITICAL", SEV_CRITICAL in sev_h1)

# consec_losses >= 7 → CRITICAL
_h2 = {"risk_halted": False, "gate_open": True, "consec_losses": CONSEC_LOSS_CRITICAL, "rl_toxic": 0, "iq_score": 70.0}
evts_h2 = _ad.scan(_h2)
sev_h2  = [e["severity"] for e in evts_h2]
check("H2: consec_losses>=7 triggers CRITICAL", SEV_CRITICAL in sev_h2)

# rl_toxic >= 5 → CRITICAL
_h3 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": TOXIC_CRITICAL, "iq_score": 70.0}
evts_h3 = _ad.scan(_h3)
sev_h3  = [e["severity"] for e in evts_h3]
check("H3: rl_toxic>=5 triggers CRITICAL", SEV_CRITICAL in sev_h3)

# iq_score < IQ_CRITICAL_FLOOR → CRITICAL
_h4 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 15.0}
evts_h4 = _ad.scan(_h4)
sev_h4  = [e["severity"] for e in evts_h4]
check("H4: iq_score<20 triggers CRITICAL", SEV_CRITICAL in sev_h4)

# allow_rate < 0.30 → CRITICAL
_h5 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0,
       "rl_allow_rate": 0.20}
evts_h5 = _ad.scan(_h5)
sev_h5  = [e["severity"] for e in evts_h5]
check("H5: allow_rate<0.30 triggers CRITICAL", SEV_CRITICAL in sev_h5)

check("H6: CRITICAL events have category field",
      all("category" in e for e in evts_h1 if e["severity"] == SEV_CRITICAL))


# ─────────────────────────────────────────────────────────────────────────────
# I: AnomalyDetector — HIGH severity triggers
# ─────────────────────────────────────────────────────────────────────────────
print("I: AnomalyDetector — HIGH severity")

_ad2 = AnomalyDetector()

# gate_open = False → HIGH
_i1 = {"risk_halted": False, "gate_open": False, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0}
evts_i1 = _ad2.scan(_i1)
check("I1: gate_open=False triggers HIGH",
      any(e["severity"] == SEV_HIGH and e["metric"] == "gate_open" for e in evts_i1))

# consec_losses = 5 → HIGH
_i2 = {"risk_halted": False, "gate_open": True, "consec_losses": CONSEC_LOSS_HIGH, "rl_toxic": 0, "iq_score": 70.0}
evts_i2 = _ad2.scan(_i2)
check("I2: consec_losses=5 triggers HIGH",
      any(e["severity"] == SEV_HIGH and e["category"] == "LOSS_STREAK" for e in evts_i2))

# rl_toxic = 3 → HIGH
_i3 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": TOXIC_HIGH, "iq_score": 70.0}
evts_i3 = _ad2.scan(_i3)
check("I3: rl_toxic=3 triggers HIGH",
      any(e["severity"] == SEV_HIGH and e["category"] == "TOXIC_SPIKE" for e in evts_i3))

# iq_score in [20, 35) → HIGH  (IQ_HIGH_FLOOR=35, so iq<35 triggers HIGH)
_i4 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 30.0}
evts_i4 = _ad2.scan(_i4)
check("I4: iq_score=30 triggers HIGH",
      any(e["severity"] == SEV_HIGH and e["category"] == "IQ_REGRESSION" for e in evts_i4))

# allow_rate in [0.50, 0.65) → HIGH
_i5 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0,
       "rl_allow_rate": 0.45}
evts_i5 = _ad2.scan(_i5)
check("I5: allow_rate=0.45 triggers HIGH",
      any(e["severity"] == SEV_HIGH and e["category"] == "ALLOW_COLLAPSE" for e in evts_i5))

# win_rate < WR_HIGH_FLOOR → HIGH
_i6 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0,
       "le_trending_wr": 0.30}
evts_i6 = _ad2.scan(_i6)
check("I6: le_trending_wr=0.30 triggers HIGH WIN_RATE_EROSION",
      any(e["severity"] == SEV_HIGH and e["category"] == "WIN_RATE_EROSION" for e in evts_i6))

# confidence flip GROWING → DECLINING after state update
_ad3 = AnomalyDetector()
_i7a = {"risk_halted": False, "gate_open": True, "rl_confidence_dir": "GROWING",
        "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0}
_ad3.scan(_i7a)  # establish prev
_i7b = deepcopy(_i7a)
_i7b["rl_confidence_dir"] = "DECLINING"
evts_i7 = _ad3.scan(_i7b)
check("I7: GROWING→DECLINING confidence flip triggers HIGH",
      any(e["severity"] == SEV_HIGH and e["category"] == "CONFIDENCE_FLIP" for e in evts_i7))

check("I8: HIGH events have anomaly_id field",
      all("anomaly_id" in e for e in evts_i1))


# ─────────────────────────────────────────────────────────────────────────────
# J: AnomalyDetector — MEDIUM severity triggers
# ─────────────────────────────────────────────────────────────────────────────
print("J: AnomalyDetector — MEDIUM severity")

_ad4 = AnomalyDetector()

# consec_losses = 3 → MEDIUM
_j1 = {"risk_halted": False, "gate_open": True, "consec_losses": CONSEC_LOSS_MEDIUM, "rl_toxic": 0, "iq_score": 70.0}
evts_j1 = _ad4.scan(_j1)
check("J1: consec_losses=3 triggers MEDIUM",
      any(e["severity"] == SEV_MEDIUM and e["category"] == "LOSS_STREAK" for e in evts_j1))

# rl_toxic = 1 → MEDIUM
_j2 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": TOXIC_MEDIUM, "iq_score": 70.0}
evts_j2 = _ad4.scan(_j2)
check("J2: rl_toxic=1 triggers MEDIUM",
      any(e["severity"] == SEV_MEDIUM and e["category"] == "TOXIC_SPIKE" for e in evts_j2))

# iq_score in [50, 65) → MEDIUM
_j3 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 55.0}
evts_j3 = _ad4.scan(_j3)
check("J3: iq_score=55 triggers MEDIUM IQ_REGRESSION",
      any(e["severity"] == SEV_MEDIUM and e["category"] == "IQ_REGRESSION" for e in evts_j3))

# allow_rate in [0.65, 0.75) → MEDIUM  (threshold at 0.65)
_j4 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0,
       "rl_allow_rate": 0.60}
evts_j4 = _ad4.scan(_j4)
check("J4: allow_rate=0.60 triggers MEDIUM ALLOW_COLLAPSE",
      any(e["severity"] == SEV_MEDIUM and e["category"] == "ALLOW_COLLAPSE" for e in evts_j4))

# win_rate in [WR_MEDIUM_FLOOR, WR_HIGH_FLOOR) → MEDIUM
_j5 = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0,
       "le_mean_rev_wr": 0.40}
evts_j5 = _ad4.scan(_j5)
check("J5: le_mean_rev_wr=0.40 triggers MEDIUM WIN_RATE_EROSION",
      any(e["severity"] == SEV_MEDIUM and e["category"] == "WIN_RATE_EROSION" for e in evts_j5))

check("J6: MEDIUM events have description field",
      all("description" in e for e in evts_j1))


# ─────────────────────────────────────────────────────────────────────────────
# K: AnomalyDetector — LOW severity
# ─────────────────────────────────────────────────────────────────────────────
print("K: AnomalyDetector — LOW severity")

_ad5 = AnomalyDetector()
_k1a = {"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 70.0,
        "regime": "TRENDING"}
_ad5.scan(_k1a)

_k1b = deepcopy(_k1a)
_k1b["regime"] = "MEAN_REVERTING"
evts_k = _ad5.scan(_k1b)
check("K1: regime shift triggers LOW anomaly",
      any(e["severity"] == SEV_LOW and e["category"] == "REGIME_SHIFT" for e in evts_k))
check("K2: LOW events have current_value field",
      all("current_value" in e for e in evts_k if e["severity"] == SEV_LOW))
check("K3: healthy snapshot produces no anomalies",
      _ad5.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0,
                 "rl_toxic": 0, "iq_score": 80.0, "rl_allow_rate": 0.90,
                 "le_trending_wr": 0.65, "rl_confidence_dir": "GROWING"}) == [])


# ─────────────────────────────────────────────────────────────────────────────
# L: AnomalyDetector — severity ordering
# ─────────────────────────────────────────────────────────────────────────────
print("L: AnomalyDetector — severity ordering")

_ad6 = AnomalyDetector()
# Trigger multiple severities simultaneously
_l1 = {
    "risk_halted": True,      # CRITICAL
    "consec_losses": 5,       # HIGH
    "rl_toxic": 1,            # MEDIUM
    "iq_score": 70.0,
    "gate_open": True,
}
evts_l1 = _ad6.scan(_l1)

check("L1: multiple anomalies detected",          len(evts_l1) >= 2)
check("L2: CRITICAL appears before HIGH in list",
      _find_first_sev(evts_l1, SEV_CRITICAL) < _find_first_sev(evts_l1, SEV_HIGH)
      if SEV_CRITICAL in [e["severity"] for e in evts_l1] and
         SEV_HIGH in [e["severity"] for e in evts_l1] else True)
check("L3: anomaly_ids are 8-char hex strings",
      all(len(e["anomaly_id"]) == 8 for e in evts_l1))
check("L4: no duplicate anomaly_ids in single scan",
      len({e["anomaly_id"] for e in evts_l1}) == len(evts_l1))


# ─────────────────────────────────────────────────────────────────────────────
# M: AnomalyDetector — IQ regression (absolute + peak-based)
# ─────────────────────────────────────────────────────────────────────────────
print("M: AnomalyDetector — IQ regression")

_ad7 = AnomalyDetector()

# Establish peak at 80.0
_ad7.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 80.0})
check("M1: peak_iq updated to 80.0", _ad7._peak_iq == 80.0)

# IQ drop of 22 from peak → HIGH (IQ_DROP_HIGH = 20)
evts_m2 = _ad7.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 58.0})
check("M2: 22pt drop from peak=80 triggers HIGH IQ_REGRESSION",
      any(e["severity"] == SEV_HIGH and e["category"] == "IQ_REGRESSION" for e in evts_m2))

# IQ drop of 12 from new peek at 80 (current is 68) → MEDIUM (IQ_DROP_MEDIUM = 10)
_ad7._peak_iq = 80.0   # reset peak for isolated test
evts_m3 = _ad7.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 68.0})
# 68 >= IQ_MEDIUM_FLOOR (50) so no absolute trigger. drop = 80 - 68 = 12 → MEDIUM
check("M3: 12pt drop from peak=80 triggers MEDIUM IQ_REGRESSION",
      any(e["severity"] == SEV_MEDIUM and e["category"] == "IQ_REGRESSION" for e in evts_m3))

# Absolute CRITICAL floor
_ad8 = AnomalyDetector()
evts_m4 = _ad8.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 10.0})
check("M4: iq=10 triggers CRITICAL IQ_REGRESSION",
      any(e["severity"] == SEV_CRITICAL and e["category"] == "IQ_REGRESSION" for e in evts_m4))

# IQ rising — no regression
_ad9 = AnomalyDetector()
_ad9.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 60.0})
evts_m5 = _ad9.scan({"risk_halted": False, "gate_open": True, "consec_losses": 0, "rl_toxic": 0, "iq_score": 75.0})
check("M5: rising IQ triggers no IQ anomaly",
      not any(e["category"] == "IQ_REGRESSION" for e in evts_m5))

check("M6: IQ event includes current_value",
      all("current_value" in e for e in evts_m4 if e["category"] == "IQ_REGRESSION"))


# ─────────────────────────────────────────────────────────────────────────────
# N: AnomalyDetector — active summary
# ─────────────────────────────────────────────────────────────────────────────
print("N: AnomalyDetector — active summary")

_ad_sum = AnomalyDetector()
_ad_sum.scan({"risk_halted": True, "gate_open": False, "consec_losses": 5, "rl_toxic": 3, "iq_score": 15.0})
summary = _ad_sum.get_active_summary()

check("N1: summary returns dict",                       isinstance(summary, dict))
check("N2: summary has worst_severity",                 "worst_severity" in summary)
check("N3: worst_severity is CRITICAL for this scan",   summary.get("worst_severity") == SEV_CRITICAL)
check("N4: summary has anomaly_counts",                 "anomaly_counts" in summary)
check("N5: summary has total_scans",                    "total_scans" in summary)


# ─────────────────────────────────────────────────────────────────────────────
# O: AnomalyDetector — history management
# ─────────────────────────────────────────────────────────────────────────────
print("O: AnomalyDetector — history")

_ad_hist = AnomalyDetector()
for i in range(5):
    _ad_hist.scan({"risk_halted": False, "gate_open": True,
                   "consec_losses": 3, "rl_toxic": 1, "iq_score": 55.0})

history = _ad_hist.get_history(limit=50)
check("O1: get_history returns list",         isinstance(history, list))
check("O2: get_history has entries",          len(history) > 0)
check("O3: get_history respects min_severity filter",
      all(e["severity"] in (SEV_HIGH, SEV_CRITICAL)
          for e in _ad_hist.get_history(min_severity=SEV_HIGH)))
check("O4: history entries are dicts with required keys",
      all("anomaly_id" in e and "severity" in e and "ts" in e for e in history[:3]))


# ─────────────────────────────────────────────────────────────────────────────
# P: AnomalyDetector — stats
# ─────────────────────────────────────────────────────────────────────────────
print("P: AnomalyDetector — stats")

stats_p = _ad_hist.stats()
check("P1: stats returns dict",                    isinstance(stats_p, dict))
check("P2: stats has total_scans",                 "total_scans" in stats_p)
check("P3: stats has total_anomalies",             "total_anomalies" in stats_p)
check("P4: stats total_anomalies matches history", stats_p.get("total_anomalies", 0) == len(_ad_hist._history))
check("P5: stats has medium_count",                "medium_count" in stats_p)


# ─────────────────────────────────────────────────────────────────────────────
# Q: Resilience — non-throwing
# ─────────────────────────────────────────────────────────────────────────────
print("Q: Resilience")

try:
    result_q1 = DeltaReporter().compute_delta(None)  # type: ignore
    check("Q1: DeltaReporter.compute_delta(None) does not throw", True)
except Exception as e:
    check("Q1: DeltaReporter.compute_delta(None) does not throw", False, str(e))

try:
    result_q2 = DeltaReporter().compute_delta({})
    check("Q2: DeltaReporter.compute_delta({}) does not throw", isinstance(result_q2, dict))
except Exception as e:
    check("Q2: DeltaReporter.compute_delta({}) does not throw", False, str(e))

try:
    result_q3 = AnomalyDetector().scan(None)  # type: ignore
    check("Q3: AnomalyDetector.scan(None) does not throw", isinstance(result_q3, list))
except Exception as e:
    check("Q3: AnomalyDetector.scan(None) does not throw", False, str(e))

try:
    result_q4 = AnomalyDetector().scan({})
    check("Q4: AnomalyDetector.scan({}) does not throw", isinstance(result_q4, list))
except Exception as e:
    check("Q4: AnomalyDetector.scan({}) does not throw", False, str(e))

try:
    result_q5 = AnomalyDetector().get_active_summary()
    check("Q5: get_active_summary on empty detector does not throw", isinstance(result_q5, dict))
except Exception as e:
    check("Q5: get_active_summary on empty detector does not throw", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# R: Integration — compress → delta → anomaly pipeline
# ─────────────────────────────────────────────────────────────────────────────
print("R: Integration — full pipeline")

from core.observability.intelligence_compressor import IntelligenceCompressor
from core.observability.report_lifecycle_engine import ReportLifecycleEngine
from core.observability.delta_reporter import DeltaReporter
from core.observability.anomaly_detector import AnomalyDetector

_ic   = IntelligenceCompressor()
_rle  = ReportLifecycleEngine()
_dr_r = DeltaReporter()
_ad_r = AnomalyDetector()

_raw_healthy = {
    "session_stats": {"total_net_pnl": 100.0, "n_trades": 20, "profit_factor": 1.9, "win_rate": 0.65},
    "rl": {
        "total_contexts": 50, "total_trade_decisions": 250,
        "evolution_state": {"intelligence_score": 72.0},
        "summary_metrics": {"toxic_contexts": 0, "allow_rate": 0.90, "profitable_pct": 70.0},
        "learning_speed": {"maturity_pct": 60.0, "status": "MATURE"},
        "exploration_pressure": {"pressure_status": "BALANCED"},
        "confidence_trajectory": {"confidence_direction": "GROWING"},
    },
    "risk": {"halted": False}, "gate": {"can_trade": True},
    "trade_flow": {"consecutive_losses": 0, "daily_trades": 10},
    "regime": "TRENDING", "uptime_secs": 3600, "error_count": 0,
}

compressed_r1 = _ic.compress(_raw_healthy)
check("R1: compressed healthy snapshot", isinstance(compressed_r1, dict) and "pnl" in compressed_r1)

delta_r1 = _dr_r.compute_delta(compressed_r1)
check("R2: baseline delta emitted", delta_r1.get("is_baseline") is True)

anomalies_r1 = _ad_r.scan(compressed_r1)
check("R3: healthy snapshot yields no anomalies", anomalies_r1 == [])

# Now inject a degraded snapshot
_raw_degraded = deepcopy(_raw_healthy)
_raw_degraded["session_stats"]["total_net_pnl"]  = 60.0
_raw_degraded["rl"]["evolution_state"]["intelligence_score"] = 15.0  # CRITICAL
_raw_degraded["rl"]["summary_metrics"]["toxic_contexts"]     = 6     # CRITICAL
_raw_degraded["trade_flow"]["consecutive_losses"]            = 7     # CRITICAL
_raw_degraded["risk"]["halted"]                              = True  # CRITICAL

compressed_r2 = _ic.compress(_raw_degraded)
delta_r2      = _dr_r.compute_delta(compressed_r2)
anomalies_r2  = _ad_r.scan(compressed_r2)

check("R4: degraded delta has_meaningful_delta", delta_r2.get("has_meaningful_delta") is True)
check("R5: degraded snapshot triggers CRITICAL anomalies",
      any(e["severity"] == SEV_CRITICAL for e in anomalies_r2))
check("R6: write_compressed succeeds for delta",
      _rle.write_compressed("integration_r", compressed_r2, skip_dedup_check=True).success)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for line in _results:
    print(line)

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"FTD-053-GAIA Phase 2 Verifier: {PASS}/{total} checks passed")
if FAIL > 0:
    print(f"FAILED: {FAIL} checks")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
